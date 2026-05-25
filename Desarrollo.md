# Manual de desarrollo: UNINORMA
## 1. Propósito del documento

Este documento tiene como objetivo servir de guía técnica para comprender, mantener, extender y dar continuidad al desarrollo del proyecto UNINORMA (Asistente Virtual Basado en SLM para la Consulta de Normatividad de Uninorte). Está dirigido a futuros equipos de trabajo, desarrolladores e investigadores que necesiten familiarizarse rápidamente con la estructura del repositorio, la arquitectura de microservicios locales, los contenedores, los scripts de ingesta y evaluación, las variables de entorno y el flujo de trabajo del sistema desplegado en infraestructura distribuida (Orange Pi + Servidor de inferencia).

## 2. Descripción general del proyecto desde la perspectiva de desarrollo

UNINORMA es una solución de Inteligencia Artificial 100% local (On-Premise) basada en la arquitectura Retrieval-Augmented Generation (RAG) combinada con Small Language Models (SLMs). El sistema ingesta normativas en PDF/HTML, las vectoriza y permite consultas en lenguaje natural mediante una interfaz web moderna, garantizando cero exposición de datos a terceros y mitigación de alucinaciones.
Desde la perspectiva de desarrollo, la arquitectura se divide en un despliegue distribuido: el frontend, el backend y la base de datos vectorial se ejecutan en un nodo edge (Orange Pi 5 Pro / Plus), mientras que el motor de inferencia LLM se ejecuta en un PC/Servidor externo conectado por red local para optimizar el rendimiento.

### 2.1 Tecnologías principales

* **Frontend**: Next.js 16.1.6, React 19.2.3, TypeScript 5, Tailwind CSS 4.

* **Backend y API**: Python 3.11, FastAPI (0.100+), Uvicorn, Pydantic.

* **Orquestación AI**: LangChain (0.2+) utilizando sintaxis declarativa LCEL.

* **Base de datos vectorial**: ChromaDB (Embebida, persistencia local).

* **Modelos de Inferencia (SLM)**: Ollama (ejecutando Qwen 2.5:1.5b cuantizado en GGUF Q4_K_M).

* **Modelos de Embeddings**: paraphrase-multilingual-MiniLM-L12-v2 vía sentence-transformers (HuggingFace).

* **Extracción de datos**: LiteParse (PDF + OCR), BeautifulSoup/Requests (Web Scraping Liferay).

* **Contenedores**: Docker y Docker Compose 3.8.

### 2.2 Componentes principales

* **Cliente web (Frontend)**: Interfaz conversacional que maneja la captura de prompts, renderizado por streaming de tokens y visualización de tarjetas de fuentes citadas. Incluye un proxy reverso transparente (/api/[...proxy]).

* **Servidor/API Core (Backend)**: Expone endpoints RESTful (/query, /health, /models, /models/load), valida payloads y enruta las solicitudes hacia la cadena RAG.

* **Orquestador RAG**: Transforma texto en vectores, realiza búsqueda por similitud del coseno (Top-K=6) en ChromaDB, inyecta contexto en el prompt y gestiona la comunicación con Ollama.

* **Pipeline de Ingesta**: Conjunto de scripts asíncronos que escrapean el portal Uninorte, aplican chunking recursivo (1000 tokens / 200 solapamiento) y guardan los vectores densos.

* **Módulo de Benchmarking**: Herramienta interna para medir métricas de hit rate, relevancia y fidelidad con un set de 40+ preguntas.

## 3. Estructura del repositorio
El repositorio sigue un enfoque monorepo que separa claramente la interfaz de usuario, la lógica de inteligencia artificial/backend, la infraestructura y los scripts de prueba.

### 3.1 Árbol general del repositorio

```
├Deploy
├── frontend/
│   ├── app/
│   ├── components/
│   ├── package.json
│   └── frontend.Dockerfile
├── backend/
│   ├── src/
│   ├── data/
│   ├── benchmark/
│   ├── backend.Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── README.md
├── Informe.md
├── Instalacion.md
└── Desarrollo.md
```

### 3.2 Descripción de directorios y archivos relevantes
* **frontend/app/**: Contiene la lógica de enrutamiento del App Router de Next.js, incluyendo la ruta de la API Proxy que comunica con el backend eludiendo problemas de CORS.

* **frontend/components/**: Aloja los componentes UI reutilizables (ChatMessage.tsx, ModelSelector.tsx, SourceCard.tsx, StatusBar.tsx).

* **backend/src/**: Núcleo del proyecto. Contiene módulos independientes como api.py (FastAPI), rag_chain.py (LangChain LCEL), embeddings.py, vector_store.py (ChromaDB) y los extractores.

* **backend/data/chroma_db/**: Directorio donde ChromaDB persiste la colección de vectores de forma local. No debe ser modificado manualmente.

* **backend/benchmark/**: Contiene test_questions.json y scripts de métricas para evaluar distintos modelos SLM.

## 4. Organización de la solución a nivel de código
El sistema sigue una arquitectura orientada a microservicios con un fuerte desacoplamiento habilitado por las abstracciones de LangChain.

### 4.1 Organización por módulos o capas

* **Capa de Presentación (Frontend)**: SSR y Client Components en Next.js.

* **Capa de Enrutamiento (FastAPI)**: Define los contratos de la API mediante Pydantic.

* **Capa de Orquestación (LangChain)**: Define el flujo lógico Retriever → PromptTemplate → LLM → StrOutputParser.

* **Capa de Persistencia Vectorial**: Integración embebida con ChromaDB.
Capa de Extracción de Datos (Offline): Web Scraping local y Parsing de PDFs.

### 4.2 Relación entre componentes del sistema y código fuente

* **Ingesta**: web_scraper.py descarga; pdf_extractor.py extrae/OCR; text_chunker.py divide.

* **Vectorización**: embeddings.py inicializa MiniLM-L12-v2; vector_store.py guarda en la colección uninorte_normatividad.

* **Inferencia RAG**: rag_chain.py ejecuta la cadena LCEL principal.

* **API Proxy**: frontend/app/api/[...proxy]/route.ts protege las llamadas HTTP internas.

## 5. Contenedores
La solución completa está paquetizada en Docker para garantizar el cumplimiento del requerimiento de portabilidad (RNF03) y facilitar el despliegue en la arquitectura ARM64 de la Orange Pi.

### 5.1 Contenedores utilizados

* **backend**: Contenedor Python que ejecuta FastAPI, la cadena LangChain y ChromaDB embebido.

* **frontend**: Contenedor Node.js que sirve la aplicación web de Next.js.

***(Nota)**: Ollama no se incluye en el docker-compose.yml base, ya que por diseño se ejecuta en bare-metal en un nodo/PC externo con recursos dedicados.*

### 5.2 Archivos relacionados con contenedores

* **docker/backend.Dockerfile**: Imagen multietapa que instala dependencias de Python y descarga el modelo de HuggingFace en tiempo de build para permitir arranques 100% offline.

* **docker/frontend.Dockerfile**: Construye la versión optimizada de producción de Next.js.

* **docker-compose.yml**: Orquesta los servicios, redes y volúmenes en el nodo principal (Orange Pi).

### 5.3 Construcción y ejecución de contenedores
Para levantar el entorno completo:
```
Bash
docker compose build
docker compose up -d
```
Para verificar logs en caso de errores en la API:

```
Bash
docker compose logs -f backend
```

### 5.4 Redes, puertos y volúmenes

* **Red**: Se utiliza una red bridge custom (uninorma_network).

* **Puertos**:
    * Frontend expuesto en el puerto 5174:3000.

    * Backend expuesto internamente en el puerto 8000 (accesible vía el proxy Next.js).

* **Volúmenes**: Se monta ./backend/data/chroma_db hacia el interior del contenedor backend para asegurar que los vectores persistan entre reinicios.

### 5.5 Recomendaciones para modificar contenedores

* **Descarga de modelos**: Si se cambia el modelo de embeddings en embeddings.py, es obligatorio actualizar el script de precarga en el backend.Dockerfile para no degradar el tiempo de inicio.

* **Arquitectura**: Al desplegar en la Orange Pi, Docker resolverá automáticamente las imágenes compatibles con ARM64 (aarch64).

## 6. Scripts y automatizaciones

### 6.1 Scripts principales

* **En Backend (Python)**:
    * python src/ingest.py: Ejecuta el pipeline completo de scraping y vectorización.

    * python benchmark/run_benchmark.py: Ejecuta el plan de pruebas automático contra las más de 40 preguntas del JSON.

* **En Frontend (Node)**:
    * npm run dev: Inicia servidor Next.js en caliente para desarrollo UI.
    * npm run build: Compila Server Components y CSS para producción.

### 6.2 Ubicación de scripts auxiliares

Los scripts aislados de limpieza de datos o métricas matemáticas específicas del RAG se encuentran dentro del directorio backend/benchmark/.

### 6.3 Consideraciones para su uso

El script ingest.py puede demorar varios minutos dependiendo de la cantidad de PDFs escaneados que requieran OCR (LiteParse). Asegúrese de no interrumpir el proceso para evitar bloqueos corruptos en los archivos .sqlite3 de ChromaDB.

## 7. Variables de entorno

El sistema depende de muy pocas variables de entorno, ya que no se consumen APIs comerciales de pago.

### 7.1 Variables requeridas

* **Backend (backend/.env)**:

    * OLLAMA_BASE_URL: Crítica. Debe apuntar a la IP privada del servidor externo que corre Ollama (Ej. http://192.168.1.50:11434).

    * DEFAULT_MODEL: Modelo a usar al arrancar (Ej. qwen2.5:1.5b).

* **Frontend (frontend/.env)**:

    * NEXT_PUBLIC_API_URL: URL interna para que el proxy Next.js alcance a FastAPI (en docker suele ser http://backend:8000).

### 7.2 Variables por ambiente

Dado que es un entorno puramente local, las configuraciones suelen ser idénticas, variando únicamente el apuntador IP de OLLAMA_BASE_URL dependiendo de si se ejecuta todo en localhost (desarrollo puro) o en red distribuida (producción Orange Pi).

### 7.3 Manejo seguro de secretos

La principal ventaja de UNINORMA es la privacidad (RNF01). El sistema NO requiere API Keys (ni de OpenAI, ni de Pinecone, etc.). Por tanto, no hay gestión crítica de secretos.

## 8. Flujo de trabajo de desarrollo

### 8.1 Preparación del entorno

1. Clonar el repositorio.

2. Asegurar que Ollama esté corriendo en el nodo de inferencia y que el modelo requerido esté descargado (ollama run qwen2.5:1.5b).

3. Copiar los archivos .env.example a .env y configurar OLLAMA_BASE_URL.

4. Levantar los contenedores: docker compose up -d.

### 8.2 Desarrollo de nuevas funcionalidades

* Si se modifica la estructura del Prompt o la métrica de RAG, los cambios deben hacerse en rag_chain.py.

* Si se añaden nuevas fuentes normativas, no se modifica código: se deben añadir las URLs al archivo de configuración del scraper y re-ejecutar ingest.py (cumpliendo RNF05).

### 8.3 Ejecución de pruebas y validaciones

Antes de cualquier PR o despliegue definitivo, se debe correr obligatoriamente el módulo de pruebas de integración:

```
Bash
python backend/benchmark/run_benchmark.py
```

*Criterio de éxito mínimo*: Hit rate de recuperación vectorial > 85% y cero fallos en el parsing JSON de LangChain.

## 9. Dependencias y servicios externos

A nivel de APIs o SaaS de terceros, el proyecto es 100% autónomo y offline en la fase de inferencia.

### 9.1 Servicios externos integrados (Fase de Build/Ingesta)

* **HuggingFace Hub**: Utilizado al construir la imagen Docker para descargar los pesos de paraphrase-multilingual-MiniLM-L12-v2.

## 10. Convenciones del proyecto

### 10.1 Convenciones de código

* **Backend (Python)**: Se aplica Type Hinting estricto. Todas las respuestas de API se manejan serializando clases de Pydantic.

* **Frontend (TypeScript)**: Se respetan las convenciones de Server Components de React 19. Las directivas 'use client' solo se aplican en componentes interactivos (ChatMessage.tsx).

* **Prompting**: El System Prompt no debe modificarse sin realizar un benchmark posterior, ya que las instrucciones de "no alucinar" y "ceñirse al contexto" han sido afinadas rigurosamente para el modelo Qwen.

## 11. Problemas frecuentes y recomendaciones

### 11.1 Problemas frecuentes

* **Timeouts hacia Ollama**: Si el backend muestra errores de conexión rehusada, verifique que en el PC externo Ollama haya sido iniciado exponiendo el host (variable de entorno OLLAMA_HOST=0.0.0.0 antes de lanzar ollama serve).

* **ChromaDB bloqueado**: Si se aborta bruscamente la ingesta, Chroma puede dejar un archivo .lock. Borrar la carpeta data/chroma_db e ingestar de nuevo soluciona el problema.

### 11.2 Deuda técnica conocida

* **Cuello de botella en Inferencia**: Ollama encola las peticiones secuencialmente. Si múltiples usuarios envían prompts simultáneamente, los tiempos de espera crecerán linealmente.

* **Falta de Memoria de Sesión (Multi-turno)**: El prototipo actual evalúa RAG en consultas independientes (Single-turn). No retiene el contexto de la pregunta anterior.

### 11.3 Recomendaciones para continuidad

Para futuros grupos de investigación, se sugiere:

1. Implementar la memoria de conversación inyectando un historial resumido en el vector temporal.

2. Explorar despliegues con vLLM en lugar de Ollama para permitir batching continuo y soportar múltiples usuarios en paralelo.

## 12. Historial de decisiones técnicas relevantes

| Decisión | Alternativas evaluadas | Selección Definitiva | Razón Principal |
|----------|------------------------|----------------------|-----------------|
|Base de Datos Vectorial|	Pinecone, Weaviate, Milvus, ChromaDB|	ChromaDB|	Se ejecuta embebido en Python; no requiere servidor externo ni cuentas SaaS, respetando 100% la restricción de privacidad.|
|Modelo Inferencia (SLM)|	GPT-4, Llama 3.2:3b, Phi-3, Qwen 2.5:1.5b|Qwen 2.5:1.5b|	Demostró mayor fluidez semántica en español y menor huella de RAM/VRAM bajo cuantización GGUF Q4_K_M (~2GB).|
|Orquestación RAG|	LlamaIndex, Hardcoded, LangChain|	LangChain (LCEL)|	Mayor madurez de su ecosistema declarativo, lo que permite sustituir el LLM sin reescribir lógica (Bajo acoplamiento).|
|Arquitectura de Despliegue|	Todo en Orange Pi vs. Todo en Nube	Distribuida| (OPi + PC externo)|	La Orange Pi colapsaba en tiempos de respuesta al ejecutar el modelo localmente. Separar la Inferencia al PC logró latencia < 8s.|
|Proxy de API|	Nginx, Traefik, Next.js API Routes|	Next.js 16|	Permite enrutar el tráfico cliente->backend evadiendo CORS sin añadir un contenedor extra de Nginx al stack.|

## 13. Referencias relacionadas

* [LangChain LCEL Documentation](https://docs.langchain.com/oss/python/langchain/overview#langchain-expression-language-lcel)

* [ChromaDB Python API](https://docs.trychroma.com/docs/overview/introduction)

* [Ollama REST API](https://github.com/ollama/ollama/blob/main/docs/api.md)

* [Next.js Route Handlers (Proxy)](https://nextjs.org/docs/app/api-reference/file-conventions/route)

* *Para detalles teóricos, métricas esperadas y contexto del negocio, consultar el archivo [Informe.md](./Informe.md) en la raíz del proyecto.*
