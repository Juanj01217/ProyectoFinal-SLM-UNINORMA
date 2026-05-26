"""Configuracion centralizada del prototipo RAG."""
import os
from pathlib import Path

# === Rutas ===
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_PDF_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma_db"

# === Fuente de PDFs (relativa a la raiz del repo) ===
SCRAPING_PDF_DIR = PROJECT_ROOT.parent / "WebScraping" / "reglamentos"

# === Parametros de Chunking ===
# Chunking jerarquico: cada articulo del reglamento es la unidad minima.
# Solo se subdivide si excede ARTICLE_MAX_CHARS. CHUNK_SIZE/CHUNK_OVERLAP se
# mantienen como fallback para documentos sin estructura de articulos.
# ARTICLE_MAX_CHARS subido de 2500 a 4000: listas largas como "8. Son derechos
# de los estudiantes: a... m." (Reg_Estudiantes) cabian fragmentadas. Con 4000
# entran completas en un solo chunk -> el SLM ve los 13 items de una.
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
ARTICLE_MAX_CHARS = 4000
ARTICLE_MIN_CHARS = 80

# Version del chunker. Incrementar cuando cambie la logica de detectar
# articulos o partir texto, para que el entrypoint detecte mismatch y
# re-indexe automaticamente la base vectorial.
# v3-secciones: chunking sobre full_text + deteccion de secciones numeradas
# "N. Son derechos...". Resuelve fragmentacion cross-page de listas.
CHUNKER_VERSION = "v3-secciones"

# === Modelos de Embedding ===
EMBEDDING_MODELS = {
    "minilm-multilingual": "paraphrase-multilingual-MiniLM-L12-v2",
    "mpnet-multilingual": "paraphrase-multilingual-mpnet-base-v2",
}
DEFAULT_EMBEDDING_MODEL = "mpnet-multilingual"

# === Reranker (cross-encoder) ===
# Modelo cross-encoder multilingue que reordena los chunks recuperados.
# Multiplica el retrieval_accuracy y permite reducir top_k post-rerank,
# compactando el contexto que ve el SLM y bajando latencia de generacion.
# Nota: fastembed 0.8+ NO soporta 'BAAI/bge-reranker-v2-m3'. Usamos
# 'jinaai/jina-reranker-v2-base-multilingual' que SI esta en su catalogo de
# modelos ONNX y es multilingue nativo (espanol incluido).
RERANKER_MODEL = "jinaai/jina-reranker-v2-base-multilingual"
# Activado: fastembed (ONNX int8) carga el modelo de reranking. Si falla en
# alguna arquitectura, el pipeline cae automaticamente al slicing por
# similitud coseno del vector store.
RERANKER_ENABLED = True
# Subido de 3 -> 5: con 3 chunks tiene riesgo de no entregar el chunk con
# la lista completa de derechos/deberes al SLM cuando el reranker no es
# perfecto. 5 chunks da margen sin saturar el prompt (~10k chars).
RERANKER_TOP_N = 5

# === Configuracion de Ollama ===
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
SLM_MODELS = [
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "llama3.2:1b",
    "llama3.2:3b",
    "phi3:mini",
    "gemma3:1b",
    "mistral:7b",
    "llama3.1:8b",
]
DEFAULT_SLM_MODEL = "qwen2.5:1.5b"

# Modelo dedicado (mas pequeno) para query rewriting. Cualquier modelo de 0.5-1.5B
# rinde bien para una tarea tan acotada y corta la doble llamada LLM a la mitad
# en terminos de tiempo.
REWRITE_SLM_MODEL = "qwen2.5:1.5b"

# keep_alive: tiempo que Ollama mantiene el modelo cargado tras inactividad.
# Sin este valor, el primer query tras 5 min sufre cold-start de 5-15s.
OLLAMA_KEEP_ALIVE = "30m"

# === Parametros de Recuperacion ===
# Con RERANKER_ENABLED=False el vector store es la unica senal de ordenamiento,
# asi que sobre-traer (TOP_K=12) inundaba el prompt con ruido y disparaba la
# tasa de alucinacion. Bajamos a 8 candidatos y subimos el threshold de
# similitud para filtrar chunks debiles antes de que lleguen al SLM.
RETRIEVAL_TOP_K = 8
RETRIEVAL_SCORE_THRESHOLD = 0.35

# === Parametros de Generacion ===
# temperature=0.0 + top_p/top_k acotados en create_llm() garantizan que la misma
# pregunta produzca la misma respuesta. Imprescindible para un asistente
# normativo donde la consistencia importa mas que la creatividad.
TEMPERATURE = 0.0
# Subido de 700 -> 1100: listas largas (13 derechos a-m del Reglamento de
# Estudiantes, ~2.5KB de texto literal) requieren ~700-900 tokens solo para
# los items, mas la cita por linea. 1100 da margen sin saturar la latencia
# en SLMs pequenos.
MAX_TOKENS = 1100
