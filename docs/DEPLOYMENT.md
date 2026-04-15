# Deploy — PDF AI Service

## Opção 1: Docker (Recomendado)

### Pré-requisitos
- Docker e Docker Compose instalados
- Ollama rodando no host (ou em container separado)

### Deploy
```bash
# Clone e entre no diretório
git clone https://github.com/marvincoast/pdf-service.git
cd pdf-service

# Build e start
docker-compose up -d --build

# Verificar
curl http://localhost:8080/health
```

### Variáveis de Ambiente
Edite `docker-compose.yml` ou crie um `.env`:
```env
OLLAMA_API=http://host.docker.internal:11434
LLM_MODEL=phi3:mini
MAX_FILE_SIZE_MB=15
MAX_TEXT_CHARS=4000
OLLAMA_TIMEOUT=90
```

---

## Opção 2: Local (Desenvolvimento)

```bash
# Instale dependências
pip install -r requirements.txt

# Inicie o Ollama
ollama serve &
ollama pull phi3:mini

# Rode a aplicação
python app.py
```

---

## Opção 3: Gunicorn (Produção)

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 2 app:app
```

---

## Frontend

O frontend é estático e pode ser servido por qualquer servidor web:

```bash
# Exemplo com Python
cd frontend/
python -m http.server 3000
```

Ou servir via Nginx, Caddy, etc.

---

## Ollama — Modelos Recomendados

| Modelo | Tamanho | Velocidade | Qualidade |
|---|---|---|---|
| `phi3:mini` | 2.3GB | Rápido | Boa |
| `qwen2.5:3b` | 2.0GB | Rápido | Boa |
| `llama3.2:3b` | 2.0GB | Médio | Muito Boa |
| `mistral:7b` | 4.1GB | Lento (CPU) | Excelente |
