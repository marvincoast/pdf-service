"""
Fallback inteligente por regex quando a IA não está disponível.
Extrai entidades, valores e padrões do texto bruto.
"""
import re
from backend.config import logger


def intelligent_fallback(text: str, doc_type: str) -> dict:
    """
    Análise por regex quando Ollama falha ou não responde.
    Sempre retorna dados úteis, mesmo sem IA.
    """
    logger.info(f"🔄 Executando fallback inteligente para tipo: {doc_type}")

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Entidades comuns extraídas por regex
    entities = _extract_common_entities(text)

    result = {
        "classification_confidence": 75,
        "source": "fallback_regex",
        "common_entities": entities,
    }

    # Sempre gera um resumo baseado nas primeiras linhas
    preview_lines = [l for l in lines[:10] if len(l) > 10]
    result["detailed_summary"] = (
        f"Documento classificado como '{doc_type}'. "
        f"Contém {len(text.split())} palavras em {len(lines)} linhas. "
        f"Primeiras informações: {' | '.join(preview_lines[:3])}"
    )

    # Lógica específica por tipo
    _type_handlers = {
        "resume": _handle_resume,
        "educational_certificate": _handle_certificate,
        "bank_statement": _handle_bank_statement,
        "medical_prescription": _handle_prescription,
        "medical_report": _handle_medical_report,
        "invoice": _handle_invoice,
        "contract": _handle_contract,
        "legal_document": _handle_legal,
        "technical_report": _handle_technical,
    }

    handler = _type_handlers.get(doc_type, _handle_generic)
    result.update(handler(text, lines, entities))

    logger.info(f"🎯 Fallback concluído: {len(result)} campos extraídos")
    return result


def _extract_common_entities(text: str) -> dict:
    """Extrai entidades comuns a qualquer tipo de documento."""
    return {
        "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
        "phones": re.findall(r'\(?\d{2}\)?[-.\s]?\d{4,5}[-.\s]?\d{4}', text),
        "dates": re.findall(r'\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}', text),
        "cpfs": re.findall(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text),
        "cnpjs": re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text),
        "monetary_values": re.findall(r'R\$\s*[\d.,]+', text),
        "urls": re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text),
    }


def _handle_resume(text, lines, entities):
    """Extração específica para currículos."""
    text_lower = text.lower()
    name = lines[0] if lines else "Não identificado"

    # Skills técnicas (palavras capitalizadas com 4+ chars)
    tech_words = re.findall(r'\b[A-Z][a-zA-Z+#]{3,}\b', text)
    skills = list(set(tech_words))[:15]

    # Seções do currículo
    sections = [l for l in lines if len(l) < 40 and any(
        k in l.lower() for k in ["experiência", "formação", "educação", "habilidades",
                                   "competências", "idiomas", "certificações", "objetivo"]
    )]

    return {
        "personal_info": {
            "name": name,
            "emails": entities["emails"],
            "phones": entities["phones"],
            "urls": entities["urls"]
        },
        "skills_found": skills,
        "sections_found": sections,
        "dates_found": entities["dates"],
        "key_findings": [
            f"Nome identificado: {name}",
            f"{len(skills)} competências técnicas encontradas",
            f"{len(entities['emails'])} email(s) encontrado(s)",
            f"{len(sections)} seções do currículo identificadas"
        ],
        "note": "Análise por fallback regex — dados extraídos por padrão"
    }


def _handle_certificate(text, lines, entities):
    """Extração para certificados/diplomas."""
    name = lines[0] if lines else "Não identificado"
    institutions = [l for l in lines if any(
        k in l.lower() for k in ["universidade", "faculdade", "instituto", "centro", "escola"]
    )]
    courses = [l for l in lines if len(l) > 20 and not any(
        k in l.lower() for k in ["universidade", "faculdade", "certificado", "diploma"]
    )]

    return {
        "student_name": name,
        "institution": institutions[0] if institutions else "Não identificado",
        "course": courses[0] if courses else "Não identificado",
        "dates": entities["dates"],
        "key_findings": [
            f"Estudante: {name}",
            f"Instituição: {institutions[0] if institutions else 'não identificada'}",
            f"{len(entities['dates'])} datas encontradas"
        ],
        "note": "Certificado analisado via fallback regex"
    }


def _handle_bank_statement(text, lines, entities):
    """Extração para extratos bancários."""
    amounts = entities["monetary_values"]

    # Calcula maior valor fora do f-string (backslash não permitido em f-string no Python < 3.12)
    _pat = re.compile(r'[R$.\s]')
    def _to_float(v):
        try:
            return float(_pat.sub('', v).replace(',', '.'))
        except ValueError:
            return 0.0

    maior_valor = max(amounts, key=_to_float) if amounts else 'N/A'

    return {
        "account_holder": lines[0] if lines else "Não identificado",
        "values_found": amounts[:10],
        "total_transactions": len(amounts),
        "dates": entities["dates"],
        "key_findings": [
            f"{len(amounts)} valores monetários encontrados",
            f"{len(entities['dates'])} datas de movimentação",
            f"Maior valor: {maior_valor}"
        ],
        "note": "Extrato analisado via fallback regex"
    }


def _handle_prescription(text, lines, entities):
    """Extração para receitas médicas."""
    meds = re.findall(r'([A-Z][a-zA-Zà-ú\s]+)\s+(\d+\s*mg|\d+\s*ml|\d+\s*mcg)', text)
    crm = re.findall(r'CRM[:\s]*(\d+)', text, re.IGNORECASE)

    return {
        "medications": [{"name": m[0].strip(), "dosage": m[1]} for m in meds[:10]],
        "doctor_crm": crm[0] if crm else "Não encontrado",
        "dates": entities["dates"],
        "key_findings": [
            f"{len(meds)} medicamento(s) identificado(s)",
            f"CRM: {crm[0] if crm else 'não encontrado'}",
        ],
        "note": "Receita analisada via fallback regex"
    }


def _handle_medical_report(text, lines, entities):
    """Extração para laudos/prontuários médicos."""
    crm = re.findall(r'CRM[:\s]*(\d+)', text, re.IGNORECASE)
    cid = re.findall(r'CID[:\s-]*([A-Z]\d{2,3})', text, re.IGNORECASE)

    return {
        "doctor_crm": crm[0] if crm else "Não encontrado",
        "cid_codes": cid,
        "dates": entities["dates"],
        "key_findings": [
            f"CRM: {crm[0] if crm else 'não encontrado'}",
            f"CIDs encontrados: {', '.join(cid) if cid else 'nenhum'}",
        ],
        "note": "Laudo/prontuário analisado via fallback regex"
    }


def _handle_invoice(text, lines, entities):
    """Extração para notas fiscais."""
    nf_number = re.findall(r'(?:NF|Nota\s+Fiscal)[:\s-]*(\d+)', text, re.IGNORECASE)
    chave = re.findall(r'\d{44}', text)

    return {
        "invoice_number": nf_number[0] if nf_number else "Não encontrado",
        "access_key": chave[0] if chave else "Não encontrada",
        "cnpjs": entities["cnpjs"],
        "values": entities["monetary_values"][:10],
        "dates": entities["dates"],
        "key_findings": [
            f"NF nº: {nf_number[0] if nf_number else 'não encontrado'}",
            f"{len(entities['cnpjs'])} CNPJ(s) encontrado(s)",
            f"{len(entities['monetary_values'])} valor(es) monetário(s)",
        ],
        "note": "Nota fiscal analisada via fallback regex"
    }


def _handle_contract(text, lines, entities):
    """Extração para contratos."""
    clauses = [l for l in lines if re.match(r'^(CLÁUSULA|Cláusula|cláusula)\s', l)]

    return {
        "parties_cpf_cnpj": entities["cpfs"] + entities["cnpjs"],
        "clauses_count": len(clauses),
        "values": entities["monetary_values"][:5],
        "dates": entities["dates"],
        "key_findings": [
            f"{len(clauses)} cláusulas identificadas",
            f"{len(entities['cpfs'])} CPF(s) e {len(entities['cnpjs'])} CNPJ(s)",
        ],
        "note": "Contrato analisado via fallback regex"
    }


def _handle_legal(text, lines, entities):
    """Extração para documentos jurídicos."""
    processo = re.findall(r'(?:Processo|Autos)\s*(?:n[ºo°]?\.?\s*)(\d[\d./-]+)', text, re.IGNORECASE)
    oab = re.findall(r'OAB[:/\s]*([A-Z]{2})\s*(\d+)', text, re.IGNORECASE)

    return {
        "case_number": processo[0] if processo else "Não encontrado",
        "lawyers_oab": [f"OAB/{o[0]} {o[1]}" for o in oab],
        "dates": entities["dates"],
        "key_findings": [
            f"Processo: {processo[0] if processo else 'não encontrado'}",
            f"{len(oab)} advogado(s) identificado(s)",
        ],
        "note": "Documento jurídico analisado via fallback regex"
    }


def _handle_technical(text, lines, entities):
    """Extração para relatórios técnicos."""
    sections = [l for l in lines if len(l) < 50 and l.isupper() or (
        len(l) < 60 and any(k in l.lower() for k in [
            "introdução", "metodologia", "resultados", "conclusão",
            "referências", "abstract", "objetivo"
        ])
    )]

    return {
        "sections_found": sections[:10],
        "dates": entities["dates"],
        "urls": entities["urls"],
        "key_findings": [
            f"{len(sections)} seções do relatório identificadas",
            f"{len(text.split())} palavras no documento",
        ],
        "note": "Relatório técnico analisado via fallback regex"
    }


def _handle_generic(text, lines, entities):
    """Extração genérica para qualquer documento."""
    return {
        "summary_preview": " ".join(lines[:5])[:300],
        "word_count": len(text.split()),
        "line_count": len(lines),
        "key_findings": [
            f"Documento com {len(text.split())} palavras",
            f"{len(entities['emails'])} email(s), {len(entities['phones'])} telefone(s)",
            f"{len(entities['monetary_values'])} valor(es) monetário(s)",
        ],
        "note": "Documento genérico analisado via fallback regex"
    }
