#!/bin/bash
set -e

echo "======================================="
echo "  UNINORMA Backend - Iniciando..."
echo "======================================="

# --- 1. Esperar a Ollama ---
echo ""
echo "[1/3] Esperando que Ollama esté listo en ${OLLAMA_BASE_URL}..."
until curl -sf "${OLLAMA_BASE_URL}/api/tags" > /dev/null 2>&1; do
    echo "  Ollama no disponible aún, reintentando en 3s..."
    sleep 3
done
echo "[1/3] Ollama listo."

# --- 2. Descargar modelo si no está disponible ---
echo ""
echo "[2/3] Verificando modelo..."
python3 - <<'PYEOF'
import requests, os, json, sys

base = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
model = "qwen2.5:1.5b"

try:
    tags = requests.get(f"{base}/api/tags", timeout=10).json()
    names = [m["name"] for m in tags.get("models", [])]

    if any(model in n for n in names):
        print(f"  Modelo {model} ya disponible.")
        sys.exit(0)

    print(f"  Descargando {model} (~2 GB). Puede tardar 5-10 min la primera vez...")
    with requests.post(f"{base}/api/pull", json={"name": model}, stream=True, timeout=600) as r:
        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    status = data.get("status", "")
                    completed = data.get("completed", 0)
                    total = data.get("total", 0)
                    if total > 0:
                        pct = int(completed / total * 100)
                        print(f"  {status}: {pct}%", end="\r", flush=True)
                    elif status:
                        print(f"  {status}", flush=True)
                except Exception:
                    pass
    print(f"\n  Modelo {model} descargado correctamente.")

except Exception as e:
    print(f"  ERROR al verificar/descargar modelo: {e}")
    print("  Continuando de todas formas...")
PYEOF
echo "[2/3] Verificación de modelo completada."

# --- 3. Verificar ChromaDB ---
echo ""
echo "[3/3] Verificando base de datos vectorial (ChromaDB)..."
NEEDS_REINDEX=false
if [ ! -d "/app/data/chroma_db" ] || [ -z "$(ls -A /app/data/chroma_db 2>/dev/null)" ]; then
    NEEDS_REINDEX=true
    echo "  ChromaDB no encontrada."
elif [ -f "/app/data/chroma_db/.embedding_model" ]; then
    CURRENT_MODEL=$(cat /app/data/chroma_db/.embedding_model)
    EXPECTED_MODEL=$(python3 -c "from config import DEFAULT_EMBEDDING_MODEL; print(DEFAULT_EMBEDDING_MODEL)")
    if [ "$CURRENT_MODEL" != "$EXPECTED_MODEL" ]; then
        NEEDS_REINDEX=true
        echo "  Embedding model cambió ($CURRENT_MODEL -> $EXPECTED_MODEL)."
    fi
else
    NEEDS_REINDEX=true
    echo "  No se encontró registro del embedding model usado."
fi

if [ "$NEEDS_REINDEX" = true ]; then
    echo "  Ejecutando ingestión de datos..."
    python3 ingest.py --pdf-dir /reglamentos
    python3 -c "from config import DEFAULT_EMBEDDING_MODEL; open('/app/data/chroma_db/.embedding_model','w').write(DEFAULT_EMBEDDING_MODEL)"
    echo "  Ingestión completada."
else
    echo "[3/3] ChromaDB encontrada y lista."
fi

# --- Iniciar servidor ---
echo ""
echo "======================================="
echo "  API disponible en http://0.0.0.0:8000"
echo "======================================="
exec uvicorn api:app --host 0.0.0.0 --port 8000
