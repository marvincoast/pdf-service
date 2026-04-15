"""
Cliente para comunicação com o Ollama LLM.
Prompts adaptativos e detalhados por tipo de documento.
"""
import json
import re
import requests
from backend.config import OLLAMA_API, LLM_MODEL, OLLAMA_TIMEOUT, MAX_TEXT_CHARS, logger


# Prompts detalhados por tipo — cada um pede finalidade + agrupamento de informações
_PROMPTS = {
    "resume": """Você é um especialista em RH e análise de currículos. Analise o currículo abaixo e retorne APENAS um JSON válido com esta estrutura exata:
{
  "document_purpose": "Explique em 2 frases para que serve este documento e qual seu objetivo principal (ex: apresentar candidato para vaga de X)",
  "detailed_summary": "Resumo profissional de 3-5 frases: perfil do candidato, área de atuação, nível de senioridade e diferenciais",
  "grouped_info": {
    "identificacao": {"name": "nome completo", "email": "email", "phone": "telefone", "location": "cidade/estado"},
    "experiencia_profissional": [{"cargo": "cargo", "empresa": "empresa", "periodo": "período", "descricao": "atividades principais"}],
    "formacao": [{"titulo": "grau/título", "instituicao": "instituição", "ano": "ano"}],
    "competencias": {"tecnicas": ["habilidades técnicas"], "soft_skills": ["competências comportamentais"], "idiomas": ["idiomas e nível"], "certificacoes": ["certificações"]}
  },
  "key_findings": ["3-5 pontos mais relevantes do perfil para um recrutador"],
  "recommendations": ["2-3 sugestões para melhorar o currículo ou o perfil"]
}
Texto do currículo:
""",

    "medical_prescription": """Você é um analista de documentos médicos. Analise esta receita médica e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases o propósito desta receita: quem prescreveu para quem, e para qual condição/tratamento",
  "detailed_summary": "Resumo de 2-3 frases: médico, paciente, número de medicamentos prescritos e indicação geral",
  "grouped_info": {
    "paciente": "nome do paciente",
    "medico": {"nome": "nome do médico", "crm": "CRM", "especialidade": "especialidade"},
    "data_emissao": "data da prescrição",
    "medicamentos": [{"nome": "medicamento", "dosagem": "dosagem", "frequencia": "como tomar", "duracao": "por quanto tempo", "via": "oral/injetável/etc"}],
    "diagnostico": "condição ou indicação clínica mencionada"
  },
  "key_findings": ["alertas importantes sobre a prescrição"],
  "recommendations": ["observações de segurança ou atenção ao paciente"]
}
Texto da receita:
""",

    "medical_report": """Analise este laudo/prontuário médico e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve este documento: tipo de laudo, quem emitiu e para qual finalidade",
  "detailed_summary": "Resumo de 3-5 frases: tipo do exame, paciente, achados principais e conclusão médica",
  "grouped_info": {
    "paciente": "nome do paciente",
    "medico_responsavel": {"nome": "médico", "crm": "CRM"},
    "tipo_exame": "tipo de exame ou consulta",
    "data": "data do exame",
    "achados_clinicos": ["achados do exame em ordem de relevância"],
    "diagnostico": "diagnóstico ou hipótese diagnóstica",
    "conclusao": "conclusão do laudo"
  },
  "key_findings": ["3-5 achados mais relevantes do documento médico"],
  "recommendations": ["recomendações médicas ou próximos passos mencionados"]
}
Texto do documento:
""",

    "bank_statement": """Analise este extrato bancário e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve este extrato: quem é o titular, de qual banco e o que ele demonstra",
  "detailed_summary": "Resumo de 3-5 frases: titular, banco, período, saldo final e tendência geral de movimentação",
  "grouped_info": {
    "titular": "nome do titular",
    "banco": "nome do banco",
    "conta": "agência e número da conta",
    "periodo": "período coberto pelo extrato",
    "saldos": {"inicial": "saldo inicial", "final": "saldo final"},
    "totais": {"creditos": "total de créditos", "debitos": "total de débitos"},
    "maiores_movimentacoes": [{"data": "data", "descricao": "descrição", "valor": "valor", "tipo": "crédito/débito"}]
  },
  "key_findings": ["3-5 observações relevantes sobre a movimentação financeira"],
  "recommendations": ["sugestões financeiras baseadas no extrato"]
}
Texto do extrato:
""",

    "invoice": """Analise esta nota fiscal/fatura e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve esta nota fiscal: o que documenta, entre quais partes e qual operação",
  "detailed_summary": "Resumo de 2-3 frases: emitente, destinatário, tipo de produto/serviço e valor total",
  "grouped_info": {
    "emitente": {"razao_social": "nome", "cnpj": "CNPJ", "endereco": "endereço"},
    "destinatario": {"nome": "nome", "cnpj_cpf": "documento"},
    "nota_fiscal": {"numero": "número NF", "data_emissao": "data", "chave_acesso": "chave de 44 dígitos se houver"},
    "itens": [{"descricao": "item", "quantidade": "qtd", "valor_unit": "preço unit.", "total": "total item"}],
    "valores": {"subtotal": "subtotal", "impostos": "total impostos", "total": "valor total"}
  },
  "key_findings": ["pontos relevantes da nota fiscal"],
  "recommendations": ["observações fiscais ou contábeis relevantes"]
}
Texto da nota fiscal:
""",

    "educational_certificate": """Analise este certificado/diploma e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve este certificado: o que comprova, a quem foi emitido e qual sua validade/utilidade",
  "detailed_summary": "Resumo de 2-3 frases: beneficiário, instituição, curso/programa e período",
  "grouped_info": {
    "beneficiario": "nome do estudante/participante",
    "instituicao": {"nome": "nome da instituição", "credenciamento": "credenciamento se mencionado"},
    "curso": {"nome": "nome do curso", "tipo": "graduação/pós/extensão/livre", "carga_horaria": "horas"},
    "periodo": {"inicio": "data início", "conclusao": "data conclusão"},
    "resultado": {"nota": "nota ou conceito se informado", "situacao": "aprovado/concluído/etc"}
  },
  "key_findings": ["pontos que valorizam este certificado"],
  "recommendations": ["como este certificado pode ser utilizado ou valorizado"]
}
Texto do certificado:
""",

    "contract": """Analise este contrato e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve este contrato: tipo de relação jurídica que estabelece e obrigações principais",
  "detailed_summary": "Resumo de 3-5 frases: tipo de contrato, partes, objeto, prazo e valor",
  "grouped_info": {
    "tipo_contrato": "tipo (prestação de serviço, locação, trabalho, compra e venda, etc.)",
    "partes": [{"papel": "contratante/contratado", "nome": "nome", "documento": "CPF/CNPJ"}],
    "objeto": "o que está sendo contratado",
    "condicoes_financeiras": {"valor": "valor do contrato", "forma_pagamento": "forma/prazo de pagamento"},
    "vigencia": {"inicio": "início", "termino": "término", "renovacao": "condições de renovação"},
    "clausulas_principais": ["cláusulas mais importantes resumidas"]
  },
  "key_findings": ["pontos de atenção do contrato para as partes"],
  "recommendations": ["alertas jurídicos ou cláusulas que merecem atenção especial"]
}
Texto do contrato:
""",

    "legal_document": """Analise este documento jurídico e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve este documento: tipo de peça, em qual processo/contexto existe e qual seu objetivo legal",
  "detailed_summary": "Resumo de 3-5 frases: tipo de peça jurídica, partes, objeto da ação e decisão/pedido principal",
  "grouped_info": {
    "tipo_peca": "petição/sentença/despacho/recurso/contrato/etc",
    "processo": {"numero": "número do processo", "vara_tribunal": "vara ou tribunal", "comarca": "comarca/jurisdição"},
    "partes": [{"papel": "autor/réu/requerente", "nome": "nome", "advogado": "advogado e OAB"}],
    "materia": "assunto jurídico (trabalhista, cível, criminal, etc.)",
    "pedido_decisao": "pedido principal ou decisão proferida",
    "datas_importantes": ["datas de prazos, audiências ou decisões"]
  },
  "key_findings": ["pontos jurídicos mais relevantes do documento"],
  "recommendations": ["observações práticas ou alertas sobre prazos e obrigações"]
}
Texto do documento:
""",

    "technical_report": """Analise este relatório técnico/acadêmico e retorne APENAS um JSON válido:
{
  "document_purpose": "Explique em 2 frases para que serve este relatório: qual problema aborda, qual sua finalidade e a quem se destina",
  "detailed_summary": "Resumo de 3-5 frases: tema, metodologia utilizada, principais resultados e conclusões",
  "grouped_info": {
    "identificacao": {"titulo": "título do relatório", "autores": ["autores"], "data": "data", "instituicao": "instituição se mencionada"},
    "contexto": {"objetivo": "objetivo do estudo", "problema_abordado": "problema ou questão de pesquisa"},
    "desenvolvimento": {"metodologia": "metodologia resumida", "ferramentas_usadas": ["ferramentas, tecnologias ou métodos"]},
    "resultados": {"principais_resultados": ["resultados em ordem de relevância"], "conclusoes": ["conclusões dos autores"]}
  },
  "key_findings": ["3-5 achados ou contribuições mais importantes do relatório"],
  "recommendations": ["recomendações dos autores ou próximos passos sugeridos"]
}
Texto do relatório:
""",

    "other": """Analise este documento e retorne APENAS um JSON válido com análise completa:
{
  "document_purpose": "Explique em 2 frases para que serve este documento: qual seu tipo, objetivo e para quem foi criado",
  "detailed_summary": "Resumo de 3-5 frases descrevendo o conteúdo, propósito e informações mais relevantes",
  "grouped_info": {
    "tipo_documento": "classificação e natureza do documento",
    "entidades_principais": [{"tipo": "pessoa/organização/local", "nome": "identificação"}],
    "topicos_abordados": ["principais temas ou seções do documento"],
    "datas_importantes": ["datas relevantes encontradas"],
    "valores_mencionados": ["valores monetários ou numéricos relevantes"],
    "estrutura": ["seções ou partes identificadas no documento"]
  },
  "key_findings": ["3-5 informações mais importantes do documento"],
  "recommendations": ["sugestão de próximos passos ou uso do documento"]
}
Texto do documento:
"""
}


def call_ollama(text: str, doc_type: str) -> dict | None:
    """
    Chama Ollama com prompt adaptativo baseado no tipo de documento.
    Retorna dict com análise ou None se falhar.
    """
    truncated = text[:MAX_TEXT_CHARS]
    base_prompt = _PROMPTS.get(doc_type, _PROMPTS["other"])
    prompt = f"{base_prompt}\n{truncated}"

    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
            "num_predict": 800
        }
    }

    # Ativa modo JSON nativo se suportado pelo modelo
    if any(m in LLM_MODEL for m in ["phi3", "qwen", "llama", "mistral"]):
        payload["format"] = "json"

    logger.info(f"🤖 Chamando Ollama: modelo={LLM_MODEL}, texto={len(truncated)} chars")

    resp = requests.post(
        f"{OLLAMA_API}/api/generate",
        json=payload,
        timeout=OLLAMA_TIMEOUT
    )
    resp.raise_for_status()

    llm_text = resp.json().get("response", "").strip()
    logger.info(f"📝 Ollama respondeu: {len(llm_text)} chars")

    # Tenta extrair JSON mesmo se vier com texto extra
    return _extract_json(llm_text)


def _extract_json(text: str) -> dict | None:
    """Extrai JSON de texto misto (markdown, explicações, etc.)"""
    # Tenta parse direto
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Tenta extrair bloco JSON do texto
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    logger.warning("⚠️ Não foi possível extrair JSON da resposta do LLM")
    return None
