"""
Rotas de análise de PDFs.
Blueprint Flask para /health e /analyze.
"""
import time
from flask import Blueprint, request, jsonify
from backend.config import DOCUMENT_TYPES, logger
from backend.services.pdf_extractor import extract_text
from backend.services.classifier import classify_document
from backend.services.ollama_client import call_ollama
from backend.utils.fallback_parser import intelligent_fallback

analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "pdf-service",
        "version": "4.0-modular"
    }), 200


@analyze_bp.route("/analyze", methods=["POST"])
def analyze_pdf():
    """
    Endpoint principal de análise de PDF.
    Pipeline: Upload → Extração → Classificação → IA → Fallback → Resposta
    """
    start_time = time.time()

    # Validação de entrada
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    if file.filename == "" or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Apenas PDFs válidos"}), 400

    try:
        # 1. EXTRAÇÃO do PDF
        pdf_bytes = file.read()
        extraction = extract_text(pdf_bytes)
        raw_text = extraction["raw_text"]

        if not raw_text.strip():
            return jsonify({"error": "PDF vazio ou não legível"}), 400

        logger.info(f"📄 PDF: {file.filename} | {len(raw_text)} chars | {extraction['num_pages']} páginas")

        # 2. CLASSIFICAÇÃO do documento
        classification = classify_document(raw_text)
        doc_type = classification["doc_type"]
        logger.info(f"🎯 Tipo: {classification['label']} (confiança: {classification['confidence']}%)")

        # 3. ANÁLISE via IA (com fallback automático)
        ai_result = None
        analysis_method = "fallback_intelligent"
        try:
            ai_result = call_ollama(raw_text, doc_type)
            if ai_result:
                analysis_method = "ai"
                logger.info(f"✅ IA respondeu em {time.time() - start_time:.1f}s")
        except Exception as e:
            logger.warning(f"⚠️ IA falhou ({type(e).__name__}): {str(e)[:100]}")

        # 4. FALLBACK inteligente (sempre executa para complementar)
        fallback_result = intelligent_fallback(raw_text, doc_type)

        # 5. MERGE dos resultados (IA tem prioridade, fallback complementa)
        final_result = ai_result if ai_result else {}
        for key, value in fallback_result.items():
            if key not in final_result or not final_result[key]:
                final_result[key] = value

        # 6. RESPOSTA estruturada
        response = {
            "filename": file.filename,
            "document_type": doc_type,
            "document_type_label": DOCUMENT_TYPES.get(doc_type, doc_type),
            "confidence": classification["confidence"],
            "text_length": len(raw_text),
            "pages": extraction["num_pages"],
            "pdf_metadata": extraction.get("pdf_metadata", {}),
            "processing_time_sec": round(time.time() - start_time, 2),
            "analysis_method": analysis_method,
            "classification_scores": classification.get("scores", {}),
            "extracted_data": final_result
        }
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Erro crítico: {e}", exc_info=True)
        return jsonify({"error": "Erro interno ao processar"}), 500
