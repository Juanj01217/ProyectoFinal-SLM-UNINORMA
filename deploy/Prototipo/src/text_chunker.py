"""Division de documentos en chunks para embedding vectorial.

Estrategia jerarquica (nueva):
  1. Intentar detectar articulos ("Articulo N.", "Art. N.", "ARTICULO N") y usar
     cada articulo como unidad minima de chunk. Preserva la semantica legal:
     una respuesta que cita "Art. 70" no llega al LLM partida por la mitad.
  2. Si el articulo excede ARTICLE_MAX_CHARS, se subdivide con el splitter
     recursivo manteniendo overlap.
  3. Fallback: si no se detectan articulos en el texto (ej. bienestar, informes),
     se aplica el splitter recursivo clasico.
"""
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Agregar raiz del prototipo al path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SEPARATORS,
    ARTICLE_MAX_CHARS,
    ARTICLE_MIN_CHARS,
)


# Regex que detecta el inicio de un articulo. Cubre las variantes mas comunes
# en reglamentos colombianos:
#   - Digitos: "Articulo 12.", "ARTICULO 12.", "Art. 12."
#   - Ordinales en espanol: "ARTICULO PRIMERO", "Articulo Segundo", "Art. Decimo"
# Captura el identificador (numerico u ordinal) para normalizarlo a numero.
_ORDINAL_MAP = {
    "PRIMERO": "1", "SEGUNDO": "2", "TERCERO": "3", "CUARTO": "4",
    "QUINTO": "5", "SEXTO": "6", "SEPTIMO": "7", "SÉPTIMO": "7",
    "OCTAVO": "8", "NOVENO": "9", "DECIMO": "10", "DÉCIMO": "10",
    "UNDECIMO": "11", "UNDÉCIMO": "11", "ONCEAVO": "11",
    "DUODECIMO": "12", "DUODÉCIMO": "12", "DOCEAVO": "12",
    "DECIMOTERCERO": "13", "DECIMOTERCER": "13",
    "DECIMOCUARTO": "14", "DECIMOQUINTO": "15", "DECIMOSEXTO": "16",
    "DECIMOSEPTIMO": "17", "DECIMOSÉPTIMO": "17",
    "DECIMOCTAVO": "18", "DECIMONOVENO": "19", "VIGESIMO": "20", "VIGÉSIMO": "20",
}

_ORDINAL_PATTERN = "|".join(sorted(_ORDINAL_MAP.keys(), key=len, reverse=True))

_ARTICLE_RE = re.compile(
    r"(?im)^\s*(?:art[íi]culo|art\.)\s*"
    r"(?P<num>\d+|" + _ORDINAL_PATTERN + r")"
    r"[\.\-\s°º:,]",
)

# Detector de secciones numeradas tipo "7. Son deberes...", "8. Son derechos...",
# "9. La Universidad...". Usado en documentos cuyo cuerpo normativo se enumera
# con "N." (Reg_Estudiantes_Febrero_2025.pdf) en lugar de "ARTÍCULO N".
# Soporta dos formatos del PDF tras extraccion:
#   - "7. Son deberes" (numero + punto + espacio)
#   - "10.\nLa estudiante" (numero + punto + salto de linea)
# IMPORTANTE: solo lineas que empiezan con N. + palabra capitalizada de oracion
# (Son, La, El, Las, Los, Para, En, Cuando...). NO matchea sub-items "a. Ejercer"
# ni decimales tipo "1.5" porque exigimos palabra capitalizada despues.
_SECTION_RE = re.compile(
    r"(?m)^[ \t]*(?P<num>\d{1,3})\.[ \t\r\n]+"
    r"(?P<lead>[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)",
)


def _normalize_article_number(raw: str) -> str:
    """Convierte 'SEGUNDO' -> '2', 'Decimo' -> '10', '12' -> '12'."""
    upper = raw.upper().strip()
    return _ORDINAL_MAP.get(upper, upper)


def create_splitter(
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: List[str] = None,
) -> RecursiveCharacterTextSplitter:
    """Crea un text splitter configurado."""
    if separators is None:
        separators = SEPARATORS
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
    )


def _find_article_boundaries(text: str) -> List[Tuple[int, int, str]]:
    """Devuelve [(start, end, article_number)] con los limites de cada articulo."""
    matches = list(_ARTICLE_RE.finditer(text))
    if not matches:
        return []
    boundaries: List[Tuple[int, int, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        boundaries.append((start, end, _normalize_article_number(m.group("num"))))
    return boundaries


def _find_section_boundaries(text: str) -> List[Tuple[int, int, str]]:
    """Detecta secciones numeradas tipo 'N. Capitalized...' en el texto.

    Usado como fallback cuando el documento no expone 'ARTÍCULO N' pero su
    cuerpo normativo se enumera con 'N.' (caso Reg_Estudiantes_Febrero_2025).
    Acepta numeros crecientes y reinicios (e.g. capitulo II usa 1-14, capitulo
    III reinicia en 1). Filtra falsos positivos exigiendo que el segmento
    tenga al menos ARTICLE_MIN_CHARS y descarta numeros aislados de paginacion.
    """
    raw_matches = list(_SECTION_RE.finditer(text))
    if not raw_matches:
        return []
    # Heuristica anti-ruido: aceptar todos los matches con numero razonable.
    # La validacion final se hace en _chunk_by_boundaries via min_chars.
    matches = []
    for m in raw_matches:
        try:
            n = int(m.group("num"))
        except ValueError:
            continue
        if n <= 0 or n > 999:
            continue
        matches.append(m)
    if not matches:
        return []
    boundaries: List[Tuple[int, int, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        boundaries.append((start, end, m.group("num")))
    return boundaries


def _chunk_by_boundaries(
    text: str,
    boundaries: List[Tuple[int, int, str]],
    splitter: RecursiveCharacterTextSplitter,
    max_chars: int,
    min_chars: int,
    unit_label: str,
) -> List[Dict[str, Any]]:
    """Divide texto en chunks usando una lista de fronteras precomputadas.

    Cada elemento devuelto: {"text": str, "article": str | None, "start": int}
    El campo `start` es el offset en el texto original (para mapear a pagina).
    """
    chunks: List[Dict[str, Any]] = []
    preamble_end = boundaries[0][0]
    preamble = text[:preamble_end].strip()
    if len(preamble) >= min_chars:
        chunks.append({"text": preamble, "article": None, "start": 0})

    for start, end, num in boundaries:
        unit_text = text[start:end].strip()
        if len(unit_text) < min_chars:
            continue
        if len(unit_text) <= max_chars:
            chunks.append({"text": unit_text, "article": num, "start": start})
        else:
            # Unidad muy larga: subdividir manteniendo el numero.
            for sc in splitter.split_text(unit_text):
                chunks.append({"text": sc, "article": num, "start": start})
    return chunks


def _chunk_full_document(
    full_text: str,
    splitter: RecursiveCharacterTextSplitter,
    max_chars: int = ARTICLE_MAX_CHARS,
    min_chars: int = ARTICLE_MIN_CHARS,
) -> List[Dict[str, Any]]:
    """Divide el documento completo respetando limites de articulos o secciones.

    Estrategia:
      1. Si detecta 'ARTÍCULO N' -> chunkea por articulo (mantiene listas
         completas aun cuando crucen paginas).
      2. Si NO encuentra articulos pero SI encuentra secciones numeradas tipo
         'N. Son derechos...' (Reg_Estudiantes) -> chunkea por seccion.
      3. Caso especial: documento con pocos articulos (preambulo) y muchas
         secciones (cuerpo). Reg_Estudiantes tiene 3 ARTÍCULO PRIMERO/SEGUNDO/
         TERCERO (preambulo) y 100+ secciones numeradas (cuerpo). Preferimos
         secciones si superan al menos 2x los articulos.
      4. Caso contrario -> splitter recursivo clasico.
    """
    article_boundaries = _find_article_boundaries(full_text)
    section_boundaries = _find_section_boundaries(full_text)

    # Heuristica: preferir secciones si son significativamente mas densas
    # que los articulos (cuerpo del documento se enumera con N. y los pocos
    # ARTÍCULOs detectados son solo preambulo/considerandos).
    if section_boundaries and len(section_boundaries) >= 2 * max(len(article_boundaries), 1) + 1:
        return _chunk_by_boundaries(
            full_text, section_boundaries, splitter, max_chars, min_chars, "section"
        )

    if article_boundaries and len(article_boundaries) >= 2:
        return _chunk_by_boundaries(
            full_text, article_boundaries, splitter, max_chars, min_chars, "article"
        )

    if section_boundaries and len(section_boundaries) >= 3:
        return _chunk_by_boundaries(
            full_text, section_boundaries, splitter, max_chars, min_chars, "section"
        )

    # Fallback: splitter recursivo clasico. No tenemos offsets exactos, asumir 0.
    return [
        {"text": c, "article": None, "start": 0}
        for c in splitter.split_text(full_text)
    ]


def _build_page_offsets(pages: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
    """Calcula offsets (start, page_number) de cada pagina en full_text.

    full_text se construye con "\n\n".join(page_texts), asi que cada pagina
    arranca en (suma de longitudes previas + 2 * indice).
    """
    offsets: List[Tuple[int, int]] = []
    cursor = 0
    for i, page in enumerate(pages):
        offsets.append((cursor, page["page_number"]))
        cursor += len(page["text"]) + (2 if i + 1 < len(pages) else 0)
    return offsets


def _resolve_page(start: int, page_offsets: List[Tuple[int, int]]) -> int:
    """Dado un offset, devuelve el numero de pagina al que corresponde."""
    page_num = page_offsets[0][1] if page_offsets else 1
    for off, pnum in page_offsets:
        if start >= off:
            page_num = pnum
        else:
            break
    return page_num


def _chunk_by_article(
    page_text: str,
    splitter: RecursiveCharacterTextSplitter,
    max_chars: int = ARTICLE_MAX_CHARS,
    min_chars: int = ARTICLE_MIN_CHARS,
) -> List[Dict[str, Any]]:
    """Compat: divide una pagina respetando limites de articulos.

    Mantenido por compatibilidad con tests u otros llamadores. Para la ingesta
    real preferimos `_chunk_full_document` que opera sobre todo el texto.
    """
    boundaries = _find_article_boundaries(page_text)
    if not boundaries:
        return [
            {"text": c, "article": None, "start": 0}
            for c in splitter.split_text(page_text)
        ]
    return _chunk_by_boundaries(page_text, boundaries, splitter, max_chars, min_chars, "article")


def chunk_document(
    doc_data: Dict[str, Any],
    splitter: RecursiveCharacterTextSplitter,
) -> List[Document]:
    """Divide el texto de un documento en chunks de LangChain.

    Operamos sobre full_text (no por pagina) para no cortar articulos/secciones
    que crucen el limite de pagina. Cada chunk incluye metadata con: source,
    title, page (estimada por offset), chunk_index y opcionalmente article.
    """
    full_text = doc_data.get("full_text", "")
    if not full_text.strip():
        return []

    raw_chunks = _chunk_full_document(full_text, splitter)
    page_offsets = _build_page_offsets(doc_data.get("pages", []))

    chunks: List[Document] = []
    for idx, ch in enumerate(raw_chunks):
        page = _resolve_page(ch.get("start", 0), page_offsets) if page_offsets else 1
        metadata: Dict[str, Any] = {
            "source": doc_data.get("filename", "?"),
            "title": doc_data.get("title", ""),
            "page": page,
            "chunk_index": idx,
        }
        if ch.get("article") is not None:
            metadata["article"] = ch["article"]
        chunks.append(Document(page_content=ch["text"], metadata=metadata))
    return chunks


def chunk_all_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """Divide todos los documentos extraidos en chunks."""
    splitter = create_splitter(chunk_size, chunk_overlap)
    all_chunks = []
    total_articles = 0

    for doc_data in documents:
        doc_chunks = chunk_document(doc_data, splitter)
        article_chunks = sum(1 for c in doc_chunks if c.metadata.get("article"))
        total_articles += article_chunks
        all_chunks.extend(doc_chunks)
        print(
            f"  {doc_data['filename']}: {len(doc_chunks)} chunks "
            f"({article_chunks} con articulo/seccion)"
        )

    print(
        f"\nTotal: {len(all_chunks)} chunks de {len(documents)} documentos "
        f"({total_articles} anclados a articulo/seccion)"
    )
    return all_chunks
