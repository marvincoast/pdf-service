# 📄 PDF AI Service

> Motor de análise inteligente de documentos PDF com IA local — classificação automática, extração de entidades e resumos detalhados.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 O que é?

PDF AI Service é uma aplicação que **analisa documentos PDF automaticamente** usando IA local (Ollama). O sistema:

1. **Extrai** texto do PDF via PyMuPDF
2. **Classifica** o tipo de documento (currículo, nota fiscal, contrato, etc.)
3. **Analisa** via LLM local com prompts adaptativos por tipo
4. **Retorna** JSON estruturado com resumo, entidades e recomendações

**Zero dados na nuvem** — todo processamento é local.

---

## 🏗️ Arquitetura

```
📄 PDF Upload
    ↓ POST /analyze
📥 PyMuPDF (Extração de texto + metadados)
    ↓
🎯 Classificador (Keyword scoring → 10 tipos)
    ↓
🧠 Ollama LLM (Prompt adaptativo → análise semântica)
    ↓
🔄 Fallback Regex (complementa ou substitui IA)
    ↓
📤 JSON Estruturado (resumo + entidades + recomendações)
```

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Função |
|---|---|---|
| **Backend** | Python 3.11 + Flask | API REST com Blueprint e App Factory |
| **IA Local** | Ollama + Phi-3 / Qwen 3.5 | Inferência LLM sem cloud |
| **Extração PDF** | PyMuPDF (fitz) | Texto bruto + metadados |
| **Servidor** | Gunicorn | 2 workers + 2 threads |
| **Container** | Docker + Compose | Build e deploy isolados |
| **Frontend** | HTML5 + CSS3 + Vanilla JS | Interface glassmorphism com 3D parallax |

---

## 📁 Estrutura do Projeto

```
pdf-service/
├── backend/
│   ├── __init__.py              # App Factory (Flask)
│   ├── config.py                # Configurações centralizadas
│   ├── routes/
│   │   └── analyze.py           # Rotas /health e /analyze
│   ├── services/
│   │   ├── pdf_extractor.py     # PyMuPDF — extração de texto
│   │   ├── classifier.py        # Classificação por keywords
│   │   └── ollama_client.py     # Comunicação com Ollama LLM
│   └── utils/
│       └── fallback_parser.py   # Fallback regex inteligente
│
├── frontend/
│   ├── index.html               # Página principal
│   ├── arquitetura.html         # Diagrama de arquitetura
│   ├── stacks.html              # Stacks tecnológicas
│   └── assets/
│       ├── css/
│       │   ├── main.css         # Design system
│       │   ├── animations.css   # Animações
│       │   └── components.css   # Componentes
│       └── js/
│           └── app.js           # Lógica principal
│
├── tests/
│   └── test_app.py              # Testes da API
├── docs/
│   ├── ARCHITECTURE.md          # Documentação técnica
│   ├── API.md                   # Documentação da API
│   └── DEPLOYMENT.md            # Guia de deploy
│
├── app.py                       # Entry point
├── Dockerfile                   # Build da imagem
├── docker-compose.yml           # Orquestração
├── requirements.txt             # Dependências
├── requirements-dev.txt         # Deps de desenvolvimento
├── Makefile                     # Comandos úteis
├── .env.example                 # Template de variáveis
└── .gitignore
```

---

## 🚀 Setup Rápido

### Pré-requisitos
- Python 3.11+
- [Ollama](https://ollama.ai) instalado e rodando
- Um modelo LLM baixado: `ollama pull phi3:mini`

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/marvincoast/pdf-service.git
cd pdf-service

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis (opcional)
cp .env.example .env

# Inicie o servidor
python app.py
```

### Com Docker

```bash
# Build e run
docker-compose up -d --build

# Ou manualmente
docker build -t pdf-service .
docker run -p 8080:8080 pdf-service
```

---

## 📡 API

### `GET /health`
```json
{"status": "healthy", "service": "pdf-service", "version": "4.0-modular"}
```

### `POST /analyze`
Upload de PDF via multipart form-data.

**Request:**
```bash
curl -X POST http://localhost:8080/analyze \
  -F "file=@meu_documento.pdf"
```

**Response:**
```json
{
  "filename": "curriculo.pdf",
  "document_type": "resume",
  "document_type_label": "Currículo/Resume",
  "confidence": 85,
  "pages": 2,
  "text_length": 3200,
  "processing_time_sec": 12.5,
  "analysis_method": "ai",
  "extracted_data": {
    "detailed_summary": "Profissional com 5 anos de experiência em...",
    "personal_info": {"name": "João Silva", "email": "joao@email.com"},
    "skills": ["Python", "Docker", "AWS"],
    "key_findings": ["5 anos de experiência", "Certificação AWS"],
    "recommendations": ["Adicionar portfolio", "Incluir métricas"]
  }
}
```

---

## 📋 Tipos de Documentos Suportados

| Tipo | Label | Keywords Detectadas |
|---|---|---|
| `resume` | Currículo/Resume | experiência, formação, habilidades |
| `medical_prescription` | Receita Médica | medicamento, dosagem, CRM |
| `medical_report` | Prontuário/Laudo | diagnóstico, exame, anamnese |
| `bank_statement` | Extrato Bancário | saldo, débito, crédito, PIX |
| `invoice` | Nota Fiscal | CNPJ, NF-e, valor total |
| `educational_certificate` | Certificado/Diploma | universidade, carga horária |
| `contract` | Contrato | cláusula, vigência, foro |
| `legal_document` | Documento Jurídico | processo, OAB, sentença |
| `technical_report` | Relatório Técnico | metodologia, resultados |
| `other` | Genérico | fallback automático |

---

## 🧪 Testes

```bash
# Instale deps de dev
pip install -r requirements-dev.txt

# Execute os testes
pytest tests/ -v

# Lint
flake8 backend/ app.py --max-line-length=120
```

---

## 👨‍💻 Autor

**Marvin Costa** — SRE / Cloud Engineer

- [LinkedIn](https://linkedin.com/in/marvincost)
- [GitHub](https://github.com/marvincoast)

---

## 📄 Licença

MIT License — use livremente.
