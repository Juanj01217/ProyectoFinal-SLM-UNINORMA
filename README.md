# Nombre del Proyecto

## Resumen ejecutivo

### Contexto y Problemática:

La Universidad del Norte cuenta con un vasto corpus normativo (reglamentos estudiantiles, resoluciones, políticas) disperso en cientos de páginas y PDFs. Actualmente, los estudiantes enfrentan dificultades para encontrar respuestas a sus dudas administrativas debido a que los buscadores tradicionales por palabras clave carecen de comprensión semántica. Por otro lado, delegar esta tarea a Modelos de Lenguaje (LLMs) comerciales como ChatGPT es inviable para la institución: expone la privacidad de los datos a terceros, genera costos recurrentes por consulta y corre el riesgo de generar respuestas inventadas ("alucinaciones") sobre temas normativos críticos.

### Solución Propuesta:

Para resolver esta brecha, nace **UNINORMA**, un Asistente Virtual conversacional 100% local (On-Premise) basado en la arquitectura RAG (Generación Aumentada por Recuperación) y Modelos de Lenguaje Pequeños (SLM, específicamente Qwen 2.5:1.5b). En lugar de depender de la nube, el sistema recupera fragmentos exactos de una base de datos vectorial local (ChromaDB) y redacta respuestas precisas basadas estrictamente en la documentación oficial de la universidad.

### Alcance:

El proyecto abarca el ciclo de vida completo del sistema: desde un pipeline automatizado que extrae y procesa los PDFs normativos (incluyendo OCR), pasando por una API orquestada con LangChain y FastAPI, hasta llegar a una interfaz web moderna en Next.js. Todo el sistema está paquetizado en contenedores Docker y optimizado para ejecutarse en hardware de consumo y dispositivos Edge (Orange Pi).

### Valor Aportado:

**UNINORMA** democratiza el acceso a la información institucional, permitiendo a los estudiantes consultar sus deberes y derechos en lenguaje natural. Su principal innovación es garantizar privacidad absoluta (los datos nunca salen de la red local), costo operativo cero por inferencia y mitigación de alucinaciones, ya que cada respuesta generada incluye la cita exacta y la página del documento fuente utilizado.


## Documentación del repositorio

| Documento | Descripción |
|---|---|
| [Informe.md](./Informe.md) | Documento principal del proyecto |
| [Instalación.md](./Instalación.md) | Guía de instalación, desarrollo y despliegue |
| [Desarrollo.md](./Desarrollo.md) | Detalles técnicos del desarrollo |

## Estudiantes

| Nombre | GitHub |
|---|---|
| Nombre Apellido | [@imcarlosmsX](https://github.com/imcarlosmsX) |
| Nombre Apellido | [@jesusdlacrz](https://github.com/jesusdlacrz) |
| Nombre Apellido | [@Juanjo1217](https://github.com/Juanjo1217) |

## Tutores

- Eduardo Zurek Varela
- Augusto Salazar Silva
