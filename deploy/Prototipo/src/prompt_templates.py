"""Plantillas de prompts para el sistema RAG, en espanol."""

SYSTEM_PROMPT_ES = (
    "Eres UNINORMA, asistente normativo de la Universidad del Norte (Uninorte). "
    "Respondes en espanol formal, usando UNICAMENTE los fragmentos que te entrega cada consulta. "
    "Nunca usas portugues, ingles ni otro idioma."
)

RAG_PROMPT_TEMPLATE = """Tarea: responder la pregunta de un usuario sobre la normatividad de Uninorte usando UNICAMENTE los fragmentos provistos.

PREGUNTA del usuario: {question}

Fragmentos normativos recuperados:
{context}
{attendance_note}{rights_note}
Como debes responder:
1. Identifica el unico fragmento que responde la PREGUNTA. Casi siempre es el que empieza con "Son derechos de los..." o "Son deberes de los..." o "Artículo N. Son derechos/deberes..." y cuyo destinatario (estudiantes/egresados/profesores) coincide con la pregunta.
2. Copia TEXTUAL los items de la enumeracion (a, b, c... o 1, 2, 3...) hasta el ultimo. No inventes items. No parafrasees. No resumas.
3. Si ningun fragmento responde la pregunta, di EXACTAMENTE: "No encontre informacion sobre este tema en los documentos disponibles." (sin nada antes ni despues).
4. Cierra cada afirmacion normativa con [Art. N] tomado del header del fragmento, o [Fuente: nombre_archivo].
5. No mezcles fragmentos de temas distintos. No agregues advertencias al final.
6. Responde en espanol formal. Nunca cambies a portugues u otro idioma.

Tu respuesta a la PREGUNTA:"""

# ---------------------------------------------------------------------------
# Prompt para reescritura de queries (Query Rewriting / Lexical Gap closure)
# ---------------------------------------------------------------------------
QUERY_REWRITE_PROMPT = (
    "Eres un traductor de consultas para busqueda en reglamentos universitarios. "
    "Convierte la pregunta coloquial en una frase de busqueda con terminos normativos formales. "
    "Corrige errores ortograficos (ej. 'acitvos' -> 'activos') antes de reformular. "
    "Manten en PLURAL los sustantivos de personas ('estudiantes', 'egresados', 'profesores'); los "
    "reglamentos los enumeran en plural. "
    "Manten si la pregunta habla de 'estudiantes' o 'egresados', y si pide 'derechos' o 'deberes'. "
    "Solo sustantivos formales. Sin verbos. Maximo 10 palabras.\n\n"
    "Ejemplos:\n"
    "Pregunta: 'que pasa si rompo o dano algo de la universidad'\n"
    "Frase: 'sancion disciplinaria dano deterioro bienes materiales institucion'\n\n"
    "Pregunta: 'me pueden echar si voy muy mal en notas'\n"
    "Frase: 'cancelacion matricula bajo rendimiento academico consecuencias'\n\n"
    "Pregunta: 'cuales son los derechos de los estudiantes acitvos'\n"
    "Frase: 'derechos estudiantes activos regulares prerrogativas'\n\n"
    "Pregunta: 'dime los 10 derechos de los egresados'\n"
    "Frase: 'derechos egresados Uninorte carnet servicios'\n\n"
    "Pregunta: 'cuales son los deberes de los egresados'\n"
    "Frase: 'deberes egresados obligaciones Uninorte'\n\n"
    "{context_hint}"
    "Pregunta: '{question}'\n"
    "Frase:"
)


def format_context_from_docs(docs: list) -> str:
    """Formatea documentos recuperados con etiquetas de fuente y articulo."""
    context_parts = []
    for i, doc in enumerate(docs):
        metadata = doc.metadata
        source = metadata.get("source", "Desconocido")
        page = metadata.get("page", "?")
        title = metadata.get("title", "")
        article = metadata.get("article")

        if title:
            header = f"[Fuente: {title} ({source}) | Pagina: {page}]"
        else:
            header = f"[Fuente: {source} | Pagina: {page}]"

        if article:
            header = f"[Art. {article}] " + header

        context_parts.append(f"{header}\n{doc.page_content}")

    return "\n\n".join(context_parts)


_NO_INFO_MARKERS = ("no encontre informacion", "no encontré información",
                    "no encontre documentacion", "no encontré documentación")

_MAX_ASSISTANT_CHARS = 150


def _is_no_info(content: str) -> bool:
    low = content.lower()[:100]
    return any(m in low for m in _NO_INFO_MARKERS)


def _next_is_no_info(history: list, i: int) -> bool:
    if i + 1 >= len(history):
        return False
    nxt = history[i + 1]
    return nxt.get("role") == "assistant" and _is_no_info(nxt.get("content", ""))


def _format_user(history: list, i: int) -> tuple:
    content = history[i].get("content", "").strip()
    if not content:
        return None, 1
    if _next_is_no_info(history, i):
        return None, 2
    return f"Pregunta previa: {content}", 1


def _format_assistant(msg: dict):
    content = msg.get("content", "").strip()
    if not content or _is_no_info(content):
        return None
    snippet = content[:_MAX_ASSISTANT_CHARS]
    if len(content) > _MAX_ASSISTANT_CHARS:
        snippet += "..."
    return f"Respuesta previa: {snippet}"


_STOPWORDS_LOCAL = {
    "que", "cual", "cuales", "como", "donde", "cuando", "quien", "quienes",
    "cuanto", "cuanta", "el", "la", "los", "las", "un", "una", "del", "por",
    "para", "con", "sin", "sobre", "entre", "hay", "tiene", "ser", "estar",
    "esta", "esto", "segun", "cada", "todo", "toda", "establece", "define",
    "normativa", "reglamento", "universidad", "uninorte",
}


def _simple_key_terms(text: str) -> set:
    import re as _re
    words = _re.findall(r"\b[a-záéíóúüñ]+\b", text.lower())
    return {w for w in words if len(w) >= 5 and w not in _STOPWORDS_LOCAL}


def _topic_changed(current_question: str, history: list) -> bool:
    cur_terms = _simple_key_terms(current_question)
    if not cur_terms:
        return False
    prior_terms: set = set()
    for m in history:
        if m.get("role") == "user":
            prior_terms |= _simple_key_terms(m.get("content", ""))
    return not (cur_terms & prior_terms)


def _collect_history_lines(history: list) -> list:
    lines = []
    i = 0
    while i < len(history):
        role = history[i].get("role", "")
        if role == "user":
            line, step = _format_user(history, i)
        else:
            line, step = _format_assistant(history[i]), 1
        if line:
            lines.append(line)
        i += step
    return lines


def format_history_for_prompt(history: list, current_question: str = "") -> str:
    if not history:
        return ""
    if current_question and _topic_changed(current_question, history):
        return ""
    lines = _collect_history_lines(history)
    if not lines:
        return ""
    return "Contexto de la conversacion:\n" + "\n".join(lines) + "\n\n"


_FOLLOWUP_STARTERS = (
    "para que sirve", "y que", "y cual",
    "tambien", "ademas", "que mas",
    "como es", "cuando aplica", "cuanto",
    "y si", "pero", "entonces",
)

_ANAPHORA_WORDS = {
    "ese", "esa", "esos", "esas", "eso", "este", "esta", "estos", "estas",
    "dicho", "dicha", "dichos", "dichas", "mismo", "misma", "él", "ella",
    "ellos", "ellas", "su", "sus",
}


def _is_followup(question: str) -> bool:
    q = question.strip().lower()
    words = q.split()
    if len(words) <= 6:
        return True
    if any(q.startswith(s) for s in _FOLLOWUP_STARTERS):
        return True
    if any(w in _ANAPHORA_WORDS for w in words[:4]):
        return True
    return False


def build_retrieval_query(question: str, history: list) -> str:
    if not history or not _is_followup(question):
        return question
    user_turns = [
        m["content"].strip()
        for m in history
        if m.get("role") == "user" and m.get("content", "").strip()
    ]
    if user_turns:
        return user_turns[-1] + " " + question
    return question


def build_rag_prompt(context: str, question: str, history: str = "", attendance_note: str = "") -> str:
    return RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=question,
        history=history,
        attendance_note=attendance_note,
    )
