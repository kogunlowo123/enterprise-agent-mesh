.PHONY: install test test-unit test-integration lint fmt clean docker-build docker-up docker-down tf-init-aws tf-plan-aws tf-apply-aws

install:
	uv pip install -e "services/api[dev]"
	uv pip install -e "services/agent-runtime[dev]"
	uv pip install -e "services/rag-core[dev]"

test:
	pytest tests/ -v --asyncio-mode=auto

test-unit:
	pytest tests/unit/ -v --asyncio-mode=auto

test-integration:
	pytest tests/integration/ -v --asyncio-mode=auto

lint:
	ruff check services/ tests/
	mypy services/api/src services/agent-runtime/src

fmt:
	ruff format services/ tests/
	ruff check --fix services/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

tf-init-aws:
	terraform -chdir=infra/envs/aws/prod init

tf-plan-aws:
	terraform -chdir=infra/envs/aws/prod plan

tf-apply-aws:
	terraform -chdir=infra/envs/aws/prod apply

tf-init-azure:
	terraform -chdir=infra/envs/azure/prod init

tf-init-gcp:
	terraform -chdir=infra/envs/gcp/prod init
