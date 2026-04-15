"""
Classificador de tipos de documentos por keyword scoring.
"""
import json
from backend.config import DOCUMENT_TYPES, logger


# Keywords por tipo de documento (peso implícito: mais keywords = mais específico)
_KEYWORD_MAP = {
    "resume": [
        "currículo", "curriculum vitae", "resume", "experiência profissional",
        "formação acadêmica", "habilidades", "competências", "objetivo profissional",
        "dados pessoais", "idiomas", "linkedin", "github", "portfólio"
    ],
    "medical_prescription": [
        "receita médica", "prescrição", "medicamento", "dosagem", "médico",
        "crm", "paciente", "tomar", "comprimido", "mg", "via oral",
        "posologia", "uso contínuo", "uso interno"
    ],
    "medical_report": [
        "prontuário", "laudo", "exame", "diagnóstico", "sintomas",
        "tratamento", "anamnese", "evolução", "hemograma", "ultrassom",
        "ressonância", "tomografia", "cid"
    ],
    "bank_statement": [
        "extrato bancário", "conta corrente", "saldo", "débito", "crédito",
        "agência", "banco", "transação", "movimentação", "pix",
        "transferência", "tarifa", "rendimento"
    ],
    "invoice": [
        "nota fiscal", "nf-e", "nfe", "fatura", "cnpj", "valor total",
        "imposto", "emitente", "destinatário", "icms", "iss",
        "base de cálculo", "chave de acesso"
    ],
    "educational_certificate": [
        "certificado", "diploma", "certificação", "concluiu", "graduação",
        "universidade", "faculdade", "carga horária", "coordenador",
        "bacharelado", "licenciatura", "pós-graduação", "mestrado"
    ],
    "contract": [
        "contrato", "cláusula", "vigência", "partes contratantes", "obrigações",
        "rescisão", "foro", "assinatura", "testemunha", "contratante",
        "contratado", "objeto do contrato"
    ],
    "legal_document": [
        "processo nº", "autos", "sentença", "despacho", "petição",
        "advogado", "oab", "juízo", "vara", "tribunal",
        "intimação", "mandado", "recurso"
    ],
    "technical_report": [
        "relatório técnico", "metodologia", "resultados", "conclusão",
        "análise", "dados", "gráfico", "tabela", "referências",
        "abstract", "introdução", "objetivo geral"
    ],
}


def classify_document(text: str) -> dict:
    """
    Classifica o tipo de documento baseado em keywords.

    Returns:
        dict com: doc_type, label, confidence, scores
    """
    text_lower = text.lower()
    scores = {}

    for doc_type, keywords in _KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[doc_type] = score

    if not scores:
        return {
            "doc_type": "other",
            "label": DOCUMENT_TYPES["other"],
            "confidence": 0,
            "scores": {}
        }

    best_type = max(scores, key=scores.get)
    max_score = scores[best_type]
    total_keywords = len(_KEYWORD_MAP.get(best_type, []))
    confidence = min(100, int((max_score / max(total_keywords, 1)) * 100))

    logger.info(f"📊 Scores: {json.dumps(scores)}")
    logger.info(f"🎯 Classificado: {best_type} (confiança: {confidence}%)")

    return {
        "doc_type": best_type,
        "label": DOCUMENT_TYPES.get(best_type, best_type),
        "confidence": confidence,
        "scores": scores
    }
