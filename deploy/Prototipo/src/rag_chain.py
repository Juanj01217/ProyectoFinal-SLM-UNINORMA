"""Cadena RAG: combina retriever + LLM para Q&A sobre normatividad."""
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

_logger = logging.getLogger(__name__)


def _dedup_answer(text: str) -> str:
    """Elimina lineas duplicadas de la respuesta del LLM."""
    lines = text.splitlines()
    seen: set = set()
    result: list = []
    for line in lines:
        normalized = re.sub(r"\s+", " ", line.strip()).lower()
        if normalized and normalized in seen:
            continue
        if normalized:
            seen.add(normalized)
        result.append(line)
    return "\n".join(result)


# Patrones de "leak" del SLM: cuando termina la respuesta y empieza a copiar
# los headers de fragmentos del prompt o a repetir la enumeracion.
_LEAK_PATTERNS = (
    # Header de fragmento completo: "[Art. N] [Fuente: ...]"
    re.compile(r"\n\s*\[Art\.\s*\d+[a-z]?\][^\n]*\[Fuente:", re.IGNORECASE),
    # Header parcial: "[Fuente: xxx]" en linea propia
    re.compile(r"\n\s*\[Fuente:[^\]]+\]\s*\n", re.IGNORECASE),
    # Re-enumeracion: "[Art. N] Son derechos/deberes..." indica que el SLM
    # esta regenerando la respuesta desde el principio.
    re.compile(r"\n\s*\[Art\.\s*\d+\]\s+Son\s+(?:derechos|deberes)", re.IGNORECASE),
    # Inicio de re-enumeracion sin cita: el SLM repite "8. Son derechos..."
    re.compile(r"\n\s*\d{1,3}\.\s+Son\s+(?:derechos|deberes)\s+(?:de|del)", re.IGNORECASE),
    # Headers de prompt filtrados al output
    re.compile(r"\n\s*PREGUNTA(?:\s+del\s+usuario)?\s*:", re.IGNORECASE),
    re.compile(r"\n\s*Fragmentos?\s+normativos?\s*:", re.IGNORECASE),
    re.compile(r"\n\s*REGLAS\s*:", re.IGNORECASE),
    re.compile(r"\n\s*INSTRUCCION\s*:", re.IGNORECASE),
    re.compile(r"\n\s*Tu\s+respuesta", re.IGNORECASE),
    # Cierre con "No encontre" despues de haber respondido = artefacto
    re.compile(r"\n\s*No\s+encontre\s+informacion", re.IGNORECASE),
    # Leak de las pistas inyectadas: si el SLM regurgita la nota interna
    re.compile(r"\n\s*Pista\s+de\s+formato\s*:", re.IGNORECASE),
    re.compile(r"\n\s*MODO\s+(?:ESPECIFICO|LISTA)\s*:", re.IGNORECASE),
)


# Patrones de leak AL INICIO de la respuesta (posicion 0, sin newline previo).
# Capturan el caso "1) [Art. 2] [Fuente: ...]" donde el SLM enumera chunk
# headers en vez de sintetizar la respuesta.
_LEAK_PATTERNS_AT_START = (
    re.compile(r"^\s*\d+\)\s*\[Art\.\s*\d+[a-z]?\][^\n]*\[Fuente:[^\]]+\]", re.IGNORECASE),
    re.compile(r"^\s*\[Art\.\s*\d+[a-z]?\]\s*\[Fuente:[^\]]+\]", re.IGNORECASE),
    re.compile(r"^\s*\[Fuente:[^\]]+\][^\n]*", re.IGNORECASE),
    # Leak del nombre de la pista
    re.compile(r"^\s*Pista\s+de\s+formato\s*:[^\n]*", re.IGNORECASE),
    re.compile(r"^\s*MODO\s+(?:ESPECIFICO|LISTA)\s*:[^\n]*", re.IGNORECASE),
)


_BRACKET_RE = re.compile(r"\[[^\]]+\]")


def _is_mostly_brackets(text: str, ratio: float = 0.40) -> bool:
    """True si mas del `ratio` del texto son brackets de cita/header."""
    if not text or len(text) < 30:
        return False
    bracket_chars = sum(len(m.group(0)) for m in _BRACKET_RE.finditer(text))
    return (bracket_chars / len(text)) > ratio


def _truncate_at_leak(text: str) -> str:
    """Corta la respuesta cuando el SLM empieza a echar headers o instrucciones.

    Util porque qwen2.5:1.5b suele:
      - Continuar generando despues de su respuesta legitima, copiando el
        header del fragmento (`[Art. N] [Fuente: ...]`) o repitiendo la
        enumeracion -> patrones _LEAK_PATTERNS (requieren \\n previo).
      - Empezar la respuesta directamente listando headers de chunks
        (`1) [Art. 2] [Fuente: ...]`) -> patrones _LEAK_PATTERNS_AT_START
        (matchean en posicion 0).

    Si despues de strippear los leaks el texto restante es mayormente
    brackets (sin contenido sintetizado), devolvemos "" para que el caller
    sirva _NO_INFO en lugar de basura.
    """
    if not text:
        return text
    # Si la respuesta ES 'No encontre informacion...' entera, no la trunques.
    low = text.lower().lstrip()
    if low.startswith("no encontre informacion"):
        return text

    # PASO 1: Strippear leaks que aparecen AL INICIO de la respuesta.
    # Iterativamente porque suelen venir encadenados ("1) [...] 2) [...]").
    stripped = text.lstrip()
    while stripped:
        matched = False
        for pat in _LEAK_PATTERNS_AT_START:
            m = pat.match(stripped)
            if m:
                stripped = stripped[m.end():].lstrip()
                matched = True
                break
        if not matched:
            break
    text = stripped

    # PASO 2: Truncar en el primer leak interno (despues del char 60).
    if text:
        earliest = len(text)
        search_start = min(60, len(text))
        for pat in _LEAK_PATTERNS:
            m = pat.search(text, pos=search_start)
            if m and m.start() < earliest:
                earliest = m.start()
        text = text[:earliest].rstrip()

    # PASO 3: Si lo que queda es mayormente brackets, descartar.
    if _is_mostly_brackets(text):
        return ""
    return text


_NO_INFO = (
    "No encontre documentacion especifica de Uninorte sobre este tema. "
    "Para orientacion, te recomendamos consultar directamente con Bienestar Universitario "
    "o la dependencia correspondiente de la Universidad del Norte."
)

_STOPWORDS_ES = {
    "que", "cual", "cuales", "como", "donde", "cuando", "quien", "quienes",
    "cuanto", "cuanta", "cuantos", "cuantas",
    "el", "la", "los", "las", "un", "una", "unos", "unas", "del", "por",
    "para", "con", "sin", "sobre", "entre", "hasta", "desde", "hay",
    "tiene", "tienen", "tienes", "ser", "estar", "pasa", "sirve", "dice",
    "esta", "esto", "estos", "estas", "segun", "cada", "todo", "toda",
    "establece", "define", "menciona", "explica", "debo", "puedo",
    "exactamente", "aproximadamente", "solamente", "unicamente", "exacto",
    "concretamente", "especificamente", "precisamente",
    "hablame", "cuentame", "dime", "quiero", "busco", "consigo",
    "obtengo", "necesitas", "podrias",
}

_OMNIPRESENT = {
    "normativa", "reglamento", "universidad", "uninorte",
    "conforme", "mediante", "disposicion", "articulo",
}

_ATTENDANCE_KEYWORDS = {
    "falto", "faltar", "falte", "faltas", "fallar",
    "clase", "clases", "asignatura",
    "asistencia", "asistir", "asisto", "asisti",
    "inasistencia", "inasistencias",
    "ausencia", "ausencias", "ausentar", "ausento", "ausenta", "ausente",
    "perder", "pierdo", "pierde",
}

# Marcadores tipicos de pregunta de seguimiento (anafora explicita o implicita
# por brevedad). Usamos esto para decidir si concatenamos el turno anterior al
# query de retrieval.
_FOLLOWUP_STARTERS_RC = (
    "para que", "para qué", "y que", "y qué", "y cual", "y cuál",
    "como es", "cómo es", "como funciona", "cómo funciona",
    "que es", "qué es", "que hace", "qué hace", "que sirve", "qué sirve",
    "cual es la funcion", "cuál es la función", "cual es la función",
    "cuáles son las funciones", "cuales son las funciones",
    "cuando aplica", "cuándo aplica", "cuanto cuesta", "cuánto cuesta",
    "tambien", "también", "ademas", "además",
    "explicame", "explícame", "dime mas", "dime más",
    "como puedo", "cómo puedo", "como obtengo", "cómo obtengo",
    "donde", "dónde",
)

_ANAPHORA_RC = {
    "ese", "esa", "esos", "esas", "eso", "este", "esta", "estos", "estas",
    "dicho", "dicha", "dichos", "dichas", "mismo", "misma",
}

# Entidades normativas: si la pregunta menciona una, es auto-contenida y no
# necesita pegarle el turno anterior. Esto evita contaminar 'cuales son los
# derechos de los estudiantes' con el contexto previo 'carnet de egresados'.
_MAIN_ENTITIES_RC = (
    "estudiante", "egresad", "profesor", "docente", "alumno",
    "asignatura", "matricula", "matrícula",
    "trabajador", "empleado", "personal directivo", "directivo",
)


def _has_main_entity(question: str) -> bool:
    q = question.lower()
    return any(e in q for e in _MAIN_ENTITIES_RC)


def _is_short_followup(question: str, history: Optional[List[Dict[str, str]]] = None) -> bool:
    """True si la pregunta luce como seguimiento que necesita contexto previo.

    Reglas:
      - Si la pregunta menciona una entidad principal (estudiante/egresado/etc.)
        es auto-contenida -> NO followup, aunque sea corta.
      - <= 5 palabras sin entidad -> followup.
      - Contiene marcador de seguimiento ('para que sirve', 'que es...') en
        cualquier parte -> followup si no tiene entidad.
      - Primeras palabras tienen demostrativo (ese/esta/dicho) -> followup.
    """
    q = question.strip().lower()
    if not q:
        return False
    if _has_main_entity(q):
        return False
    words = q.split()
    if len(words) <= 5:
        return True
    if any(s in q for s in _FOLLOWUP_STARTERS_RC):
        return True
    head_terms = set(words[:3])
    return bool(head_terms & _ANAPHORA_RC)

_ATTENDANCE_DEFAULT_SESSIONS = 48
_ATTENDANCE_THRESHOLD_PCT = 0.25
_ATTENDANCE_LANG_THRESHOLD_PCT = 0.20

_NUMBER_WORDS_ES = {
    "una": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20,
}

_ATTENDANCE_RULE_NOTE = (
    "[REGLA EXACTA Art. 70 Reglamento Estudiantil - usa esto para responder]: "
    "La sancion de 0.0 solo aplica cuando las faltas EXCEDAN el 25% del total de clases del periodo. "
    "En un semestre tipico de pregrado (~48 sesiones), eso equivale a MAS DE 12 clases. "
    "Para lenguas extranjeras el umbral es el 20% (Art. 73).\n"
)


def _is_attendance_question(question: str) -> bool:
    words = set(re.findall(r"\b[a-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00fc\u00f1]+\b", question.lower()))
    return len(words & _ATTENDANCE_KEYWORDS) >= 2


def _is_language_question(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in ("lengua", "idioma", "ingles", "frances", "aleman", "portugues", "mandarin"))


def _extract_absence_count(question: str) -> Optional[int]:
    """Extrae el numero de clases/faltas mencionado en la pregunta, o None."""
    q = question.lower()
    m = re.search(r"\b(\d{1,3})\b", q)
    if m:
        n = int(m.group(1))
        if 0 < n < 200:
            return n
    for word, val in _NUMBER_WORDS_ES.items():
        if re.search(rf"\b{re.escape(word)}\b", q):
            return val
    return None


def _deterministic_attendance_answer(question: str) -> Optional[str]:
    """Respuesta determinista para preguntas de asistencia."""
    if not _is_attendance_question(question):
        return None
    q_lower = question.lower()
    is_lang = _is_language_question(question)
    pct = _ATTENDANCE_LANG_THRESHOLD_PCT if is_lang else _ATTENDANCE_THRESHOLD_PCT
    threshold_int = int(_ATTENDANCE_DEFAULT_SESSIONS * pct)
    article = "Art. 73" if is_lang else "Art. 70"
    pct_label = f"{int(pct * 100)}%"

    n = _extract_absence_count(question)

    if n is None:
        asking_threshold = any(
            w in q_lower
            for w in ("cuantas", "cu\u00e1ntas", "cuantos", "maximo", "m\u00e1ximo",
                      "limite", "l\u00edmite", "permitido", "permitidas", "necesito")
        )
        if not asking_threshold:
            return None
        return (
            f"Segun el {article} del Reglamento Estudiantil de Uninorte, las faltas de asistencia deben "
            f"EXCEDER el {pct_label} del total de clases programadas en el periodo para perder el derecho "
            f"al examen final con calificacion 0.0. En un semestre tipico de pregrado con "
            f"{_ATTENDANCE_DEFAULT_SESSIONS} sesiones, eso equivale a mas de {threshold_int} clases. "
            f"El numero exacto depende del total de sesiones de tu asignatura segun el silabo."
        )

    if n > threshold_int:
        return (
            f"Con {n} faltas en un semestre tipico de {_ATTENDANCE_DEFAULT_SESSIONS} sesiones "
            f"SI superas el umbral del {pct_label} ({article} del Reglamento Estudiantil), "
            f"por lo que la asignatura se calificaria con 0.0 (cero punto cero). "
            f"El umbral exacto depende del numero total de sesiones programadas en tu asignatura."
        )
    return (
        f"Con {n} faltas en un semestre tipico de {_ATTENDANCE_DEFAULT_SESSIONS} sesiones "
        f"NO superas el umbral del {pct_label} ({article} del Reglamento Estudiantil), "
        f"que equivale a mas de {threshold_int} inasistencias. "
        f"Con {n} faltas no perderas el derecho al examen final por inasistencia, "
        f"aunque el umbral exacto depende del total de sesiones de tu asignatura."
    )


def _key_terms(question: str) -> set:
    """Extrae terminos discriminadores de la pregunta."""
    words = re.findall(r"\b[a-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00fc\u00f1]+\b", question.lower())
    return {
        w for w in words
        if len(w) >= 5
        and w not in _STOPWORDS_ES
        and w not in _OMNIPRESENT
    }


def _token_in_text(term: str, text: str) -> bool:
    """Busqueda con tolerancia a plurales/genero comunes del espanol."""
    pattern = r"\b" + re.escape(term) + r"(s|es|a|as|os|ados|idas|idos)?\b"
    return bool(re.search(pattern, text))


def _context_covers(
    question: str,
    docs: list,
    threshold: float = 0.35,
    rewritten_query: str = "",
) -> bool:
    """Verifica que al menos el `threshold` (35%) de los terminos clave aparezcan en chunks."""
    terms = _key_terms(question)
    if rewritten_query:
        terms = terms | _key_terms(rewritten_query)

    if len(terms) == 0:
        return len(question.strip().split()) > 3
    context_text = " ".join(doc.page_content.lower() for doc in docs)
    matched = sum(1 for t in terms if _token_in_text(t, context_text))
    return (matched / len(terms)) >= threshold


_NON_NORMATIVE_KW = ("informe", "sostenibilidad", "sustainability", "memoria")

_ACRONYM_RE = re.compile(r"\b[A-Z\u00c1\u00c9\u00cd\u00d3\u00da]{3,}\b")
_ALLOWED_ACRONYMS = {"UNINORTE", "PDF", "DNI", "NRC", "TIC", "GPS", "URL", "API", "ID"}


def _validate_no_invented_acronyms(answer: str, docs: List[Document]) -> str:
    """Elimina acronimos inventados que no aparecen en los chunks fuente."""
    corpus = " ".join(d.page_content for d in docs)
    found = set(_ACRONYM_RE.findall(answer)) - _ALLOWED_ACRONYMS
    invented = [a for a in found if a not in corpus]
    if not invented:
        return answer
    for a in invented:
        answer = re.sub(rf"\b{re.escape(a)}\b", "[termino no verificado]", answer)
    return answer


# Matcher para citas validas: [Art. N], [Art N], [Fuente: xxx]
_CITATION_RE = re.compile(
    r"\[(?:art[\u00ed\u00ed\u00edi]culo|art\.?)\s*\d+[a-z]?\]|\[fuente:[^\]]+\]",
    re.IGNORECASE,
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\\!\?])\s+(?=[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00bf\u00a1])")


def _enforce_citations(answer: str, docs: List[Document]) -> str:
    """Garantiza cita al final si la respuesta es una sola oracion; NO descarta
    oraciones sin cita en respuestas largas.

    Historico: el comportamiento anterior eliminaba toda oracion sin
    [Art. N]/[Fuente: ...], lo cual mutilaba respuestas de SLMs pequenos
    (qwen2.5:1.5b) que olvidan citar parte de sus oraciones, especialmente
    cuando los chunks no traen metadata.article (caso del Reglamento de
    Egresados antes del fix de ordinales). Ahora:
      - Si la respuesta empieza con 'No encontre...': devolver tal cual.
      - Si es una sola oracion sin cita: anexar la cita del primer doc.
      - Si tiene varias oraciones: devolver la respuesta integra. La calidad
        de citas se evalua en el benchmark (faithfulness), no se impone
        destructivamente en runtime.
    """
    if not docs or not answer.strip():
        return answer

    low = answer.lower().strip()
    if low.startswith(("no encontre", "no encontr\u00e9", "no hay informacion")):
        return answer

    sentences = _SENTENCE_SPLIT_RE.split(answer.strip())
    if len(sentences) <= 1:
        if _CITATION_RE.search(answer):
            return answer
        first = docs[0].metadata
        if first.get("article"):
            return f"{answer.rstrip('.').rstrip()} [Art. {first['article']}]."
        elif first.get("source"):
            return f"{answer.rstrip('.').rstrip()} [Fuente: {first['source']}]."
        return answer

    # Multi-oracion: conservar respuesta integra (no destructivo).
    return answer


# Query Rewriting - validacion del output del rewriter
_REWRITE_MAX_CHARS = 150

_REWRITE_BAD_PREFIXES = (
    "no ", "lo siento", "disculpa", "lo que pregunta",
    "la pregunta", "respuesta:", "segun ", "seg\u00fan ",
    "como asistente", "no puedo", "estimado", "hola",
)


def _is_bad_rewrite(rewritten: str, original: str) -> bool:
    cleaned = rewritten.strip()
    if not cleaned or len(cleaned) < 4:
        return True
    if len(cleaned) > _REWRITE_MAX_CHARS:
        return True
    low = cleaned.lower()
    return any(low.startswith(p) for p in _REWRITE_BAD_PREFIXES)


sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    OLLAMA_BASE_URL,
    DEFAULT_SLM_MODEL,
    REWRITE_SLM_MODEL,
    TEMPERATURE,
    MAX_TOKENS,
    OLLAMA_KEEP_ALIVE,
    RERANKER_ENABLED,
    RERANKER_TOP_N,
)
from src.prompt_templates import (
    SYSTEM_PROMPT_ES,
    RAG_PROMPT_TEMPLATE,
    QUERY_REWRITE_PROMPT,
    format_context_from_docs,
)
from src.reranker import get_reranker, rerank_documents


def create_llm(
    model_name: str = DEFAULT_SLM_MODEL,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> Ollama:
    """LLM principal para generar la respuesta final al usuario.

    keep_alive mantiene el modelo cargado en memoria de Ollama tras inactividad,
    eliminando el cold-start de 5-15s que sufre el primer query tras pausa larga.

    top_p=0.9 / top_k=40 (relajados desde 0.3 / 20): con temperature=0 son
    irrelevantes para el determinismo, pero valores bajos en algunos backends
    de Ollama recortaban tokens correctos cuando la distribucion era amplia
    (e.g. el modelo equivocaba la enumeracion correcta por una abreviada).
    repeat_penalty=1.1 (bajado desde 1.2): el 1.2 penalizaba listas tipo "a. b.
    c. d. ..." porque comparte tokens entre items y truncaba antes del final.
    """
    return Ollama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        top_p=0.9,
        top_k=40,
        num_predict=max_tokens,
        system=SYSTEM_PROMPT_ES,
        repeat_penalty=1.1,
        keep_alive=OLLAMA_KEEP_ALIVE,
    )


def create_rewrite_llm(model_name: str = REWRITE_SLM_MODEL) -> Ollama:
    """LLM dedicado a Query Rewriting, mas pequeno que el principal."""
    return Ollama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=0.0,
        num_predict=35,
        repeat_penalty=1.0,
        keep_alive=OLLAMA_KEEP_ALIVE,
    )


class RAGChain:
    """Cadena RAG que encapsula retriever + prompt + LLM con soporte de historial."""

    def __init__(
        self,
        retriever,
        llm,
        prompt: PromptTemplate,
        rewrite_llm: Optional[Ollama] = None,
    ):
        self.retriever = retriever
        self.llm = llm
        self.prompt = prompt
        self.rewrite_llm = rewrite_llm

    @staticmethod
    def _format_docs(docs: List[Document]) -> str:
        return format_context_from_docs(docs)

    @staticmethod
    def _is_toc_or_preamble(doc: Document) -> bool:
        """Detecta chunks de tabla de contenido o preambulo (sin numero de
        articulo/seccion, mayormente headings cortos en mayusculas).

        Estos fragmentos confunden al SLM porque mencionan 'DEBERES', 'DERECHOS'
        en forma de TOC y el modelo cree que responden la pregunta cuando solo
        son indice. Los excluimos cuando hay otros chunks con metadata real.
        """
        if doc.metadata.get("article"):
            return False
        content = doc.page_content
        if "TABLA DE CONTENIDO" in content[:200].upper():
            return True
        # Heuristica: muchas lineas cortas en mayusculas y pocas oraciones.
        lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
        if len(lines) < 8:
            return False
        upper_short = sum(1 for ln in lines if ln.upper() == ln and 3 < len(ln) < 60)
        return upper_short >= max(5, len(lines) // 3)

    @staticmethod
    def _filter_and_dedup(docs: List[Document], seen: set, question: str = "") -> List[Document]:
        result = []
        q_lower = question.lower()
        is_student_query = "estudiant" in q_lower
        is_alumni_query = "egresad" in q_lower

        # Si hay chunks con article metadata, descartamos los TOC sin articulo.
        any_with_article = any(d.metadata.get("article") for d in docs)

        for doc in docs:
            title = doc.metadata.get("title", "").lower()
            source = doc.metadata.get("source", "").lower()

            if any(kw in title or kw in source for kw in _NON_NORMATIVE_KW):
                continue

            if any_with_article and RAGChain._is_toc_or_preamble(doc):
                continue

            is_alumni_doc = "egresado" in title or "egresado" in source
            is_student_doc = "estudiant" in title or "estudiant" in source

            if is_student_query and not is_alumni_query and is_alumni_doc:
                continue
            if is_alumni_query and not is_student_query and is_student_doc:
                continue

            fingerprint = doc.page_content[:120].strip()
            if fingerprint not in seen:
                seen.add(fingerprint)
                result.append(doc)
        return result

    def _keyword_search_fallback(self, terms: set, n: int = 3) -> List[Document]:
        """Busqueda literal por keyword en ChromaDB cuando el vector search falla."""
        try:
            collection = self.retriever.vectorstore._collection
            for term in sorted(terms, key=len, reverse=True):
                if len(term) < 4:
                    continue
                result = collection.get(
                    where_document={"$contains": term},
                    include=["documents", "metadatas"],
                    limit=n,
                )
                raw_docs = result.get("documents") or []
                raw_metas = result.get("metadatas") or []
                if raw_docs:
                    return [
                        Document(page_content=text, metadata=meta or {})
                        for text, meta in zip(raw_docs, raw_metas)
                    ]
        except Exception:
            pass
        return []

    def _rewrite_query_for_retrieval(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]],
    ) -> str:
        """Traduce pregunta coloquial a terminos normativos via LLM rewriter."""
        terms = _key_terms(question)
        fallback = " ".join(terms) if terms else question

        if self.rewrite_llm is None:
            return fallback

        context_hint = ""
        if history:
            # Solo enriquecer con contexto previo si la pregunta luce como
            # seguimiento (carece de entidad propia). Si la pregunta ya menciona
            # 'estudiantes' u otra entidad, es auto-contenida y agregar
            # contexto cruzado degrada la query (ej. mezclar carnet/egresados
            # con derechos/estudiantes).
            if _is_short_followup(question, history):
                user_turns = [
                    m["content"].strip()
                    for m in history
                    if m.get("role") == "user" and m.get("content", "").strip()
                ]
                anchor = ""
                for prev in reversed(user_turns):
                    if _has_main_entity(prev):
                        anchor = prev
                        break
                if not anchor and user_turns:
                    anchor = user_turns[-1]
                if anchor:
                    context_hint = f"Contexto del turno anterior: {anchor}\n"

        prompt_text = QUERY_REWRITE_PROMPT.format(
            question=question,
            context_hint=context_hint,
        )

        try:
            raw = self.rewrite_llm.invoke(prompt_text)
            rewritten = raw.content if hasattr(raw, "content") else str(raw)
            rewritten = rewritten.strip()

            low_r = rewritten.lower()
            for marker in ("frase:", "consulta:", "busqueda:", "> "):
                if marker in low_r:
                    idx = low_r.rfind(marker)
                    after = rewritten[idx + len(marker):]
                    extracted = after.strip().strip("'\"").split("\n")[0].strip().strip("'\"").strip()
                    if extracted and 4 <= len(extracted) <= _REWRITE_MAX_CHARS:
                        rewritten = extracted
                        break

            rewritten = rewritten.strip().strip('"').strip("'").strip()

            if _is_bad_rewrite(rewritten, question):
                _logger.debug(
                    "Rewrite descartado - invalido: %r | fallback: %r",
                    rewritten, fallback,
                )
                return fallback

            _logger.debug("Rewrite OK: %r -> %r", question, rewritten)
            return rewritten

        except Exception as exc:
            _logger.warning("Rewrite fallo (%s): fallback '%s'.", exc, fallback)
            return fallback

    def invoke(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta la cadena RAG (sin streaming) y retorna respuesta + docs fuente."""
        det = _deterministic_attendance_answer(question)
        if det is not None:
            _, source_docs, _ = self._prepare(question, history)
            return {"answer": det, "source_documents": source_docs}

        prompt_text, source_docs, _ = self._prepare(question, history)
        if not source_docs:
            return {"answer": _NO_INFO, "source_documents": []}
        raw_answer = self.llm.invoke(prompt_text)
        answer = raw_answer.content if hasattr(raw_answer, "content") else str(raw_answer)
        answer = _truncate_at_leak(answer)
        # Si el filtro vacio la respuesta (era leak puro), devolver _NO_INFO
        # en vez de string vacio. Mejor "no se" honesto que basura.
        if not answer.strip():
            return {"answer": _NO_INFO, "source_documents": []}
        answer = _dedup_answer(answer)
        answer = _validate_no_invented_acronyms(answer, source_docs)
        answer = _enforce_citations(answer, source_docs)
        return {"answer": answer, "source_documents": source_docs}

    def _prepare(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]],
    ):
        """Nucleo del pipeline RAG.

        Flujo:
          PASO 1 - Query Rewriting (a frase normativa formal)
          PASO 2 - Retrieval MULTI-QUERY (original + rewritten -> union dedup)
                   Asegura que si el rewriter degrada la query, la version
                   original todavia recupera el chunk correcto.
          PASO 3 - Cobertura de terminos
          PASO 4 - Fallback keyword si no cubre
          PASO 4.5 - Rerank cross-encoder a RERANKER_TOP_N
          PASO 5 - Prompt final
        """
        if history is None:
            history = []

        retrieval_query = self._rewrite_query_for_retrieval(question, history)

        # Si la pregunta luce como seguimiento corto ("para que sirve el carnet?"),
        # concatenamos el ultimo turno del usuario para recuperar el contexto
        # tematico. Esto resuelve la perdida de coherencia conversacional que
        # vimos en el deploy con "el carnet" -> traer chunks de egresados.
        followup_query = ""
        if history and _is_short_followup(question, history):
            user_turns = [
                m["content"].strip() for m in history
                if m.get("role") == "user" and m.get("content", "").strip()
            ]
            # Buscar el ultimo turno previo que MENCIONA una entidad
            # (estudiante/egresado/etc.); ese es el contexto relevante. Si no
            # hay, usar el ultimo turno simple. Esto evita arrastrar contextos
            # cruzados cuando hay multiples cambios de tema en el historial.
            anchor = ""
            for prev in reversed(user_turns):
                if _has_main_entity(prev):
                    anchor = prev
                    break
            if not anchor and user_turns:
                anchor = user_turns[-1]
            if anchor:
                followup_query = f"{anchor} {question}".strip()
                _logger.debug("Followup -> query enriquecida: %r", followup_query)

        # Multi-query: recuperar con la pregunta original, con el rewrite, y
        # con la version enriquecida con historial si aplica. Union deduplicada.
        # El rewrite a veces sustituye palabras claves; el original ancla
        # semanticamente; el followup recupera el contexto del turno anterior.
        queries = [retrieval_query]
        if question != retrieval_query:
            queries.append(question)
        if followup_query and followup_query not in queries:
            queries.append(followup_query)

        merged: List[Document] = []
        seen_keys: set = set()
        for q in queries:
            for doc in self.retriever.invoke(q):
                key = doc.page_content[:120].strip()
                if key not in seen_keys:
                    seen_keys.add(key)
                    merged.append(doc)

        seen_fingerprints: set = set()
        unique_docs = self._filter_and_dedup(merged, seen_fingerprints, question)

        terms = _key_terms(question)
        needs_fallback = (
            (unique_docs and not _context_covers(
                question, unique_docs, rewritten_query=retrieval_query
            ))
            or (not unique_docs and bool(terms))
        )
        if needs_fallback:
            fallback_docs = self._keyword_search_fallback(terms)
            unique_docs = self._filter_and_dedup(fallback_docs, seen_fingerprints, question)

        # PASO 4.5: rerank cross-encoder.
        # Reordena por relevancia real (query, chunk) y recorta a TOP_N, lo que
        # compacta el prompt final ~50% y acelera la generacion del SLM.
        # Si el reranker esta deshabilitado (CPU ARM no lo soporta sin penalizar
        # latencia), recortamos igual a TOP_N confiando en el orden por
        # similitud coseno del vector store. Esto evita inundar el prompt con
        # chunks de baja relevancia que disparan alucinaciones.
        if RERANKER_ENABLED and unique_docs:
            unique_docs = rerank_documents(
                question, unique_docs, top_n=RERANKER_TOP_N
            )
        elif unique_docs:
            unique_docs = unique_docs[:RERANKER_TOP_N]

        context = self._format_docs(unique_docs)
        attendance_note = _ATTENDANCE_RULE_NOTE if _is_attendance_question(question) else ""

        # Decidir si esta es una pregunta de tipo "lista" (pide enumeracion
        # completa) o "especifica" (pide un dato puntual).
        # Pista de lista: solo si la pregunta menciona el tipo (derechos/deberes)
        # Y usa formulacion enumerativa ('cuales son', 'lista', 'todos los',
        # 'enumera') o pide directamente la lista ('dime los').
        q_lower = question.lower()
        is_list_query = (
            any(kw in q_lower for kw in (
                "cuales son", "cuáles son", "lista de", "todos los",
                "todas las", "enumera", "enumere", "enumerar",
                "dime los", "dame los", "dime las", "dame las",
                "dime todos", "dame todos", "menciona los", "menciona las",
            ))
            or q_lower.strip().startswith(("son derechos", "son deberes"))
        )
        is_specific_query = any(kw in q_lower for kw in (
            "para que sirve", "para qué sirve", "que sirve", "qué sirve",
            "que es", "qué es", "que hace", "qué hace",
            "como funciona", "cómo funciona", "como es", "cómo es",
            "funcion", "función", "uso de",
        ))

        rights_note = ""
        if not is_specific_query:
            if "derecho" in q_lower and "deber" not in q_lower and "obligacion" not in q_lower:
                rights_note = (
                    "Pista: busca el fragmento que empiece con 'Son derechos' o "
                    "'ARTICULO ... Son derechos'. Ignora fragmentos que enumeren "
                    "'acatar/cumplir/respetar' (esos son deberes).\n\n"
                )
            elif "deber" in q_lower and "derecho" not in q_lower:
                rights_note = (
                    "Pista: busca el fragmento que empiece con 'Son deberes' o "
                    "'ARTICULO ... Son deberes'. Ignora fragmentos que empiecen "
                    "con 'Son derechos'.\n\n"
                )

        # Pista de modo (lista vs especifico). El SLM responde mejor cuando
        # sabe que extension de respuesta dar. NOTA: se quito el ejemplo
        # detallado de "MODO ESPECIFICO" porque qwen2.5:1.5b lo copiaba
        # textualmente a la respuesta (leak de instrucciones). La regla 2 del
        # RAG_PROMPT_TEMPLATE ya cubre el comportamiento esperado; estas notas
        # son solo un refuerzo corto.
        if is_specific_query:
            rights_note += (
                "Pista de formato: respuesta breve (1-2 oraciones), enfocada "
                "solo en lo que responde la pregunta puntual; no enumeres la lista.\n\n"
            )
        elif is_list_query:
            rights_note += (
                "Pista de formato: la pregunta pide una lista. Copia textualmente "
                "todos los items (a-z o 1-N) del fragmento relevante, en orden, "
                "sin saltar ninguno y sin parafrasear.\n\n"
            )

        prompt_text = self.prompt.format(
            context=context,
            question=question,
            attendance_note=attendance_note,
            rights_note=rights_note,
        )

        seen_sources: set = set()
        sources_info = []
        for doc in unique_docs:
            meta = doc.metadata
            key = (meta.get("source", ""), str(meta.get("page", "")))
            if key not in seen_sources:
                seen_sources.add(key)
                sources_info.append({
                    "source": meta.get("source", ""),
                    "title": meta.get("title", ""),
                    "page": str(meta.get("page", "")),
                })

        return prompt_text, unique_docs, sources_info

    def invoke_stream(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
    ):
        """Ejecuta la cadena RAG con streaming de tokens."""
        det = _deterministic_attendance_answer(question)
        if det is not None:
            _, source_docs, sources_info = self._prepare(question, history)
            def _det_gen():
                yield det
            return sources_info, source_docs, _det_gen()

        prompt_text, source_docs, sources_info = self._prepare(question, history)
        if not source_docs:
            def _no_info_gen():
                yield _NO_INFO
            return [], [], _no_info_gen()
        return sources_info, source_docs, self.llm.stream(prompt_text)


def create_rag_chain(
    retriever,
    model_name: str = DEFAULT_SLM_MODEL,
    temperature: float = TEMPERATURE,
) -> RAGChain:
    """Construye la cadena RAG completa.

    - llm:         LLM principal (modelo seleccionado por usuario)
    - rewrite_llm: LLM mini rewriter (REWRITE_SLM_MODEL, mas pequeno)
    - prompt:      Template con XML isolation de historial y fragmentos
    """
    llm = create_llm(model_name, temperature)
    rewrite_llm = create_rewrite_llm(model_name)

    # Precarga el reranker ahora para que el primer query no pague la descarga
    # (~568MB BAAI/bge-reranker-v2-m3) ni el cold-start del CrossEncoder.
    get_reranker()

    prompt = PromptTemplate(
        template=RAG_PROMPT_TEMPLATE,
        input_variables=["context", "question", "attendance_note", "rights_note"],
    )

    return RAGChain(retriever, llm, prompt, rewrite_llm)


def query_rag(
    chain: RAGChain,
    question: str,
    model_name: str = "",
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Ejecuta una consulta RAG y retorna el resultado estructurado."""
    result = chain.invoke(question, history=history)
    source_docs = result.get("source_documents", [])
    sources_info = []
    for doc in source_docs:
        meta = doc.metadata
        sources_info.append({
            "source": meta.get("source", ""),
            "title": meta.get("title", ""),
            "page": meta.get("page", ""),
        })
    return {
        "answer": result.get("answer", "Sin respuesta"),
        "source_documents": source_docs,
        "sources_info": sources_info,
        "model": model_name,
    }


def format_response_with_sources(result: Dict[str, Any]) -> str:
    """Formatea la respuesta con citas de fuentes."""
    answer = result["answer"]
    sources = result.get("sources_info", [])
    if not sources:
        return answer
    seen = set()
    unique_sources = []
    for s in sources:
        key = (s["source"], s["page"])
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)
    sources_text = "\n\n---\n**Fuentes consultadas:**\n"
    for s in unique_sources:
        title = s.get("title", s["source"])
        page = s.get("page", "?")
        sources_text += f"- {title} (pag. {page})\n"
    return answer + sources_text
