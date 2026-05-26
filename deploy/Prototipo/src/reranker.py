"""
Reranker cross-encoder post-retrieval (ONNX int8 cuantizado via fastembed).

Aumenta la precision del retrieval reordenando los top-k chunks que devuelve
ChromaDB con un cross-encoder multilingue. El cross-encoder evalua (query, chunk)
como par conjunto, a diferencia del bi-encoder de embeddings que los codifica
por separado. Esto captura interacciones query-chunk que la similitud coseno
no ve.

Cambio clave respecto a la version anterior: usamos fastembed (binario ONNX
cuantizado a int8) en lugar de sentence_transformers (PyTorch float32). En CPU
ARM (Orange Pi) esto es ~3-5x mas rapido sin perdida medible de calidad.

Modelo: BAAI/bge-reranker-v2-m3 (multilingue, ~150 MB en formato ONNX int8
vs ~568 MB del PyTorch original).

Fallback: si fastembed no carga (arquitectura no soportada, descarga fallida,
o desactivado por config), devuelve los documentos en el orden original
truncados a top_n, sin romper el pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RERANKER_MODEL, RERANKER_ENABLED, RERANKER_TOP_N

_logger = logging.getLogger(__name__)

# Cache de modelo a nivel de modulo para evitar recargar en cada query.
_cached_reranker = None
_reranker_load_failed = False


def get_reranker():
    """
    Carga (y cachea) el cross-encoder ONNX. Devuelve None si falla o esta
    desactivado.

    Se importa fastembed de forma perezosa para que el pipeline siga
    funcionando si la libreria no esta instalada o no compila en la
    arquitectura objetivo.
    """
    global _cached_reranker, _reranker_load_failed

    if not RERANKER_ENABLED:
        return None
    if _reranker_load_failed:
        return None
    if _cached_reranker is not None:
        return _cached_reranker

    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _logger.info("Cargando reranker ONNX int8: %s", RERANKER_MODEL)
        _cached_reranker = TextCrossEncoder(model_name=RERANKER_MODEL)
        _logger.info("Reranker ONNX cargado.")
        return _cached_reranker
    except Exception as exc:
        _logger.warning(
            "No se pudo cargar el reranker ONNX (%s). Se continua sin rerank.", exc
        )
        _reranker_load_failed = True
        return None


def rerank_documents(
    query: str,
    docs: List[Document],
    top_n: int = RERANKER_TOP_N,
    reranker=None,
) -> List[Document]:
    """
    Reordena `docs` segun la relevancia del par (query, doc) y devuelve top_n.

    Si `docs` tiene menos elementos que top_n, devuelve la lista ordenada completa.
    Si no hay reranker disponible, hace un fallback truncando al top_n original
    confiando en el orden por similitud coseno del retriever.
    """
    if not docs:
        return []

    if reranker is None:
        reranker = get_reranker()

    if reranker is None:
        return docs[:top_n]

    try:
        passages = [d.page_content for d in docs]
        scores = list(reranker.rerank(query, passages))
        scored = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_n]]
    except Exception as exc:
        _logger.warning("Reranker fallo en runtime (%s). Fallback a orden original.", exc)
        return docs[:top_n]
