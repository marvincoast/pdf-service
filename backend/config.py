"""
Configurações centralizadas do PDF Service.
Todas as variáveis de ambiente são carregadas aqui.
"""
import os
import logging

# === API & Modelo ===
OLLAMA_API = os.getenv("OLLAMA_API", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")

# === Limites ===
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 15)) * 1024 * 1024
MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", 4000))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 90))

# === Tipos de documentos suportados ===
DOCUMENT_TYPES = {
    "resume": "Currículo/Resume",
    "medical_prescription": "Receita Médica",
    "medical_report": "Prontuário/Laudo Médico",
    "bank_statement": "Extrato Bancário",
    "invoice": "Nota Fiscal/Fatura",
    "contract": "Contrato",
    "educational_certificate": "Certificado/Diploma",
    "legal_document": "Documento Jurídico",
    "technical_report": "Relatório Técnico",
    "other": "Outro/Genérico"
}

# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"pdf-service","message":"%(message)s"}'
)
logger = logging.getLogger("pdf-service")
