.PHONY: install lint type test gates build package deploy

ifeq ($(OS),Windows_NT)
PY := .venv/Scripts/python.exe
else
PY := .venv/bin/python
endif

BUCKET := antares-deploy-846719029074
STACK := antares-dev
REGION := us-east-1

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .

type:
	$(PY) -m mypy src

test:
	$(PY) -m pytest --cov=src/antares --cov-fail-under=90

gates: lint type test

# Lambda bundle: aarch64 wheels only (the function runs ARM64), built from
# the pinned runtime set. boto3 and botocore are dropped: the Lambda runtime
# ships them.
build:
	rm -rf .aws-build
	mkdir -p .aws-build
	$(PY) -m pip install --platform manylinux2014_aarch64 --implementation cp --python-version 3.12 --only-binary=:all: -r requirements.txt -t .aws-build
	rm -rf .aws-build/boto3 .aws-build/botocore .aws-build/boto3-*.dist-info .aws-build/botocore-*.dist-info
	cp -r src/antares .aws-build/antares

package: build
	aws cloudformation package --template-file infra/template.yaml --s3-bucket $(BUCKET) --s3-prefix antares-dev --output-template .aws-build/packaged.yaml --region $(REGION)

deploy: package
	aws cloudformation deploy --template-file .aws-build/packaged.yaml --stack-name $(STACK) --capabilities CAPABILITY_IAM --region $(REGION) --tags Project=Antares Env=dev ManagedBy=cloudformation --no-fail-on-empty-changeset
