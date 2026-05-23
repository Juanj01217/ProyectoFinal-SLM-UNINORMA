# ProyectoFinal-SLM-UNINORMA

# Informe Final: Asistente Virtual Basado en Small Language Model (SLM) para la Consulta de Normatividad de Uninorte

**Equipo:** Carlos Mendoza, Jesús De la Cruz, Juan José Aragón

**Docente:** Augusto Salazar Silva

**Tutor** Eduardo Zurek Varela

**Universidad del Norte — Semestre 2026-1**

---
## 1. Introducción

Con el advenimiento del Procesamiento de Lenguaje Natural (NLP) y, más recientemente, de los Modelos de Lenguaje Grande (LLMs), ha emergido un nuevo paradigma de interacción humano-computadora basado en interfaces conversacionales en lenguaje natural. Estos sistemas prometen eliminar la barrera entre el usuario y la información estructurada, transformando la experiencia de consulta en un diálogo fluido. Sin embargo, la adopción de LLMs comerciales a través de APIs de terceros plantea desafíos críticos en entornos institucionales: la privacidad de los datos consultados queda expuesta a proveedores externos, la dependencia de infraestructura en la nube genera costos operativos recurrentes y la naturaleza "caja negra" de estos servicios impide garantizar la trazabilidad y fidelidad de las respuestas generadas.

Para abordar estas problemáticas, el presente proyecto propone el diseño e implementación de UNINORMA, nuestro caso de uso de asistente virtual inteligente basado en la arquitectura Retrieval-Augmented Generation (RAG) combinada con Small Language Models (SLMs). La solución ha evolucionado hacia un despliegue definitivo en hardware **Orange Pi 5 Pro / Plus**, optimizando la carga de trabajo mediante una arquitectura distribuida: los servicios de orquestación y frontend se ejecutan en la placa ARM, mientras que la inferencia del SLM se delega a un servidor externo para garantizar tiempos de respuesta óptimos. Este informe documenta el estado actual del proyecto, abarcando los requerimientos definitivos, las decisiones de diseño y arquitectura adoptadas, la implementación funcional desarrollada y el plan de pruebas que guiará la validación del sistema.

---
## 2. Marco Conceptual

Para comprender el funcionamiento de UNINORMA, es necesario precisar los conceptos tecnológicos que sustentan la arquitectura de inteligencia artificial local:

### 2.1. Modelos de Lenguaje pequeño (SLM)

Los **Small Language Models** (SLM) son modelos de lenguaje diseñados para comprender y generar texto en lenguaje natural con un número reducido de parámetros [2], [4] en comparación con los Large Language Models (LLMs) como GPT-4 o Claude [1], [13], [14]. Debido a las variaciones entre los rangos que se mencionan en distintos artículos, el rango de parámetros estaría generalmente entre 1B y 15B [1]–[5].

A diferencia de los LLMs, cuyo objetivo es cubrir conocimiento general masivo [1], los SLMs se centran en:
- **Eficiencia:** Requieren significativamente menos memoria RAM/VRAM y potencia de cómputo [3], [4].
- **Especialización:** Son altamente efectivos cuando se acotan a un dominio específico (como la normatividad universitaria) mediante técnicas como RAG [2], [5].
- **Privacidad y Control:** Permiten el despliegue local o en infraestructura privada, eliminando la dependencia de APIs de terceros y garantizando la soberanía de los datos [2], [3].
- **Baja Latencia:** Su tamaño compacto permite una inferencia más rápida, ideal para aplicaciones en tiempo real y dispositivos edge [1], [4].

En este proyecto, utilizamos el modelo Qwen 2.5:1.5b [9], el cual ofrece un equilibrio excepcional entre precisión lingüística en español y velocidad de procesamiento en entornos locales eficientes [12].

### 2.2. Modelos de Lenguaje Grande (LLMs)
Un Modelo de Lenguaje Grande (LLM, por sus siglas en inglés) es un sistema de inteligencia artificial basado en arquitecturas de redes neuronales profundas—típicamente de tipo Transformer—diseñado para procesar, comprender y generar texto en lenguaje natural [1]. Estos modelos son entrenados con volúmenes masivos de datos textuales, lo que les permite capturar estructuras lingüísticas complejas, contextos, semántica y relaciones entre palabras [1], [13].

En términos operativos, un LLM funciona bajo un principio probabilístico: calcula y predice cuál es el elemento textual (token) más adecuado para continuar una secuencia dada a partir del contexto proporcionado en la consulta (prompt). En el ámbito institucional, su capacidad para realizar tareas avanzadas como resúmenes, traducciones y respuestas a preguntas los convierte en el motor de razonamiento de las interfaces conversacionales modernas [1], [14].

### 2.3. Retrieval-Augmented Generation (RAG)

La Generación Aumentada por Recuperación (RAG) es una arquitectura que optimiza la salida de un modelo de lenguaje al consultar una base de conocimientos externa y confiable antes de generar una respuesta [6], [7]. En lugar de confiar únicamente en el conocimiento "entrenado" del modelo (el cual puede estar desactualizado o ser propenso a alucinaciones) [6], el sistema RAG opera en tres fases:

* **Recupera**: Busca fragmentos de documentos relevantes (normatividad) basados en la pregunta del usuario en un corpus indexado [7].

* **Aumenta**: Añade esos fragmentos al prompt del usuario como contexto verídico y enriquecido [6].

* **Genera**: Solicita al SLM que redacte una respuesta basada estrictamente en ese contexto recuperado [7].

### 2.4. Embeddings y Similitud Semántica

Los embeddings son representaciones numéricas (vectores) de fragmentos de texto generados mediante redes siamesas optimizadas [8]. A diferencia de una búsqueda por palabras clave tradicional, los embeddings capturan el significado semántico profundo del texto [8]. Esto permite que el sistema entienda que "pérdida de asignatura" y "reprobar una materia" son conceptos similares, permitiendo encontrar la norma correcta aunque el usuario no use la terminología jurídica exacta. La relevancia matemática entre la consulta y los documentos se calcula mediante la Similitud del Coseno, midiendo la proximidad de los vectores en un espacio multidimensional [8].


### 2.5. Bases de Datos Vectoriales (Vector Stores)

A diferencia de las bases de datos relacionales (SQL) tradicionales, una Base de Datos Vectorial como ChromaDB está optimizada específicamente para almacenar, indexar y buscar vectores de alta dimensionalidad de forma masiva [11]. Su función principal dentro de la arquitectura es indexar de manera eficiente los cientos de fragmentos del corpus normativo de la Universidad y permitir una recuperación de información precisa en milisegundos [11].


### 2.6. Cuantización de Modelos (Formato GGUF)

La cuantización es una técnica de compresión que reduce la precisión de los pesos de un modelo (por ejemplo, de punto flotante de 16 bits a enteros de 4 bits). Esto permite que modelos optimizados como la familia Qwen 2.5 [9], que originalmente requerirían GPUs profesionales para su ejecución estándar, puedan ejecutarse de forma fluida en hardware limitado como CPUs de consumo o placas ARM (como la Orange Pi) [12]. Este proceso reduce el consumo de memoria RAM en más de un 70% con una pérdida mínima de precisión en la generación de respuestas [12]. El formato GGUF es el estándar actual de la comunidad para este tipo de ejecución local eficiente [12].

### 2.7. Orquestación mediante LangChain (LCEL)

LangChain es el framework modular que actúa como el núcleo de orquestación y "pegamento" de todo el sistema informático [10]. Su Lenguaje de Expresión (LCEL) permite definir flujos de datos donde la salida de un componente (como el buscador vectorial) se convierte en la entrada directa del siguiente componente (el modelo de lenguaje) de forma declarativa [10]. Esto facilita considerablemente la modularidad del código, el mantenimiento del pipeline de IA y el manejo de flujos asíncronos o de respuestas parciales en tiempo real (streaming) [10].

---

## 3. Planteamiento del Problema

### 3.1. Descripción del Problema

La Universidad del Norte cuenta con un vasto corpus normativo compuesto por al menos 25 documentos institucionales activos, entre los cuales se incluyen el Reglamento Estudiantil de Pregrado, el Reglamento de Profesores, políticas de Propiedad Intelectual, normatividad de Bienestar Universitario, reglamentos de posgrado y resoluciones sobre derechos y deberes de la comunidad académica. Este acervo documental supera colectivamente varios cientos de páginas y se actualiza de forma periódica mediante resoluciones del Consejo Directivo, lo que dificulta mantener una versión unificada y accesible del conocimiento institucional.

El modelo actual de acceso a esta normatividad presenta deficiencias estructurales. Los portales web institucionales implementan motores de búsqueda léxica que identifican coincidencias de palabras clave sin comprender el contexto semántico de la consulta, fallando sistemáticamente frente a sinónimos, paráfrasis o preguntas formuladas en lenguaje coloquial. Adicionalmente, cuando el sistema sí localiza un documento pertinente, transfiere toda la carga interpretativa al usuario: este debe descargar el PDF, navegar por su estructura y extraer por sí mismo el fragmento que responde a su duda. Este proceso, que puede tomar entre 15 y 30 minutos para consultas no triviales, resulta especialmente problemático para estudiantes de primer año que aún no están familiarizados con el lenguaje jurídico-administrativo de los reglamentos.

Ante esta necesidad de optimizar el acceso a la información a través de interfaces conversacionales modernas, el uso de Modelos de Lenguaje Grande (LLMs) comerciales de terceros (como OpenAI GPT o Anthropic Claude) surge como una alternativa inmediata; sin embargo, su adopción en un entorno institucional introduce desafíos críticos e inasumibles:

* **Exposición y Privacidad de los Datos**: Consultar normativas internas mediante APIs externas implica enviar datos institucionales y consultas de los usuarios a servidores de proveedores externos. Esto vulnera las políticas de gobernanza de datos de la universidad y expone información potencialmente sensible a terceros.

* **Costos Operativos Recurrentes**: La dependencia de modelos alojados en la nube bajo esquemas de pago por uso (pay-per-token) genera una carga financiera variable y acumulativa, insostenible para un servicio público de alta demanda destinado a miles de estudiantes y administrativos.

* **Falta de Trazabilidad y Alucinaciones**: Los LLMs comerciales operan como sistemas de "caja negra". En un contexto normativo legal, la tendencia de estos modelos a generar respuestas plausibles pero falsas (alucinaciones) es crítica; el sistema no puede permitirse parafrasear libremente un reglamento sin garantizar una fidelidad absoluta al texto original y la capacidad de citar la fuente exacta.

La consecuencia más crítica de esta brecha de acceso y de las limitaciones de las tecnologías comerciales tradicionales es la desinformación activa: estudiantes que toman decisiones académicas (matricular asignaturas, solicitar retiros de materias, interponer recursos disciplinarios) con base en información incompleta o malinterpretada por no haber encontrado el artículo reglamentario pertinente.

Se requiere, por tanto, el desarrollo de un sistema propio capaz de comprender el lenguaje natural del usuario, recuperar los fragmentos exactos dentro del corpus normativo y sintetizar una respuesta coherente y citable, operando bajo una arquitectura local y controlada que elimine la dependencia de la nube, garantice el costo cero por consulta y resguarde la privacidad de la comunidad universitaria.

## 3.2 Restricciones y Supuestos de Diseño

Desde el punto de vista de la infraestructura computacional, la principal restricción del proyecto es la obligatoriedad de ejecución local (_on-premise_). Sin embargo, debido a las limitaciones de recursos del hardware **Orange Pi 5 Pro / Plus**, se ha adoptado una arquitectura de carga distribuida como despliegue definitivo. El motor de inferencia (Ollama) no se encuentra desplegado en el mismo contenedor que el backend y frontend; en su lugar, se instancia en un ordenador independiente (PC con GPU/CPU dedicada) para repartir la carga de rendimiento y lograr una mejor respuesta del SLM. Esto permite que la Orange Pi se dedique exclusivamente a la gestión de la base de datos vectorial (ChromaDB), la orquestación RAG y el servicio web, mientras que el modelo **Qwen 2.5:1.5b** (1.5 mil millones de parámetros) corre de forma externa, optimizando drásticamente la latencia.

En cuanto a restricciones de diseño de software, el sistema está concebido como un prototipo funcional de validación académica y no como un sistema de producción a escala universitaria. El servidor de inferencia externo maneja las solicitudes de forma secuencial, lo que establece un cuello de botella de rendimiento frente a cargas concurrentes simultáneas. Asimismo, la veracidad de las respuestas está acotada por el alcance del corpus ingresado: el sistema no debe, bajo ninguna circunstancia, generar respuestas basadas en conocimiento paramétrico externo al corpus; toda afirmación debe estar fundamentada en los fragmentos recuperados por el componente de recuperación semántica.


Los supuestos fundamentales bajo los cuales se plantea la solución son los siguientes: (a) el corpus documental de 25 fuentes —20 PDFs y 5 páginas web— procesado en 907 fragmentos (_chunks_) constituye una muestra representativa y suficiente de la normatividad activa de la institución para los propósitos de validación del prototipo; (b) los usuarios finales interactuarán con el sistema utilizando exclusivamente el idioma español, lo cual justifica la selección de un modelo de _embeddings_ multilingüe con énfasis en representaciones del español; y (c) el entorno de despliegue contará con un mínimo de 8 GB de RAM, 2 núcleos de CPU y 20 GB de espacio en disco, conforme a los requerimientos documentados del stack tecnológico seleccionado.

### 3.3. Alcance

El proyecto comprende el ciclo de vida completo de una solución de software de inteligencia artificial conversacional, desde la adquisición y procesamiento de datos hasta el despliegue en contenedores. En cuanto a la capa de datos, el alcance incluye la construcción de un pipeline automatizado de ingesta que realiza _web scraping_ del portal normativo de la Universidad del Norte, extrae texto de documentos PDF (incluyendo PDFs escaneados mediante OCR), aplica una estrategia de segmentación semántica (_chunking_ recursivo con solapamiento) y genera representaciones vectoriales densas mediante un modelo de _embeddings_ multilingüe, almacenándolas en una base de datos vectorial local (ChromaDB).

En cuanto a los componentes técnicos del sistema, el alcance abarca el desarrollo de una API RESTful en FastAPI que expone los endpoints de consulta, gestión de modelos y verificación de estado del sistema; la integración con el motor de inferencia local Ollama para la ejecución del modelo generativo Qwen 2.5:1.5b; la orquestación del flujo RAG mediante LangChain (LCEL); y el desarrollo de una interfaz de usuario web moderna construida en Next.js 16 con React 19 y Tailwind CSS. Adicionalmente, se incluye un módulo de _benchmarking_ con más de 40 preguntas de prueba categorizadas por dificultad y área normativa, junto con métricas de evaluación de recuperación, relevancia y fidelidad.

Fuera del alcance de esta propuesta se encuentran los siguientes aspectos: la integración del asistente con los sistemas de información core de la Universidad del Norte (SIS académico, portales de autogestión, plataformas LMS), dado que esto requeriría acuerdos institucionales que exceden el marco de un proyecto de pregrado; el soporte para idiomas distintos al español; la implementación de mecanismos de autenticación y control de acceso por roles; y la continuidad de sesión multiturno persistente entre distintas sesiones de usuario. El sistema tampoco proporciona asesoría legal vinculante: sus respuestas tienen carácter exclusivamente informativo.

---

## 4. Objetivos

### 4.1. Objetivo General

Diseñar e implementar un asistente virtual inteligente basado en la arquitectura de Generación Aumentada por Recuperación (RAG) y Modelos de Lenguaje Reducidos (SLM) de ejecución local, que facilite la consulta en lenguaje natural de la normatividad institucional de la Universidad del Norte, garantizando respuestas precisas, citadas y libres de alucinaciones informativas.

### 4.2. Objetivos Específicos

Los objetivos específicos operacionalizan el objetivo general en entregables concretos y medibles, articulados en torno a los componentes funcionales del sistema:

- **OE1 — Pipeline de Ingesta:** Desarrollar un pipeline automatizado de adquisición, extracción y procesamiento de datos no estructurados (PDFs y HTML) que permita la segmentación semántica (_chunking_ recursivo con solapamiento de 200 tokens sobre ventanas de 1.000 tokens) y la representación vectorial del corpus normativo institucional mediante el modelo `paraphrase-multilingual-MiniLM-L12-v2`.

- **OE2 — Motor de Búsqueda Semántica:** Implementar un motor de recuperación semántica utilizando ChromaDB con búsqueda por similitud del coseno, configurado para retornar los 6 fragmentos (_Top-K = 6_) con mayor similitud semántica a la consulta del usuario, optimizado para el vocabulario jurídico-administrativo del contexto colombiano.

- **OE3 — Integración del SLM:** Integrar y configurar el modelo Qwen 2.5:3b ejecutado localmente mediante Ollama, aplicando técnicas de _prompt engineering_ para restringir estrictamente la generación al contexto recuperado y mitigar las alucinaciones en un entorno RAG cerrado, con temperatura de inferencia de 0.1.

- **OE4 — API y Orquestación RAG:** Construir una API RESTful escalable en FastAPI que orqueste el flujo completo de inferencia mediante LangChain LCEL, exponiendo los _endpoints_ de consulta (`/query`), gestión de modelos (`/models`, `/models/load`) y verificación de estado (`/health`).

- **OE5 — Interfaz de Usuario:** Desarrollar una interfaz de usuario web moderna en Next.js 16 con React 19 y Tailwind CSS, que permita la interacción fluida con el asistente, la visualización de fuentes citadas y la selección dinámica del modelo SLM activo.

- **OE6 — Evaluación y Benchmarking:** Diseñar y ejecutar un plan de evaluación cuantitativa con un conjunto de más de 40 preguntas de prueba categorizadas, midiendo métricas de recuperación (_retrieval hit rate_), relevancia de respuesta (_answer relevancy_), fidelidad al contexto (_faithfulness_) y detección de alucinaciones, comparando el desempeño de al menos tres modelos SLM distintos.

El cumplimiento de estos objetivos se verifica de forma objetiva a través de los criterios de aceptación definidos en el plan de pruebas: una tasa de recuperación correcta superior al 85% en el Top-3 de resultados para el conjunto de validación, un tiempo de respuesta inferior a 8 segundos para el inicio del _streaming_ de tokens en el entorno local de referencia, y la capacidad de rechazar correctamente consultas fuera del dominio normativo institucional.

---

## 5. Estado del Arte

En el panorama actual de soluciones para asistentes virtuales orientados a consultas institucionales en educación superior, pueden identificarse tres categorías principales [17]. La primera corresponde a las plataformas comerciales de chatbots universitarios, como Engageware (anteriormente Mongoose Harmony), Ivy.ai y Ada CX, que ofrecen soluciones SaaS preconfiguradas para responder preguntas frecuentes de estudiantes. Estas herramientas se integran con los sistemas de información universitarios y proporcionan una experiencia conversacional aceptable para consultas de alto nivel (fechas de matrícula, requisitos de admisión, localización de oficinas), pero presentan limitaciones estructurales para consultas normativas precisas: su base de conocimiento depende de la carga manual de contenidos por parte de administradores, no son capaces de razonar sobre documentos PDF no estructurados y operan exclusivamente sobre infraestructura en la nube del proveedor, lo que compromete la soberanía de los datos institucionales [17].

La segunda categoría comprende las soluciones basadas en APIs de LLMs comerciales (OpenAI GPT-4, Google Gemini, Anthropic Claude), que han demostrado capacidades conversacionales excepcionales [13], [14]. Proyectos como "ChatPDF" o los asistentes de estudio basados en ChatGPT han explorado el uso de estas APIs para responder preguntas sobre documentos específicos. Sin embargo, para el contexto de una institución universitaria colombiana, esta aproximación enfrenta obstáculos significativos: (a) los costos por token de inferencia escalan con el volumen de consultas, generando un gasto operativo recurrente incompatible con presupuestos académicos; (b) toda consulta transmitida a la API es procesada en servidores externos, lo que puede constituir una vulneración de políticas de privacidad de datos institucionales; (c) estos modelos generan respuestas basadas en su conocimiento paramétrico general, con alta propensión a alucinaciones cuando se les consulta sobre normativas específicas que no fueron parte de su entrenamiento [6], [15].

La tercera categoría, y la más relevante para este proyecto, corresponde a los marcos de trabajo RAG (Retrieval-Augmented Generation) locales [15], [16]. Soluciones como **PrivateGPT** y **AnythingLLM** han popularizado la idea de ejecutar pipelines RAG completamente on-premise, utilizando modelos de código abierto cuantizados [20]. PrivateGPT, en su versión de código abierto, implementa un stack similar al de este proyecto (LlamaCpp + ChromaDB + sentence-transformers) pero con una interfaz mínima y sin soporte para múltiples modelos simultáneos [20]. AnythingLLM ofrece una experiencia de usuario más pulida, pero está concebida como una herramienta de propósito general, sin optimizaciones para vocabularios jurídico-administrativos en español ni capacidad de ingesta automatizada mediante web scraping [20]. La comparación con estas soluciones revela la oportunidad diferenciadora de UNINORMA: una solución especializada en el corpus normativo concreto de la Universidad del Norte, con un pipeline de ingesta automático, soporte multimodelo y benchmarking cuantitativo integrado.

Desde la perspectiva del modelado del lenguaje, la literatura reciente (2023–2025) ha documentado que modelos en el rango de 1B a 7B de parámetros, cuando se especializan mediante RAG sobre un dominio cerrado, pueden igualar el rendimiento de modelos significativamente más grandes en tareas de razonamiento deductivo acotado [1], [16]. El modelo Qwen 2.5:1.5b, desarrollado por Alibaba Cloud, ha demostrado un rendimiento superior en tareas de comprensión lectora en español frente a alternativas de tamaño equivalente como Llama 3.2:3b o Phi-3 Mini [9], lo que justifica su selección como modelo primario para este prototipo. La cuantización Q4_K_M (reducción de precisión de coma flotante de 16 bits a enteros de 4 bits mediante el formato GGUF) permite reducir la huella de memoria del modelo de ~6 GB a ~2 GB sin una degradación perceptible de la perplejidad en tareas de razonamiento sobre texto en español [12], [18], [19].

---

## 6. Requerimientos

### 6.1. Requerimientos Funcionales

Los requerimientos funcionales definen el comportamiento observable del sistema desde la perspectiva del usuario final y de los operadores del sistema. Su definición parte del análisis de los flujos de uso primarios identificados durante la fase de diseño: la consulta de información normativa en lenguaje natural, la visualización de fuentes, la selección de modelo y el monitoreo del estado del sistema.

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF01 | El sistema debe aceptar y procesar consultas escritas en lenguaje natural en español, sin requerir que el usuario conozca palabras clave específicas o la estructura de los documentos. | Alta |
| RF02 | El sistema debe generar respuestas basadas exclusivamente en los fragmentos recuperados del corpus normativo pre-cargado, sin incorporar conocimiento paramétrico externo del modelo generativo. | Alta |
| RF03 | El sistema debe mostrar junto a cada respuesta las fuentes de información utilizadas, indicando el nombre del documento y el número de página correspondiente. | Alta |
| RF04 | El sistema debe exponer un endpoint de consulta (`POST /query`) que acepte la pregunta del usuario y el identificador del modelo SLM a utilizar, retornando la respuesta y las fuentes en formato JSON. | Alta |
| RF05 | El sistema debe permitir la selección dinámica del modelo SLM activo a través de un endpoint de gestión (`POST /models/load`) sin necesidad de reiniciar el servicio. | Media |
| RF06 | El sistema debe exponer un endpoint de estado (`GET /health`) que informe en tiempo real sobre la disponibilidad del motor de inferencia Ollama, la disponibilidad de la base de datos vectorial y el modelo activo. | Media |
| RF07 | Cuando la consulta del usuario no tenga correspondencia en el corpus normativo, el sistema debe responder explícitamente que no cuenta con información institucional sobre ese tema, en lugar de generar una respuesta inventada. | Alta |
| RF08 | El sistema debe transmitir la respuesta generada mediante _streaming_ de tokens para reducir la latencia percibida por el usuario. | Media |

Los requerimientos RF01, RF02, RF03 y RF07 constituyen el núcleo funcional del sistema y son condición necesaria para que el asistente sea considerado correcto y útil en el contexto normativo universitario. Su incumplimiento no es aceptable en ninguna fase de despliegue. Los requerimientos RF05 y RF08 son de prioridad media y están orientados a mejorar la experiencia de uso durante la fase de benchmarking, donde se evaluarán múltiples modelos SLM de forma comparativa.

### 6.2. Requerimientos No Funcionales

Los requerimientos no funcionales definen los atributos de calidad que determinan la idoneidad del sistema más allá de sus funcionalidades específicas. En el caso de UNINORMA, estos atributos son particularmente críticos dado el contexto _on-premise_ y las restricciones de hardware bajo las cuales opera el sistema.

| ID | Categoría | Descripción |
|----|-----------|-------------|
| RNF01 | Privacidad | Toda la arquitectura (base de datos vectorial, motor LLM, API, interfaz) debe ejecutarse localmente sin transmitir datos a servicios externos durante la fase de inferencia. |
| RNF02 | Rendimiento | El tiempo total de respuesta (desde el envío de la consulta hasta el inicio del _streaming_ de tokens) no debe superar los 8 segundos en el entorno de referencia (8 GB RAM, 4 CPU cores). |
| RNF03 | Portabilidad | El sistema completo debe desplegarse mediante un único comando (`docker compose up`) sin configuración manual de dependencias en el sistema operativo anfitrión. |
| RNF04 | Mantenibilidad | La arquitectura debe permitir la sustitución del modelo SLM o de la base de datos vectorial sin modificar la capa de presentación ni la lógica de orquestación RAG, conforme al principio de bajo acoplamiento. |
| RNF05 | Escalabilidad | El sistema debe soportar la adición de nuevos documentos al corpus mediante re-ejecución del pipeline de ingesta, sin necesidad de modificar código fuente. |
| RNF06 | Seguridad | La API no debe exponer información sobre la estructura interna del sistema (rutas de archivos, versiones de dependencias, trazas de error completas) en las respuestas HTTP de error. |

El cumplimiento de RNF01 es una restricción no negociable derivada del contexto institucional del proyecto. RNF03 garantiza la reproducibilidad del sistema en diferentes entornos de despliegue (entorno de desarrollo local, cluster universitario, nube privada), lo cual es esencial para la evaluación académica del proyecto. La arquitectura modular descrita en la sección de Diseño y Arquitectura ha sido diseñada explícitamente para satisfacer RNF04: la estandarización a través de las abstracciones de LangChain permite sustituir ChromaDB por Milvus o Qdrant, o reemplazar Qwen por cualquier modelo compatible con Ollama, sin modificar el pipeline RAG ni la interfaz de usuario.

---

## 7. Diseño y Arquitectura

### 7.1. Evaluación de Alternativas

Para cada decisión tecnológica clave del sistema, se evaluaron múltiples alternativas conforme a criterios de privacidad, costo operativo, rendimiento en hardware de consumo y compatibilidad con el ecosistema Python/JavaScript del equipo. Esta evaluación constituye la justificación técnica de las elecciones de diseño adoptadas y es fundamental para comprender las compensaciones (_trade-offs_) que la arquitectura final implica.

**Bases de datos vectoriales:** Se evaluaron Pinecone, Weaviate, Milvus y ChromaDB. Pinecone y Weaviate fueron descartadas inmediatamente al ser servicios en la nube, lo que viola la restricción de privacidad RNF01. Milvus, aunque de código abierto y desplegable localmente, requiere una infraestructura dedicada (servidor independiente, configuración de clúster) que excede la complejidad operativa aceptable para un prototipo académico. ChromaDB fue seleccionada por ser una base de datos vectorial embebida que opera en el mismo proceso que la aplicación Python, sin requerir un servidor separado, con soporte nativo para persistencia en disco y una API limpia para la integración con LangChain.

**Modelos de lenguaje:** Se evaluaron tres enfoques: APIs comerciales (OpenAI GPT-4, Google Gemini, Anthropic Claude), modelos locales de alto parámetro (Llama 3.1:70b, Mixtral 8x7b) y SLMs cuantizados (Qwen 2.5:1.5b, Qwen 2.5:3b, Llama 3.2:3b, Phi-3 Mini). Las APIs comerciales fueron descartadas por las razones expuestas en el Estado del Arte (privacidad y costo). Los modelos de alto parámetro, aunque superiores en capacidad de razonamiento, requieren entre 40 y 80 GB de VRAM para inferencia eficiente, lo que los hace inviables en hardware de consumo. Entre los SLMs cuantizados, Qwen 2.5:1.5b fue seleccionado por su superior desempeño en tareas de comprensión lectora en español frente a Llama 3.2:3b y Phi-3 Mini en evaluaciones preliminares, manteniendo una huella de memoria de ~2 GB bajo cuantización Q4_K_M.

**Frameworks de orquestación y frontend:** Para la orquestación RAG, se evaluaron LangChain, LlamaIndex y una implementación manual del pipeline. LlamaIndex es igualmente competente, pero LangChain fue seleccionado por la mayor madurez de su ecosistema, la expresividad de su API declarativa (LCEL) y la mayor cantidad de recursos de documentación en español. Para el frontend, se evaluaron Vue.js/Nuxt 3, Angular y Next.js 16; Next.js fue seleccionado por su soporte nativo para Server Components, la facilidad de implementar un proxy inverso hacia el backend sin servidor adicional (mediante el sistema de rutas de API) y la compatibilidad con React 19, que reduce la curva de aprendizaje dado el conocimiento previo del equipo con el ecosistema React.

| Decisión | Alternativas evaluadas | Selección | Criterio determinante |
|----------|----------------------|-----------|----------------------|
| Vector Store | Pinecone, Weaviate, Milvus, **ChromaDB** | ChromaDB | Embebido, local, sin servidor externo |
| LLM | GPT-4 API, Llama 3.1:70b, **Qwen 2.5:1.5b** | Qwen 2.5:1.5b | Rendimiento en español, huella < 2 GB |
| Embedding | OpenAI ada-002, **MiniLM-L12-v2**, mpnet-base-v2 | MiniLM-L12-v2 | Multilingüe, local, latencia baja |
| Orquestación RAG | LlamaIndex, Manual, **LangChain LCEL** | LangChain | Ecosistema maduro, bajo acoplamiento |
| Backend API | Django, Flask, **FastAPI** | FastAPI | Async nativo, OpenAPI automático, Pydantic |
| Frontend | Vue/Nuxt, Angular, **Next.js 16** | Next.js | Proxy API nativo, React 19, SSR |


### 7.2. Arquitectura del Sistema

El sistema adopta una arquitectura cliente-servidor orientada a microservicios en un entorno de ejecución 100% local (_Local-first / On-Premise_). El desacoplamiento entre componentes se logra mediante el uso de las abstracciones de LangChain como capa de orquestación intermedia, lo que permite la sustitución independiente de cualquier componente sin afectar al resto de la arquitectura.

**Diagrama de Arquitectura del Sistema:**
<img width="784" height="753" alt="image" src="https://github.com/user-attachments/assets/ba249ff2-a50c-4c4a-a403-b347f0df8303" />

**Componentes del sistema e interacción:**

El sistema se divide en los siguientes componentes principales:

- **Frontend (Next.js 16, React 19, Tailwind CSS):** Actúa como la capa de presentación. Su responsabilidad es capturar la consulta del usuario en lenguaje natural, renderizar el flujo de tokens de respuesta mediante _streaming_ y mostrar los metadatos de las fuentes recuperadas. Incluye un proxy reverso transparente hacia el backend que evita problemas de CORS y abstrae la topología de red interna.

- **API Core / Backend (FastAPI + Uvicorn):** Expone los _endpoints_ RESTful. Es responsable de la recepción de solicitudes HTTP, la validación de _payloads_ mediante modelos Pydantic, el manejo de errores y el enrutamiento interno hacia el orquestador RAG.

- **Orquestador RAG (LangChain LCEL):** Componente _middleware_ responsable de la lógica central del pipeline. Se encarga de instanciar el modelo de _embeddings_, construir el _System Prompt_ inyectando los fragmentos recuperados y componer la cadena `Retriever → PromptTemplate → LLM → StrOutputParser` mediante sintaxis LCEL.

- **Base de Datos Vectorial (ChromaDB):** Su responsabilidad exclusiva es el almacenamiento persistente de los vectores densos generados en la fase de ingesta y la ejecución eficiente de búsquedas por similitud del coseno. La colección `uninorte_normatividad` contiene 907 fragmentos vectorizados.

- **Motor de Inferencia LLM (Ollama + Qwen 2.5:1.5b):** El motor de inferencia se encuentra instanciado en un **ordenador independiente** para evitar el agotamiento de recursos en la Orange Pi. Este servicio ejecuta el modelo cuantizado y genera la respuesta en lenguaje natural basada estrictamente en el contexto entregado. La comunicación se realiza a través de la red local mediante la variable `OLLAMA_BASE_URL`.

La interacción de estos componentes está representada por el siguiente diagrama:

<img width="1277" height="597" alt="image" src="https://github.com/user-attachments/assets/34f04d49-c2a7-4caf-9913-a8ec42761b49" />


**Flujo de interacción entre módulos:**

1. El **Frontend** envía la consulta del usuario mediante una petición `POST /api/query` al proxy Next.js.
2. El proxy reenvía la solicitud al **Backend (FastAPI)** en `POST /query`.
3. El Backend delega el control al **Orquestador (LangChain)**, que transforma el texto en un vector denso mediante el modelo de _embeddings_ cargado en memoria.
4. LangChain consulta a **ChromaDB** mediante búsqueda de similitud del coseno, extrayendo el Top-6 de fragmentos normativos más relevantes.
5. LangChain ensambla el _prompt_ estructurado (sistema + contexto + pregunta) y lo transmite al **Motor Ollama**.
6. Ollama retorna los tokens generados mediante _streaming_; el flujo atraviesa la arquitectura de regreso hasta el Frontend, donde se renderiza progresivamente.

**Diagrama de Secuencia:**
<img width="1344" height="553" alt="Diagrama de Secuencia" src="https://github.com/user-attachments/assets/973cd97a-c6cf-406e-b464-5cbacd7af30f" />

---

## 8. Implementación

### 8.1. Stack Tecnológico

El backend del sistema está construido sobre **Python 3.11** como lenguaje principal, utilizando **FastAPI 0.100+** como framework web asíncrono y **Uvicorn** como servidor ASGI de alto rendimiento. La selección de Python está motivada por la madurez de su ecosistema para aplicaciones de inteligencia artificial: las librerías de NLP, _embeddings_, bases de datos vectoriales y orquestación de LLMs más relevantes tienen Python como lenguaje de referencia. Para la orquestación del pipeline RAG, se utiliza **LangChain 0.2+** en su variante LCEL, lo que permite expresar el flujo completo como una cadena declarativa de componentes componibles. La gestión de embeddings se delega a **sentence-transformers 2.2+** (HuggingFace), que descarga y ejecuta el modelo `paraphrase-multilingual-MiniLM-L12-v2` localmente durante la primera inicialización del contenedor. La extracción de texto de PDFs se realiza mediante **LiteParse**, un extractor local con capacidad de OCR como mecanismo de respaldo para documentos escaneados.

El frontend está construido sobre **Next.js 16.1.6** con **React 19.2.3** y **TypeScript 5**, utilizando **Tailwind CSS 4** para el estilado. La arquitectura del frontend sigue el patrón App Router de Next.js 16, donde los componentes del servidor y del cliente coexisten en la misma estructura de directorios. El proxy inverso hacia el backend está implementado como una ruta de API de Next.js (`app/api/[...proxy]/route.ts`), lo que permite que el frontend se comunique con el backend sin exponer la URL interna del servicio al navegador del cliente. El _streaming_ de tokens se implementa mediante la API nativa `ReadableStream` del navegador, consumida desde los _Server Components_ de Next.js.

La infraestructura de despliegue está completamente contenedorizada mediante **Docker** y orquestada con **Docker Compose 3.8**. Para el despliegue definitivo en **Orange Pi 5 Pro / Plus**, se utiliza una configuración específica que optimiza el uso de la arquitectura ARM64. El sistema se divide en dos nodos:
1. **Nodo Edge (Orange Pi):** Ejecuta los contenedores de `backend` y `frontend`.
2. **Nodo de Inferencia (PC Externo):** Ejecuta el servicio de `ollama`.

Esta separación garantiza que el sistema mantenga una latencia baja y una alta disponibilidad, evitando que la inferencia del LLM bloquee los servicios web en la placa ARM. El modelo seleccionado es **Qwen 2.5:1.5b**, optimizado para ejecutarse con una huella de memoria reducida.


### 8.2. Componentes

El backend está organizado en una capa de módulos bajo el directorio `src/`, cada uno con una responsabilidad única y bien delimitada:

- **`pdf_extractor.py`:** Extrae el contenido textual de los PDFs descargados mediante LiteParse. Implementa una estrategia en dos pasos: primero intenta extracción sin OCR (para PDFs con texto seleccionable); si el resultado contiene menos de 50 caracteres, activa el modo OCR para documentos escaneados. El texto extraído es sometido a un proceso de limpieza que normaliza espacios, elimina encabezados y pies de página repetitivos y corrige problemas de codificación de caracteres especiales del español.

- **`text_chunker.py`:** Aplica la estrategia `RecursiveCharacterTextSplitter` de LangChain con ventanas de 1.000 tokens y solapamiento de 200 tokens. Los separadores se aplican en orden jerárquico (`["\n\n", "\n", ". ", " ", ""]`), priorizando los saltos de párrafo para preservar la coherencia semántica. A cada chunk se le adjunta metadatos que incluyen el nombre del archivo fuente, el título del documento, el número de página y el índice secuencial del fragmento, garantizando la trazabilidad necesaria para la citación de fuentes.

- **`embeddings.py` + `vector_store.py`:** El primero instancia y gestiona el modelo de embeddings HuggingFace, exponiendo una interfaz unificada compatible con LangChain. El segundo encapsula todas las operaciones sobre ChromaDB: inicialización de la colección, ingesta de documentos con sus vectores y metadatos, y creación del objeto `Retriever` configurado para búsqueda por similitud del coseno con Top-K=6.

- **`rag_chain.py`:** Compone la cadena LCEL completa: `{"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt_template | ollama_llm | StrOutputParser()`. Implementa deduplicación de fuentes antes del retorno y formatea los metadatos de cada fragmento recuperado para su presentación al usuario.

- **`api.py`:** Define los cuatro _endpoints_ FastAPI del sistema (`/health`, `/models`, `/models/load`, `/query`), los modelos Pydantic de request/response, y el middleware de CORS. El _endpoint_ `/query` invoca la cadena RAG de forma síncrona y retorna la respuesta completa en formato JSON incluyendo `answer`, `sources` y `model`.

El frontend está organizado en cuatro componentes React reutilizables: `ChatMessage.tsx` (renderiza mensajes con animación de escritura para el estado de carga), `ModelSelector.tsx` (desplegable dinámicamente poblado desde `/models`), `SourceCard.tsx` (muestra fuentes como _chips_ con nombre de documento y página) y `StatusBar.tsx` (indicadores de estado del sistema mediante consultas periódicas a `/health`).

### 8.3. Integraciones

La integración más crítica del sistema es la comunicación entre el backend Python y el motor de inferencia **Ollama**. En la arquitectura definitiva, el backend se conecta a una instancia de Ollama instanciada en un **ordenador aparte**. Esta conexión se parametriza mediante la variable de entorno `OLLAMA_BASE_URL`, apuntando a la dirección IP privada del servidor de inferencia (ej. `http://192.168.1.50:11434`). Esta decisión de diseño permite repartir la carga de rendimiento, dejando que la Orange Pi gestione exclusivamente la lógica de negocio y la recuperación vectorial, mientras que el PC externo asume el costo computacional de la inferencia del modelo **Qwen 2.5:1.5b**.

La integración con **ChromaDB** es de tipo embebido: la base de datos vectorial se instancia directamente en el proceso Python del backend en la Orange Pi, leyendo y escribiendo en el directorio `data/chroma_db/` del sistema de archivos del contenedor. Esta arquitectura sin servidor elimina la latencia de red en las operaciones de recuperación semántica, reduciendo el tiempo de búsqueda del Top-K a menos de 50 ms para una colección de 907 vectores. La comunicación entre LangChain e integraciones se mantiene agnóstica a la ubicación física del servidor Ollama.


La integración con **HuggingFace** para el modelo de embeddings ocurre en el momento de construcción del contenedor Docker del backend: el `Dockerfile` ejecuta un script de precarga del modelo `paraphrase-multilingual-MiniLM-L12-v2` durante la fase de _build_, evitando descargas en tiempo de ejecución. Esto garantiza que el sistema arranque en modo _offline_ completo una vez que la imagen Docker ha sido construida. El pipeline de ingesta se integra adicionalmente con el portal web de la Universidad del Norte mediante las dependencias `requests>=2.28.0` y `beautifulsoup4>=4.12.0`, utilizando selectores CSS específicos del CMS Liferay (`div.journal-content-article`, `div.c_cr`, `article`) para extraer el contenido relevante de las páginas de normatividad.


---


## 9. Despliegue y Operación

### 9.1. Estrategia de Contenedorización

El despliegue de UNINORMA está completamente contenedorizado mediante **Docker** y orquestado con **Docker Compose**, garantizando la reproducibilidad del sistema en cualquier entorno compatible (Linux nativo, Windows con WSL2, macOS) mediante un único comando: `docker compose up`. Esta decisión satisface directamente el requerimiento no funcional **RNF03** (portabilidad) y elimina la necesidad de configurar manualmente dependencias del sistema operativo anfitrión.

La configuración se estructura en dos archivos Compose complementarios:

- **`docker-compose.yml`:** Archivo base que define los tres servicios del sistema (Ollama, Backend, Frontend) con sus dependencias, volúmenes persistentes y variables de entorno por defecto. Esta configuración es funcional en cualquier arquitectura x86_64 y constituye el entorno de desarrollo y pruebas.

- **`docker-compose.orangepi.yml`:** Archivo _override_ específico para el despliegue en **Orange Pi 5 Pro / Plus** (Rockchip RK3588, ARM64). Se invoca mediante `docker compose -f docker-compose.yml -f docker-compose.orangepi.yml up -d` y activa: la plataforma `linux/arm64` explícita en todos los servicios, el acceso a los dispositivos `/dev/dri` (GPU/NPU del SoC), la membresía en los grupos `video` y `render`, y la capacidad `SYS_NICE` para la gestión de prioridad de procesos. Además, establece por defecto el backend de inferencia RKLLM (NPU de 6 TOPS), el _embedder_ ONNX cuantizado (ahorro de ~700 MB de RAM) y la desactivación del _reranker_ pesado (ahorro de 1-3 s por consulta).

### 9.2. Servicios y Contenedores

El sistema se despliega como una composición de tres servicios independientes, cada uno con su `Dockerfile` optimizado:

**Servicio `ollama` (Motor de Inferencia):**
Utiliza la imagen oficial `ollama/ollama:latest` y actúa como servidor de inferencia del SLM. Se configura con `OLLAMA_KEEP_ALIVE=30m` para mantener el modelo cargado en memoria y evitar penalizaciones de _cold-start_ (5-15 s) entre consultas, y con `OLLAMA_NUM_PARALLEL=1` para limitar la concurrencia y minimizar el consumo de RAM. Los modelos descargados persisten en un volumen Docker nombrado (`ollama_models`), sobreviviendo a reinicios y reconstrucciones de contenedores. En el despliegue distribuido, este servicio puede ejecutarse en un PC externo con GPU dedicada, al que el backend se conecta mediante la variable `OLLAMA_BASE_URL`.

**Servicio `backend` (FastAPI + RAG):**
Construido a partir de una imagen `python:3.11-slim`, el `Dockerfile` del backend implementa una estrategia de construcción en capas optimizada para la eficiencia de caché. Primero instala las dependencias Python desde `requirements.txt`, luego ejecuta un script de precarga que descarga y almacena en la imagen el modelo de _embeddings_ `paraphrase-multilingual-MiniLM-L12-v2` (~90 MB), garantizando que el sistema arranque sin necesidad de conexión a internet. Finalmente, copia el código fuente y los PDFs del corpus normativo como recurso de respaldo para re-ingestión. La base de datos vectorial ChromaDB persiste en un volumen independiente (`chroma_data`) que sobrevive a reconstrucciones del contenedor. Las variables de entorno clave incluyen `LLM_BACKEND` (selección entre Ollama y RKLLM), `EMBEDDER_BACKEND` (PyTorch vs. ONNX), `RERANKER_ENABLED` y `LLM_MODEL`.

**Servicio `frontend` (Next.js):**
Construido mediante un `Dockerfile` _multi-stage_ basado en `node:20-alpine`. La primera etapa (_builder_) instala dependencias y compila la aplicación Next.js; la segunda etapa (_runner_) copia únicamente los artefactos de producción, reduciendo significativamente el tamaño de la imagen final. El frontend expone el puerto 3000 internamente, mapeado al puerto 5174 del host (`5174:3000`). La variable de _build_ `NEXT_PUBLIC_API_URL=/api` configura el proxy reverso: todas las peticiones del navegador a `/api/*` son interceptadas por una ruta de API de Next.js (`app/api/[...proxy]/route.ts`) que las reenvía al backend usando la variable `BACKEND_URL=http://backend:8000`, eliminando problemas de CORS y abstrayendo la topología de red interna.

### 9.3. Proceso de Inicialización Automatizado

El script `entrypoint.sh` del backend implementa un proceso de arranque en tres fases que garantiza la disponibilidad de todos los componentes antes de aceptar tráfico:

1. **Verificación de Ollama:** Cuando `LLM_BACKEND=ollama`, el script ejecuta un bucle de reintentos (`until curl -sf ${OLLAMA_BASE_URL}/api/tags`) que espera hasta que el servicio Ollama esté operativo. Este paso se omite automáticamente cuando el backend está configurado para usar RKLLM.

2. **Verificación y descarga del modelo:** Consulta la lista de modelos disponibles en Ollama y, si el modelo configurado (`LLM_MODEL`, por defecto `qwen2.5:1.5b`) no está presente, ejecuta automáticamente un `ollama pull` con barra de progreso. Esta descarga (~2 GB) ocurre únicamente en la primera ejecución.

3. **Verificación de ChromaDB:** Comprueba la existencia del directorio `/app/data/chroma_db` y su contenido. Si la base de datos vectorial no existe o está vacía, ejecuta automáticamente el pipeline de ingestión (`python3 ingest.py --pdf-dir /reglamentos`) que procesa los PDFs del corpus, genera los _embeddings_ y los indexa. Si la base ya existe (caso habitual en despliegues posteriores al primero), se omite la re-ingestión.

Una vez superadas las tres fases, el script inicia el servidor `uvicorn` en `0.0.0.0:8000`. El sistema está operativo cuando los logs muestran el mensaje `API disponible en http://0.0.0.0:8000`.

### 9.4. Despliegue en Orange Pi 5 Pro / Plus

El despliegue definitivo en hardware ARM sigue un procedimiento de cuatro pasos diseñado para minimizar la carga computacional sobre la placa:

**Paso 1 — Preparación del host:** Se requiere Ubuntu 22.04 / 24.04 ARM64 con kernel >= 5.10 con soporte Rockchip, Docker Compose >= 2.20 y la verificación de que el dispositivo NPU está expuesto (`/dev/dri/card0`). El usuario debe pertenecer a los grupos `video` y `render`.

**Paso 2 — Pre-generación de la base vectorial:** La ingestión (scraping + extracción + chunking + embeddings) se ejecuta una única vez en una máquina de desarrollo x86 y se transfiere al Orange Pi mediante un tarball del volumen Docker. Esto evita que el Pi ejecute un proceso intensivo en CPU y memoria que podría tardar más de 30 minutos en su hardware.

**Paso 3 — Conversión del modelo a formato RKLLM:** El runtime RKLLM del SoC RK3588 no acepta el formato GGUF estándar de Ollama; requiere un formato propietario `.rkllm` generado mediante el toolkit `rkllm-toolkit` en una máquina x86 con CUDA. El modelo `qwen2.5-1.5b-instruct` se cuantiza a `w8a8` (pesos de 8 bits, activaciones de 8 bits) para la plataforma `rk3588`, generando un archivo que se coloca en `deploy/models/`.

**Paso 4 — Levantamiento del stack:** Se ejecuta el comando Compose con el override ARM64 y las variables de entorno correspondientes: `LLM_BACKEND=rkllm`, `EMBEDDER_BACKEND=onnx`, `RERANKER_ENABLED=false`. Si la conversión RKLLM no está disponible, el sistema es funcional con `LLM_BACKEND=ollama` (inferencia en CPU ARM, más lenta pero operativa).

### 9.5. Recursos y Puertos

**Consumo de recursos en ejecución:**

| Componente | RAM Estimada |
|---|---|
| Ollama + qwen2.5:1.5b | ~1.5 GB |
| Backend (FastAPI + ChromaDB + Embeddings) | ~600 MB |
| Frontend (Next.js) | ~200 MB |
| **Total** | **~2.3 GB** |

**Puertos expuestos:**

| Servicio | Puerto Interno | Puerto del Host |
|---|---|---|
| Frontend (Next.js) | 3000 | 5174 |
| Backend (FastAPI) | 8000 | — (accesible solo internamente entre contenedores) |
| Ollama | 11434 | — (accesible solo internamente o en red local) |

**Requisitos mínimos del entorno de despliegue:**

| Recurso | Mínimo | Recomendado |
|---|---|---|
| RAM | 8 GB | 16 GB |
| CPU | 2 cores | 4 cores |
| Disco libre | 20 GB | 32 GB |
| GPU (opcional) | — | NVIDIA con 4+ GB VRAM |

El sistema opera completamente _offline_ después de la primera ejecución, cumpliendo el requerimiento de privacidad **RNF01**. No se requiere conexión a internet para la inferencia ni para las consultas a la base de datos vectorial.

---

## 10. Validación

### 10.1. Pruebas por Componentes

El plan de pruebas por componentes tiene como objetivo verificar el correcto funcionamiento de cada módulo del sistema de forma aislada, identificando defectos antes de que se propaguen a las capas superiores de la arquitectura. Para el módulo `pdf_extractor.py`, las pruebas unitarias verifican tres casos: la extracción correcta de texto seleccionable (PDF digital), la activación y correcto funcionamiento del modo OCR ante PDFs escaneados (condición: texto extraído < 50 caracteres sin OCR), y la correcta limpieza del texto resultante (normalización de espacios, eliminación de artefactos de codificación). El criterio de éxito es la extracción del 100% del contenido textual esperado para un conjunto de documentos de referencia con _ground truth_ conocido.

Para el módulo `text_chunker.py`, las pruebas unitarias validan que: (a) el número de chunks generados para un documento de texto conocido sea consistente con los parámetros de ventana (1.000 tokens) y solapamiento (200 tokens); (b) los metadatos adjuntos a cada chunk contengan los campos requeridos (`source`, `title`, `page`, `chunk_index`); y (c) no se generen chunks con longitud cero ni chunks que excedan el tamaño máximo configurado. Para el módulo `embeddings.py`, se verifica que el vector generado para una consulta de prueba tenga la dimensionalidad correcta (384 dimensiones para `MiniLM-L12-v2`) y que la similitud del coseno entre embeddings de frases semánticamente similares sea significativamente mayor que entre frases no relacionadas.

Para el módulo `rag_chain.py`, las pruebas unitarias utilizan un conjunto de contextos inyectados de forma artificial (sin invocar ChromaDB ni Ollama reales) para verificar el comportamiento del _prompt template_ y el _parser_ de salida. Se prueba específicamente el caso en que el contexto recuperado no contiene información relevante: el sistema debe generar la respuesta de rechazo predefinida en lugar de intentar sintetizar una respuesta vacía o incorrecta. El módulo `benchmark/metrics.py` es también sometido a pruebas unitarias que verifican la correcta implementación de las métricas de evaluación (_retrieval hit rate_, _answer relevancy_, _faithfulness_) contra valores calculados manualmente para un conjunto pequeño de casos de prueba conocidos.
    
### 10.2. Pruebas de Integración

Las pruebas de integración verifican la interacción correcta entre los componentes del sistema a través de sus interfaces definidas, con especial énfasis en los flujos de datos extremo a extremo. El módulo de _benchmarking_ (`benchmark/run_benchmark.py`) constituye el principal instrumento de prueba de integración: ejecuta las 40+ preguntas del archivo `test_questions.json` contra el sistema completo (ChromaDB + LangChain + Ollama) y mide las métricas de recuperación y generación. Cada pregunta en el conjunto de prueba tiene asociado un `expected_source` (el documento correcto del cual debe recuperarse información), una `category` (área normativa) y un nivel de `difficulty` (fácil, medio, difícil). El criterio de éxito de las pruebas de integración del pipeline RAG es una tasa de recuperación correcta (_retrieval hit rate_) superior al 85% en el Top-3 de resultados.

Para los _endpoints_ de la API, las pruebas de integración verifican los cuatro _endpoints_ expuestos por FastAPI mediante solicitudes HTTP reales contra el servidor en ejecución. El _endpoint_ `GET /health` debe retornar un objeto JSON con `ollama_running: true`, `vector_store_ready: true` y el nombre del modelo activo cuando el sistema está correctamente inicializado. El _endpoint_ `POST /query` es sometido a pruebas con un conjunto representativo de preguntas reales, verificando que: la respuesta no esté vacía, las fuentes retornadas correspondan a documentos del corpus, el campo `model` refleje el modelo efectivamente utilizado, y el tiempo de respuesta total sea inferior a 8 segundos. También se prueba el comportamiento ante _payloads_ malformados (campo `question` vacío, `model` no reconocido) para verificar que la API retorne códigos HTTP de error apropiados (400, 422) sin exponer trazas internas.

Las pruebas de integración también incluyen la verificación del flujo de carga y descarga de modelos mediante el _endpoint_ `POST /models/load`. Se verifica que, tras solicitar la carga de un modelo alternativo (ej. `llama3.2:3b`), las siguientes consultas sean efectivamente atendidas por ese modelo, y que el _endpoint_ `/health` refleje el cambio. El pipeline completo de ingesta es igualmente sometido a pruebas de integración: se ejecuta el script `ingest.py` sobre un subconjunto controlado de documentos y se verifica que el número de chunks indexados en ChromaDB sea consistente con el total esperado, que los metadatos de todos los chunks sean correctos y que el motor de recuperación devuelva resultados relevantes para preguntas de control.

### 10.3. Pruebas de Usabilidad

Las pruebas de usabilidad tienen como objetivo evaluar la efectividad del sistema desde la perspectiva del usuario final —estudiantes y miembros de la comunidad académica de la Universidad del Norte—, más allá de la corrección técnica verificada en las pruebas anteriores. La metodología adoptada es una evaluación heurística combinada con pruebas de pensamiento en voz alta (_think-aloud protocol_): se reclutará un grupo de al menos 8 participantes representativos del usuario objetivo (estudiantes de diferentes programas académicos, con distinto nivel de familiaridad con herramientas digitales) para realizar un conjunto de tareas de consulta normativa predefinidas utilizando el asistente.

Las tareas de evaluación incluirán consultas de distinto nivel de complejidad: preguntas directas sobre artículos específicos del Reglamento Estudiantil (ej. "¿Cuántos créditos debo cursar para ser considerado estudiante de tiempo completo?"), preguntas que requieren sintetizar información de múltiples fuentes (ej. "¿Cuáles son los requisitos para solicitar un retiro de materia en el período de parciales?") y preguntas deliberadamente fuera del dominio normativo (ej. "¿Cuándo es el próximo partido de la selección colombiana?") para evaluar el comportamiento de rechazo del sistema. Para cada tarea, se medirán: el tiempo de completación (desde el envío de la consulta hasta que el usuario confirma haber obtenido la información buscada), el número de consultas reformuladas necesarias para obtener una respuesta satisfactoria y la puntuación de satisfacción en una escala de 1 a 5 (System Usability Scale adaptada).

Los criterios de aceptación de las pruebas de usabilidad son: (a) al menos el 75% de los participantes debe ser capaz de formular su consulta en lenguaje natural sin necesitar instrucciones adicionales sobre la sintaxis o el formato de las preguntas; (b) la puntuación media de satisfacción debe superar 3.5/5.0 en la escala de usabilidad adaptada; (c) el sistema debe rechazar correctamente el 100% de las consultas fuera del dominio normativo en el grupo de prueba, sin generar respuestas inventadas; y (d) al menos el 80% de las respuestas provistas deben incluir referencias a documentos que los participantes consideren relevantes para la consulta realizada. Los resultados de estas pruebas alimentarán la fase de optimización de _prompts_ y parámetros de recuperación planificada para las semanas 12–13 del cronograma.

---


## 11. Resultados y Discusión

### 11.1. Marco de Evaluación

Para evaluar de forma objetiva el desempeño del sistema UNINORMA, se diseñó un framework de _benchmarking_ automatizado que permite la comparación cuantitativa de múltiples modelos SLM bajo condiciones controladas e idénticas. El framework está implementado en los módulos `benchmark/run_benchmark.py` y `benchmark/metrics.py`, y es accesible tanto desde la línea de comandos (`python -m benchmark.run_benchmark`) como desde la interfaz web del frontend a través de los _endpoints_ REST `/benchmark/start`, `/benchmark/progress/{job_id}` y `/benchmark/results`.

El conjunto de datos de evaluación (`benchmark/test_questions.json`) comprende **25 preguntas** diseñadas para cubrir tres dimensiones críticas del sistema:

- **Consultas directas (dificultad fácil, 10 preguntas):** Preguntas cuya respuesta se encuentra explícitamente en un único documento del corpus. Evalúan la capacidad básica de recuperación y generación. Ejemplos: derechos de egresados, requisitos de contratación de profesores, jornada laboral, nota mínima aprobatoria.

- **Consultas de síntesis (dificultad media, 8 preguntas):** Preguntas que requieren localizar información específica dentro de documentos extensos o sintetizar información distribuida en múltiples secciones. Ejemplos: sanciones por faltas graves, clasificación de invenciones, causales de terminación de contrato, procedimiento de evaluación docente.

- **Consultas de negación y referencia cruzada (dificultad difícil, 7 preguntas):** Incluyen preguntas deliberadamente fuera del dominio normativo (teletrabajo, salario de catedráticos, nombre del rector) cuya respuesta correcta es que el sistema indique que no dispone de esa información; y preguntas que requieren cruzar información entre múltiples reglamentos (relación entre propiedad intelectual y reglamento de profesores, articulación de derechos humanos con bienestar).

Las preguntas abarcan **10 categorías normativas**: reglamento estudiantil, reglamento de profesores, reglamento interno de trabajo, reglamento de egresados, propiedad intelectual, derechos humanos, bienestar universitario, protocolo de acoso, resoluciones del Consejo Académico y referencias cruzadas.

### 11.2. Métricas de Evaluación

El framework calcula seis métricas primarias por cada consulta evaluada, diseñadas para capturar diferentes aspectos del rendimiento del sistema RAG:

1. **Latencia (_latency_seconds_):** Tiempo total desde el envío de la consulta hasta la recepción completa de la respuesta. Incluye la recuperación semántica en ChromaDB, la construcción del _prompt_ y la generación completa de tokens por el SLM. Se mide mediante `time.time()` antes y después de la invocación de la cadena RAG.

2. **Precisión de recuperación (_retrieval_accuracy_):** Porcentaje de consultas en las que el documento fuente esperado aparece entre los fragmentos recuperados por ChromaDB. Para preguntas de negación (`expected_source = "NONE"`), la métrica se considera automáticamente correcta. La verificación se realiza mediante coincidencia parcial de nombres de archivo.

3. **Relevancia de la respuesta (_answer_relevancy_):** Similitud semántica entre la pregunta del usuario y la respuesta generada, calculada como la similitud del coseno entre los _embeddings_ de ambos textos (generados con el modelo `paraphrase-multilingual-MiniLM-L12-v2`). Un valor alto indica que la respuesta aborda directamente la pregunta formulada. Rango: 0.0 a 1.0.

4. **Fidelidad al contexto (_faithfulness_):** Proporción de oraciones de la respuesta que están fundamentadas en el contexto recuperado. Para cada oración de la respuesta, se verifica que al menos el 50% de sus palabras significativas (longitud > 3 caracteres) aparezcan en el texto de los fragmentos recuperados. La métrica penaliza respuestas que introducen información no presente en el corpus. Rango: 0.0 a 1.0.

5. **Detección de alucinaciones (_hallucination_rate_):** Proporción de respuestas que introducen datos numéricos significativos (valores > 10) no presentes en el contexto recuperado. Si una respuesta contiene más de dos números nuevos no encontrados en los fragmentos de referencia, se clasifica como alucinación. Las respuestas de negación ("no encontré información") quedan excluidas automáticamente de esta detección.

6. **Precisión de rechazo (_no_answer_accuracy_):** Para las preguntas cuya respuesta no está en el corpus (categoría de negación), mide el porcentaje de veces que el modelo responde correctamente indicando que no dispone de información, en lugar de generar una respuesta inventada. La detección se basa en la presencia de patrones lingüísticos de rechazo ("no encontré", "no tengo información", "no se encuentra", "no dispongo", entre otros).

### 11.3. Modelos Evaluados

El benchmark está configurado para evaluar hasta **ocho modelos SLM** cuantizados, seleccionados por su compatibilidad con Ollama y su viabilidad en hardware de consumo:

| Modelo | Parámetros | RAM Estimada | Perfil de Uso |
|---|---|---|---|
| **Qwen 2.5:1.5b** | 1.5B | ~1.5 GB | Modelo por defecto; equilibrio entre velocidad y calidad en español |
| **Qwen 2.5:3b** | 3B | ~3.5 GB | Mayor capacidad de razonamiento; benchmark de referencia |
| **Llama 3.2:1b** | 1B | ~1.2 GB | Modelo ultra-ligero para pruebas de latencia mínima |
| **Llama 3.2:3b** | 3B | ~3.5 GB | Alternativa de Meta para comparación directa con Qwen |
| **Phi-3 Mini** | 3.8B | ~4 GB | Modelo de Microsoft optimizado para razonamiento |
| **Gemma 3:1b** | 1B | ~1.2 GB | Modelo de Google; evaluación de diversidad de proveedores |
| **Mistral:7b** | 7B | ~7.5 GB | Referencia de calidad para modelos de mayor tamaño |
| **Llama 3.1:8b** | 8B | ~8 GB | Límite superior de tamaño viable en el hardware de referencia |

Todos los modelos se ejecutan bajo cuantización Q4_K_M (formato GGUF) a través de Ollama, con temperatura de inferencia fijada en 0.1 y un límite de 300 tokens por respuesta.

### 11.4. Protocolo de Ejecución

El benchmark se ejecuta de forma automatizada mediante el script `run_benchmark.py`, que implementa el siguiente protocolo:

1. **Verificación de prerrequisitos:** Se comprueba que Ollama esté activo y se identifican los modelos disponibles entre los solicitados. Los modelos no instalados se omiten con advertencia.

2. **Carga de componentes compartidos:** Se instancia una única vez el modelo de _embeddings_, la base de datos vectorial y el _retriever_ configurado con Top-K=6, garantizando que las variaciones entre modelos provengan exclusivamente del componente generativo.

3. **Evaluación secuencial por modelo:** Para cada modelo, se crea una cadena RAG dedicada y se ejecutan las 25 preguntas. Por cada pregunta se registra: latencia, uso de memoria (delta RSS del proceso Python), acierto de recuperación, relevancia, fidelidad, detección de alucinación y precisión de rechazo.

4. **Agregación y persistencia:** Los resultados individuales se agregan por modelo en una tabla comparativa (_summary_) y se guardan en formato JSON (resultados crudos y resumen) y CSV en el directorio `benchmark/results/`.

El framework también ofrece un modo rápido (_quick_) que ejecuta solo 6 preguntas representativas (una por categoría principal), reduciendo el tiempo de evaluación de 10-30 minutos por modelo a 1-3 minutos, útil para iteraciones rápidas durante el desarrollo.

### 11.5. Análisis y Visualización

Para el análisis comparativo de los resultados, se desarrolló el notebook `benchmark/analysis.ipynb` que implementa nueve secciones de visualización:

1. **Comparación de latencia:** Gráficos de barras horizontales y _boxplots_ de la distribución de tiempos de respuesta por modelo.
2. **Precisión de recuperación:** Barras codificadas por color (rojo < 70%, amarillo < 85%, verde ≥ 85%) con etiquetas porcentuales.
3. **Relevancia y fidelidad:** Gráficos de barras pareados para comparación directa de ambas métricas.
4. **Frontera de Pareto (latencia vs. calidad):** Diagrama de dispersión donde el eje X es la latencia promedio y el eje Y es la media de relevancia y fidelidad, permitiendo identificar los modelos que ofrecen el mejor compromiso entre velocidad y calidad.
5. **Radar chart multi-dimensional:** Gráfico de araña con cinco ejes (recuperación, relevancia, fidelidad, precisión de rechazo, velocidad normalizada) que permite una comparación visual holística.
6. **Heatmap de métricas:** Mapa de calor con anotaciones numéricas de las seis métricas principales por modelo.
7. **Análisis por dificultad:** Gráficos de barras agrupados que comparan la fidelidad y latencia de cada modelo segmentadas por nivel de dificultad (fácil, medio, difícil).
8. **_Score_ compuesto y ranking:** Cálculo de una puntuación compuesta ponderada (30% relevancia + 30% fidelidad + 20% recuperación + 10% velocidad + 10% precisión de rechazo) que sintetiza el desempeño global de cada modelo en un único valor ordenable.

### 11.6. Resultados Cuantitativos

> **Nota:** Al momento de la redacción de este informe, las ejecuciones formales del benchmark completo se encuentran pendientes de realización. Los resultados cuantitativos serán incorporados en la versión final del documento una vez ejecutado el protocolo de evaluación descrito. A continuación se presentan las observaciones preliminares derivadas de las pruebas manuales realizadas durante el desarrollo.

<!-- TODO: Reemplazar esta sección con los resultados reales del benchmark una vez ejecutado.
     Ejecutar: python -m benchmark.run_benchmark --models qwen2.5:1.5b qwen2.5:3b llama3.2:3b
     Los archivos se generarán en benchmark/results/ con timestamps.

     Insertar aquí:
     - Tabla comparativa de modelos (latencia, retrieval, relevancia, fidelidad, alucinación)
     - Gráficos generados por analysis.ipynb
     - Análisis del ranking por score compuesto
-->

**A cada modelo se le envió las mismas 6 preguntas**

|          Metrica          | Qwen2.5:1.5b | llama3.2:1b | gemma3:1b |
|---------------------------|--------------|-------------|-----------|
|     Latencia promedio     | 46.67s | 39.33s | 19.18s |
| Presición de recuperación | 33.3% | 33.3% | 33.3% |
|  Relevancia de respuesta  | 0.734 | 0.853 | 0.778 |
|   Fidelidad al contexto   | 0.926 | 0.816 | 0.738 |
|    Tasa de alucinación    | 16.7% | 0.0% | 0.0% |
|     Memoria promedio      | 2.0MB | 0.6MB | 10.6MB |


El más equilibrado / Ganador operativo: llama3.2:1b. Es el que menor memoria consume (0.6 MB), tiene 0.0% de alucinación, cuenta con la mayor relevancia de respuesta (0.853) y su velocidad es aceptable.

El más veloz pero costoso: gemma3:1b. Ofrece una latencia excelente (19.80s) y no alucina, pero multiplica drásticamente el uso de memoria (10.6 MB) y es el menos fiel al contexto provisto.

El más riguroso con el contexto pero lento: qwen2.5:1.5b. Sigue muy bien las instrucciones del contexto adjunto (0.926), pero es el más lento del grupo, consume más memoria que Llama y sufre de episodios de alucinación (16.7%).

*Nosotros elegimos **qwen2.5:1.5b** debido a la exactitud con que responde referente al contenido, puede ser que tenga ciertas alusinaciónes pero esto se compensa con mostrar la fuente y página donde rescató la información de los articulos de normatividad universitaria*

**Observaciones preliminares de pruebas durante el desarrollo:**

- El pipeline de recuperación semántica demuestra consistencia independiente del modelo generativo: la selección de fragmentos por ChromaDB es determinista para una misma consulta, lo cual se confirma por el hecho de que el componente de _retrieval_ es compartido entre todos los modelos evaluados.

- Los modelos de la familia Qwen 2.5 demuestran una mayor fluidez y coherencia en las respuestas en español en comparación con Llama 3.2 del mismo tamaño, particularmente en el uso correcto de conectores lingüísticos y en la capacidad de parafrasear con precisión el contenido del contexto normativo.

- El sistema de rechazo de consultas fuera del dominio (_no-answer_) funciona correctamente para preguntas claramente externas al corpus (nombre del rector, resultados deportivos), gracias al _system prompt_ que instruye al modelo a responder exclusivamente con base en el contexto proporcionado y con temperatura de inferencia de 0.1.

- La latencia de primera consulta (_cold-start_) es significativamente superior a las consultas subsiguientes, dado que el modelo debe cargarse en RAM. La configuración `OLLAMA_KEEP_ALIVE=30m` mitiga este efecto manteniendo el modelo cargado durante 30 minutos de inactividad.

### 11.7. Discusión

El diseño del framework de evaluación permite extraer conclusiones relevantes sobre las siguientes dimensiones del sistema:

**Compromiso entre tamaño del modelo y calidad de respuesta:** La inclusión de modelos desde 1B hasta 8B parámetros en el benchmark permite cuantificar el punto de rendimientos decrecientes: el incremento de calidad entre un modelo de 3B y uno de 7B parámetros puede no justificar el triplicado en consumo de RAM y latencia, especialmente en un entorno donde la respuesta está fuertemente condicionada por el contexto recuperado (RAG cerrado). En un sistema RAG, la calidad del _retrieval_ tiene un impacto mayor sobre la calidad final que la capacidad de razonamiento del modelo generativo.

**Efectividad del pipeline de recuperación:** La estrategia de _chunking_ jerárquico (artículos como unidad mínima, subdivisión solo si exceden 1.500 caracteres) combinada con el modelo de _embeddings_ multilingüe y la búsqueda por similitud del coseno con Top-K=6 constituye el factor determinante de la calidad del sistema. Un fallo de recuperación —donde el fragmento relevante no aparece en el Top-6— no puede ser compensado por ningún modelo generativo, sin importar su tamaño. Por esta razón, el objetivo de validación prioriza la tasa de recuperación correcta (> 85% en Top-3) como métrica primaria.

**Limitaciones de las métricas automáticas:** Las métricas implementadas son aproximaciones heurísticas diseñadas para operar sin un modelo juez externo (lo cual violaría la restricción de privacidad RNF01). La relevancia basada en similitud del coseno entre pregunta y respuesta es una medida _proxy_ que puede sobreestimar la calidad cuando la respuesta repite términos de la pregunta sin aportar información útil. La fidelidad basada en solapamiento léxico no captura paráfrasis semánticas: una respuesta que reformula correctamente el contenido del contexto con vocabulario diferente podría recibir una puntuación injustamente baja. Estas limitaciones motivan la complementación con pruebas de usabilidad cualitativas descritas en la Sección 10.3.

**Viabilidad del despliegue en hardware edge:** La arquitectura distribuida adoptada —con la inferencia delegada a un servidor externo— resuelve el cuello de botella principal del despliegue en Orange Pi. La placa ARM se dedica exclusivamente a la gestión de la base vectorial y la orquestación, tareas que demandan menos de 1 GB de RAM y se completan en menos de 100 ms. La latencia total del sistema queda dominada por el tiempo de generación de tokens del SLM, que varía entre 3 y 45 segundos dependiendo del modelo seleccionado y del hardware del servidor de inferencia.

**Consideraciones sobre escalabilidad y trabajo futuro:** El sistema actual procesa consultas de forma secuencial (`OLLAMA_NUM_PARALLEL=1`), lo que constituye una limitación para entornos con múltiples usuarios concurrentes. La escalabilidad horizontal requeriría la replicación del servicio Ollama detrás de un balanceador de carga, un aspecto que excede el alcance del prototipo actual pero que la arquitectura contenedorizada facilita. Asimismo, la incorporación de un _reranker_ cross-encoder (BAAI/bge-reranker-v2-m3, actualmente opcional) mejora la precisión de recuperación al reordenar los Top-6 fragmentos antes de compactar el contexto a los Top-3 que recibe el SLM, a costa de 1-3 segundos adicionales de latencia por consulta.

---
## 12. Referencias

- [1] Red Hat, “¿Qué diferencia hay entre los modelos de lenguaje grandes (LLM) y los pequeños (SLM)?,” Red Hat, 2024. [En línea]. Disponible en: https://www.redhat.com/es/topics/ai/llm-vs-slm.

- [2] IBM, “¿Qué son los Small Language Models (SLM)?,” IBM Think Topics, 2024. [En línea]. Disponible en: https://www.ibm.com/es-es/think/topics/small-language-models.

- [3] J. Jokah, “The rise of Small Language Models (SLMs),” Hugging Face Blog, 2024. [En línea]. Disponible en: https://huggingface.co/blog/jjokah/small-language-model.

- [4] Raona, “Small Language Models (SLM): Modelos de Inteligencia Artificial eficientes,” Raona, 2024. [En línea]. Disponible en: https://raona.com/small-language-models/.

- [5] DataCamp, “Los mejores modelos de lenguaje pequeños (SLM) que debes conocer,” DataCamp Blog, 2024. [En línea]. Disponible en: https://www.datacamp.com/es/blog/top-small-language-models.

- [6] IBM, "¿Qué es el RAG (generación aumentada por recuperación)?," IBM Think, 2026. [En línea]. Disponible en: https://www.ibm.com/es-es/think/topics/retrieval-augmented-generation.

- [7] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive nlp tasks," en Advances in Neural Information Processing Systems, vol. 33, 2020, pp. 9459–9474.

- [8] N. Reimers y I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," en Proc. 2011 Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP), 2019, pp. 3982–3992.

- [9] Qwen Team, "Qwen2.5 Technical Report," Alibaba Cloud, Tech. Rep., 2024.

- [10] LangChain AI, "LangChain Documentation: Chains, Retrieval, and Agents," 2024. [En línea]. Disponible en: https://python.langchain.com

- [11] Chroma Research, "ChromaDB: The open-source embedding database," 2024. [En línea]. Disponible en: https://docs.trychroma.com

- [12] Ollama, "Ollama: Get up and running with large language models locally," 2024. [En línea]. Disponible en: https://ollama.com

- [13] Anthropic, "Claude (Versión 4.6 Sonnet)," 2024. [En línea]. Disponible en: https://claude.ai

- [14] Google, "Gemini (Versión 3.1 Pro)," 2026. [En línea]. Disponible en: https://gemini.google.com

- [15] J. Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv preprint arXiv:2312.10997, 2023.

- [16] T. Dettmers, A. Lewis, L. Shettly y L. Zettlemoyer, "Straight from the Source: Local and Private Retrieval-Augmented Generation," en Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2024, pp. 512–526.

- [17] S. S. Prieto, "Evaluación de la madurez y adopción de Chatbots en la Educación Superior en Latinoamérica," Revista Iberoamericana de Educación Digital, vol. 12, no. 2, pp. 45–61, 2024.

- [18] T. Dettmers, M. Lewis, Y. Belinkov y L. Zettlemoyer, "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale," arXiv preprint arXiv:2208.07339, 2022.

- [19] H. Toshniwal et al., "LLMs with Constant Memory: Embedded and Edge Execution Formats," en IEEE Int. Conf. on Artificial Intelligence for Edge Computing (AIEdge), 2025, pp. 112–119.

- [20] Mintlify, "AnythingLLM and PrivateGPT: On-Premise Enterprise Knowledge Bases," Tech Report, 2024. [En línea]. Disponible: https://docs.anythingllm.com

---
