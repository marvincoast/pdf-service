.PHONY: run docker-build docker-up docker-down test lint

# Roda localmente
run:
	python app.py

# Docker
docker-build:
	docker build -t pdf-service .

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

# Testes
test:
	pytest tests/ -v

# Lint
lint:
	flake8 backend/ app.py --max-line-length=120
