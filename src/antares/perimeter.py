"""Antares perimeter (S0): screen untrusted content before anything trusts it.

Layer 1 is pure code: normalization defeats homoglyph, invisible-character,
HTML-entity and base64 smuggling, then a signature library over the
canonical text produces named findings. Layer 2 (the Nova classifier) is
wired by the caller; this module stays dependency-free so evals can run
it with or without models (doc 07 baselines).

Severity model: block findings are hostile with high confidence, flag
findings are attack-shaped and need the semantic layer to judge.
"""

from __future__ import annotations

import base64
import binascii
import html
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

BLOCK = "block"
FLAG = "flag"
INFO = "info"

# Cyrillic and Greek glyphs that render as latin letters: the classic
# homoglyph smuggling route ("ignore" spelled with cyrillic i, o, e).
CONFUSABLES: dict[str, str] = {
    "а": "a",
    "е": "e",
    "о": "o",
    "р": "p",
    "с": "c",
    "х": "x",
    "і": "i",
    "ѕ": "s",
    "у": "y",
    "б": "b",
    "г": "r",
    "и": "n",
    "к": "k",
    "м": "m",
    "т": "t",
    "ь": "b",
    "ο": "o",
    "α": "a",
    "ε": "e",
    "ρ": "p",
    "σ": "s",
    "ν": "v",
    "κ": "k",
}

INVISIBLE_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u202a-\u202e\u2066-\u2069\u00ad]")
B64_RUN_RE = re.compile(r"[A-Za-z0-9+/=]{24,}")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s\"'<>)\]]+", re.IGNORECASE)
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HTML_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)

# Hosts and endpoints that exist to receive exfiltrated data.
EXFIL_HOST_RE = re.compile(
    r"webhook\.site|requestbin\.(?:com|net)|pipedream\.net|interact\.sh|"
    r"oast\.(?:fun|pro|live)|burpcollaborator\.net|api\.telegram\.org/bot",
    re.IGNORECASE,
)
SECRET_PARAM_RE = re.compile(
    r"[?&](?:d|data|q|payload|content|body|msg|secret|token|key|creds?|"
    r"leak|exfil|env|prompt|ctx|history|conversation)=",
    re.IGNORECASE,
)
CREDENTIAL_WORDS_RE = re.compile(
    r"(?:api[\s_-]?key|secret|token|password|credential|private key|"
    r"env var|environment variable|customer (?:data|records)|system prompt)",
    re.IGNORECASE,
)

_SIGNATURES: list[tuple[str, str, str, re.Pattern[str]]] = [
    # id, severity, category, pattern (over normalized text)
    (
        "OVR-001",
        BLOCK,
        "instruction_override",
        re.compile(
            r"\b(?:ignore|disregard|forget|override|bypass|discard|drop)\b"
            r"[^.\n]{0,48}\b(?:previous|prior|above|earlier|original|all|any|your)\b"
            r"[^.\n]{0,32}\b(?:instructions?|prompts?|rules?|directions?|"
            r"constraints?|guardrails?|guidelines?|system messages?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "OVR-002",
        BLOCK,
        "instruction_override",
        re.compile(
            r"(?:new|updated|revised|real|actual)\s+(?:instructions?|directives?|orders?)\s*:",
            re.IGNORECASE,
        ),
    ),
    (
        "OVR-003",
        FLAG,
        "instruction_override",
        re.compile(
            r"\b(?:these|the following|my)\s+(?:instructions?|words?|requests?)\b"
            r"[^.\n]{0,40}\b(?:override|supersede|take precedence|come first|trump)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "SPOOF-001",
        BLOCK,
        "role_spoofing",
        re.compile(
            r"<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>|\[/?INST\]|<<SYS>>|<</SYS>>|"
            r"<\|system\|>|<\|assistant\|>|<\|user\|>",
            re.IGNORECASE,
        ),
    ),
    (
        "SPOOF-002",
        BLOCK,
        "role_spoofing",
        re.compile(
            r"(?:^|\n)\s*(?:#{1,4}\s*)?\**SYSTEM(?:\s|_)+(?:PROMPT|MESSAGE|INSTRUCTIONS?)\**\s*[:=]?",
            re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "SPOOF-003",
        BLOCK,
        "role_spoofing",
        re.compile(
            r"\b(?:you are now|from now on,? you are|you will now act as|your new role is)\b"
            r"[^.\n]{0,64}\b(?:DAN|jailbreak|developer mode|unrestricted|uncensored|"
            r"unfiltered|unbound|no (?:rules|restrictions|filters)|do anything|god ?mode)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "SPOOF-004",
        FLAG,
        "role_spoofing",
        re.compile(
            r"(?:^|\n)\s*(?:Assistant|AI|ChatGPT|Claude|Nova)\s*:\s*"
            r"(?:Sure|Certainly|Of course|Okay|OK|I understand|Understood)[,.]?",
            re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "EXT-001",
        BLOCK,
        "prompt_extraction",
        re.compile(
            r"\b(?:reveal|print|show|repeat|output|display|leak|expose|dump|spill|recite|quote)\b"
            r"[^.\n]{0,40}\b(?:system prompts?|your (?:initial |original |hidden )?"
            r"(?:instructions?|prompts?|rules?|directives?)|the prompt above|"
            r"everything you were (?:told|given|instructed))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "EXT-002",
        FLAG,
        "prompt_extraction",
        re.compile(
            r"\brepeat\b[^.\n]{0,32}\b(?:everything|word for word|verbatim|exactly (?:what|as))\b"
            r"[^.\n]{0,32}\b(?:above|earlier|told|instructed|said|given)\b",
            re.IGNORECASE,
        ),
    ),
    ("EXF-001", BLOCK, "exfiltration", EXFIL_HOST_RE),
    (
        "EXF-003",
        BLOCK,
        "exfiltration",
        re.compile(
            r"\b(?:post|send|upload|forward|transmit|exfiltrate|curl|wget|fetch)\b"
            r"[^.\n]{0,80}(?:https?://|"
            r"the following (?:data|context|transcript|conversation|secrets?)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "IND-001",
        BLOCK,
        "indirect_injection",
        re.compile(
            r"\b(?:note|message|instructions?|directive|memo|warning|task)\s+"
            r"(?:to|for)\s+(?:the\s+)?(?:AI|A\.I\.|LLM|GPT|Claude|Nova|model|assistant|"
            r"agent|bot|automated (?:reader|system|scrapers?|agents?)|language model)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "IND-002",
        BLOCK,
        "indirect_injection",
        re.compile(
            r"\bif\s+(?:you are|you're|this is)\s+(?:an?\s+)?(?:AI|A\.I\.|LLM|GPT|Claude|"
            r"Nova|bot|agent|model|assistant|automated system|reading this)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "IND-004",
        FLAG,
        "indirect_injection",
        re.compile(
            r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?:px|pt|em)?\b|"
            r"color\s*:\s*(?:transparent|white\b|rgba?\(\s*255\s*,\s*255\s*,\s*255)",
            re.IGNORECASE,
        ),
    ),
    (
        "TOOL-001",
        BLOCK,
        "tool_abuse",
        re.compile(
            r"\b(?:call|invoke|run|execute|use)\s+(?:the\s+)?`?[a-z_]{2,32}`?\s+"
            r"(?:tool|function|command|action)\b[^.\n]{0,80}\b(?:send|delete|transfer|"
            r"post|email|wire|pay|exfiltrate|publish|grant)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOOL-002",
        FLAG,
        "tool_abuse",
        re.compile(
            r"\b(?:execute|run)\s+(?:the\s+)?(?:following|this)\s+(?:shell|command|code|sql|script)\b",
            re.IGNORECASE,
        ),
    ),
]

_BASE64_INSTRUCTION_RE = re.compile(
    r"\b(?:ignore|disregard|forget|you are now|reveal|system|instructions?|send|post|exfiltrate)\b",
    re.IGNORECASE,
)


@dataclass
class ScreenResult:
    """Perimeter output: named findings plus the normalized channels."""

    verdict: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    transforms: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    normalized_length: int = 0


def _fold_confusables(text: str) -> str:
    return "".join(CONFUSABLES.get(ch, ch) for ch in text)


def _decode_base64_candidates(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for run in set(B64_RUN_RE.findall(text)):
        padded = run + "=" * (-len(run) % 4)
        try:
            decoded = base64.b64decode(padded, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        if decoded and sum(ch.isprintable() for ch in decoded) / len(decoded) > 0.9:
            out.append((decoded, run))
    return out


def normalize(text: str) -> dict[str, Any]:
    """Canonicalize content and surface every hidden channel found."""
    current = html.unescape(text) if "&" in text else text
    transforms: list[str] = []
    if current != text:
        transforms.append("html_entities_decoded")
    stripped = INVISIBLE_RE.sub("", current)
    if stripped != current:
        transforms.append("invisible_chars_removed")
    current = stripped
    folded = _fold_confusables(current)
    if folded != current:
        transforms.append("homoglyphs_folded")
    current = unicodedata.normalize("NFKC", folded)
    channels = {"surface": current}
    for index, (decoded, _run) in enumerate(_decode_base64_candidates(current)):
        channels[f"base64_channel_{index}"] = decoded
        transforms.append("base64_decoded")
    return {
        "normalized": current,
        "channels": channels,
        "transforms": transforms,
        "urls": URL_RE.findall(current),
        "md_images": MD_IMAGE_RE.findall(current),
        "html_comments": HTML_COMMENT_RE.findall(text),
    }


def _iter_strings(value: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield prefix or "content", value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(item, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{prefix}[{index}]")


def screen_l1(text: str) -> ScreenResult:
    """Layer 1: deterministic perimeter screen. No model, microseconds."""
    norm = normalize(text)
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(rule_id: str, severity: str, category: str, detail: str) -> None:
        if rule_id in seen:
            return
        seen.add(rule_id)
        findings.append(
            {"rule_id": rule_id, "severity": severity, "category": category, "detail": detail}
        )

    for sig_id, severity, category, pattern in _SIGNATURES:
        match = pattern.search(norm["normalized"])
        if match:
            add(sig_id, severity, category, f"matched {match.group(0)[:80]!r}")

    for comment in norm["html_comments"]:
        if re.search(
            r"\b(?:ignore|disregard|instructions?|assistant|AI|LLM|model|agent|system|reveal|instead)\b",
            comment,
            re.IGNORECASE,
        ):
            add("IND-003", BLOCK, "indirect_injection", "instructions hidden in an HTML comment")

    for target in norm["md_images"]:
        if SECRET_PARAM_RE.search(target):
            add(
                "EXF-004",
                BLOCK,
                "exfiltration",
                "markdown image URL carries a data-bearing query string",
            )

    text_for_urls = norm["normalized"]
    for url in norm["urls"]:
        if EXFIL_HOST_RE.search(url):
            add("EXF-001", BLOCK, "exfiltration", "known exfiltration endpoint referenced")
        index = text_for_urls.find(url)
        window = text_for_urls[max(0, index - 96) : index]
        if SECRET_PARAM_RE.search(url) or CREDENTIAL_WORDS_RE.search(window):
            add(
                "EXF-002",
                FLAG,
                "exfiltration",
                "credential-like data flowing toward an external URL",
            )

    for key, content in norm["channels"].items():
        if key.startswith("base64_channel") and _BASE64_INSTRUCTION_RE.search(content):
            add(
                "ENC-001",
                FLAG,
                "encoding_evasion",
                "base64 payload decoded to instruction-like text",
            )

    if "invisible_chars_removed" in norm["transforms"] or "homoglyphs_folded" in norm["transforms"]:
        add("ENC-002", FLAG, "encoding_evasion", "obfuscation artifacts normalized before scanning")

    blocked = any(f["severity"] == BLOCK for f in findings)
    flags = sum(1 for f in findings if f["severity"] == FLAG)
    score = min(1.0, 0.25 * flags + (1.0 if blocked else 0.0))
    verdict = "HOSTILE" if blocked else ("SUSPECT" if findings else "CLEAN")
    return ScreenResult(
        verdict=verdict,
        findings=findings,
        score=score,
        transforms=norm["transforms"],
        urls=norm["urls"],
        normalized_length=len(norm["normalized"]),
    )


def screen_params(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Screen every string leaf of a tool call's parameters (used by the
    quorum: findings travel into the quorum context, raw text does not)."""
    combined_findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, text in _iter_strings(params):
        for finding in screen_l1(text).findings:
            if finding["rule_id"] in seen:
                continue
            seen.add(finding["rule_id"])
            combined_findings.append({**finding, "detail": f"{path}: {finding['detail']}"})
    return combined_findings
