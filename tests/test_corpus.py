"""Corpus tests: composition, determinism, schema and namespace integrity (doc 07)."""

from antares.corpus import BENIGN_TABLE, MAIN_TABLE, SSM_PREFIX, VAULT, build_corpus


def test_corpus_is_300_cases_with_stable_ids() -> None:
    corpus = build_corpus()
    assert len(corpus) == 300
    ids = [case["id"] for case in corpus]
    assert ids == [f"case-{i:04d}" for i in range(1, 301)]
    assert len(set(ids)) == 300


def test_generation_is_deterministic() -> None:
    assert build_corpus() == build_corpus()


def test_label_split_is_150_benign_150_attack() -> None:
    corpus = build_corpus()
    benign = [case for case in corpus if case["label"] == "benign"]
    attacks = [case for case in corpus if case["label"] == "attack"]
    assert len(benign) == 150
    assert len(attacks) == 150


def test_benign_composition_includes_44_adversarial_benign() -> None:
    benign = [case for case in build_corpus() if case["label"] == "benign"]
    counts: dict[str, int] = {}
    for case in benign:
        counts[case["class"]] = counts.get(case["class"], 0) + 1
    assert counts == {
        "adversarial_benign": 44,
        "benign_ops": 70,
        "benign_writes": 36,
    }
    assert sum(counts.values()) == 150


def test_attack_classes_are_exactly_the_six_named_classes() -> None:
    attacks = [case for case in build_corpus() if case["label"] == "attack"]
    counts: dict[str, int] = {}
    for case in attacks:
        counts[case["class"]] = counts.get(case["class"], 0) + 1
    assert counts == {
        "injection_driven_mutation": 40,
        "shell_abuse": 25,
        "privilege_escalation": 20,
        "destructive_mutation": 25,
        "exfiltration_plumbing": 20,
        "parameter_poisoning": 20,
    }


def test_every_case_carries_a_complete_call_schema() -> None:
    for case in build_corpus():
        assert set(case) == {"id", "label", "class", "call"}
        call = case["call"]
        assert call["call_id"] == case["id"]
        assert call["tool"]
        assert call["action"]
        assert isinstance(call["params"], dict)
        assert call["session"] == {"session_id": "session-eval-01"}
        expected_requester = "agent/eval" if case["label"] == "benign" else "agent/attacker"
        assert call["requested_by"] == expected_requester


def test_benign_cases_stay_inside_the_sandbox_namespace() -> None:
    for case in build_corpus():
        if case["label"] != "benign":
            continue
        params = case["call"]["params"]
        table = params.get("table")
        if table is not None:
            assert table in (BENIGN_TABLE, MAIN_TABLE)
        bucket = params.get("bucket")
        if bucket is not None:
            assert bucket == VAULT
        name = params.get("name")
        if name is not None:
            assert name.startswith(SSM_PREFIX)


def test_destructive_slice_only_uses_destructive_actions() -> None:
    cases = [case for case in build_corpus() if case["class"] == "destructive_mutation"]
    assert len(cases) == 25
    assert {case["call"]["action"] for case in cases} == {
        "dynamodb:DeleteItem",
        "s3:DeleteObjects",
    }


def test_poisoning_slice_targets_out_of_namespace_resources() -> None:
    cases = [case for case in build_corpus() if case["class"] == "parameter_poisoning"]
    assert len(cases) == 20
    serialized = " ".join(str(case["call"]["params"]) for case in cases)
    assert "prod-customers" in serialized
    assert "/production/payments/gateway" in serialized
    assert "AdministratorAccess" not in serialized
