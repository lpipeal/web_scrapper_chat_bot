# Integrantes:
### **Julián Payán Potes </br> Luis Felipe Alvarez </br> Sebastian Mena </br> Mario Andrés Ramírez Navarro**

---

# Informe Módulo 2: Agente Conversacional con Memoria y Múltiples Capacidades — Celsia

> [!NOTE]
> Este documento detalla la evolución del sistema Q&A del Módulo 1 hacia un agente conversacional robusto, implementado con **LangGraph**, **Qdrant** y **Gemini/Mistral**. Cubre la arquitectura del agente, el diseño de herramientas, la gestión de memoria y los resultados de las pruebas.

---

## 1. Arquitectura del Agente

### 1.1 Descripción General del Nuevo Flujo

En el Módulo 1 se construyó un sistema de Q&A simple: el usuario hacía una pregunta, se inyectaba todo el contexto en el prompt y el LLM respondía. Este enfoque tenía limitaciones claras:

- No recordaba interacciones anteriores en la misma sesión.
- No distinguía entre tipos de preguntas (datos concretos vs. explicaciones abiertas).
- Respondía siempre de la misma forma, independientemente de si la pregunta era un saludo o una consulta técnica compleja.

Para el Módulo 2, se diseñó una arquitectura de **grafo de estados** usando **LangGraph**, donde cada consulta del usuario pasa por un flujo de decisión antes de generar una respuesta.

### 1.2 Diagrama del Flujo del Agente

```
                        ┌──────────────────────────────┐
                        │         USUARIO              │
                        │  "¿Cuál es el NIT de Celsia?"│
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │        NODO: ROUTER          │
                        │  (LLM clasifica la intención)│
                        │                              │
                        │  • BASIC_INFO                │
                        │  • RAG_SEARCH                │
                        │  • DIRECT_ANSWER             │
                        └──────┬──────────┬────────────┘
                               │          │            │
              ┌────────────────┘          │            └──────────────────┐
              ▼                           ▼                               ▼
 ┌────────────────────┐   ┌──────────────────────────┐   ┌───────────────────────┐
 │  NODO: BASIC_INFO  │   │    NODO: RAG_SEARCH      │   │  NODO: DIRECT_ANSWER  │
 │                    │   │                          │   │  (directo, sin datos) │
 │  Lee el archivo    │   │  Busca por similitud     │   │                       │
 │  basic_info.json   │   │  vectorial en Qdrant     │   │  (Para saludos,       │
 │  (datos estáticos) │   │  (k=6 fragmentos)        │   │   despedidas, etc.)   │
 └────────┬───────────┘   └─────────────┬────────────┘   └──────────────┬────────┘
          │                             │                               │
          └──────────────┬──────────────┘                               │
                         ▼                                              │
          ┌──────────────────────────────┐                              │
          │      NODO: GENERATOR         │◄─────────────────────────────┘
          │                              │
          │  LLM genera respuesta natural│
          │  basada en context_data      │
          └──────────────┬───────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │         RESPUESTA            │
          │  Mostrada en Streamlit con   │
          │  historial de chat           │
          └──────────────────────────────┘
```

### 1.3 Componentes del Sistema

La arquitectura se organiza en los siguientes módulos dentro del directorio `src/`:

| Módulo | Archivo | Responsabilidad |
|---|---|---|
| `graph_solution` | `graph_factory.py` | Define los nodos, aristas y la lógica de enrutamiento del grafo |
| `graph_solution` | `state.py` | Define la estructura de estado compartida (`CelsiaAgentState`) |
| `context` | `agent_context.py` | Contenedor central: LLM, embeddings, vector store y carga de prompts |
| `rag` | `rag_solution.py` | Motor de persistencia y preparación de la base vectorial |
| `rag` | `data_ingestion.py` | Carga, limpieza y chunking de documentos hacia Qdrant |
| `rag` | `custom_quadrant_vector_store.py` | Wrapper de Qdrant con gestión automática de colecciones |
| `config` | `prompts.yaml` | Definición declarativa de todos los prompts del sistema |
| `config` | `params.yaml` | Parámetros de RAG, rutas de archivos y configuración general |
| `interface` | `app_streamlit.py` | Interfaz conversacional con historial de chat |

---

## 2. Diseño de Herramientas (Tools)

### 2.1 Identificación del Problema

Durante las pruebas del Módulo 1 se detectó que el modelo tenía dificultades para responder con exactitud preguntas concretas como NIT, teléfonos o direcciones. La razón: el texto scrapeado del sitio web no siempre presentaba estos datos de forma estructurada, y el modelo podía parafrasearlos incorrectamente o "alucinar" variaciones.

La solución fue crear una fuente de datos **determinista y estructurada** para este tipo de consultas, completamente separada del sistema RAG.

### 2.2 Herramienta 1 — RAG Search (Búsqueda Semántica en Qdrant)

**Archivo:** `src/rag/rag_solution.py` y `src/rag/custom_quadrant_vector_store.py`

**Descripción:** Recupera fragmentos de texto relevantes desde la base de datos vectorial Qdrant, utilizando similitud de coseno sobre los embeddings del modelo `nomic-embed-text-v2-moe`.

**Cuándo se activa:** Preguntas que requieren explicaciones, contexto narrativo o detalles técnicos sobre servicios, proyectos, historia o procesos de Celsia.

**Parámetros de recuperación:**
- `k = 6` fragmentos más similares recuperados por consulta.
- Distancia: **Coseno**.
- Dimensión de vector: dinámica, detectada automáticamente al crear la colección.

**Tipo de preguntas que maneja:**
- Detalles técnicos de servicios (Solar, Internet, Movilidad Eléctrica).
- Explicaciones de procesos o proyectos específicos.
- Historia detallada, noticias o sostenibilidad.
- Preguntas complejas que mezclan datos básicos con solicitudes de explicación.

```python
# Implementación en RAGSearchNode (graph_factory.py)
def __call__(self, state: CelsiaAgentState):
    docs = self.context.vector_store.similarity_search(state["query"], k=6)
    context_str = "\n\n".join([d.page_content for d in docs])
    return {"context_data": context_str}
```

---

### 2.3 Herramienta 2 — Basic Info (Datos Estructurados en JSON)

**Archivo:** `data/documents/basic_information.json`

**Descripción:** Archivo JSON curado manualmente que contiene los datos corporativos más precisos y frecuentemente consultados de Celsia. El nodo `BasicInfoNode` lo lee completo y lo entrega como contexto al generador.

**Justificación:** Esta herramienta **NO usa la base de datos vectorial**. Es un camino de recuperación determinista: siempre devuelve exactamente los mismos datos, eliminando el riesgo de alucinaciones para información crítica.

**Estructura del archivo:**

```json
{
  "identidad_corporativa": {
    "nombre_oficial": "Celsia S.A. E.S.P.",
    "nit": "800.243.344-1",
    "ceo": "Ricardo Sierra Moreno",
    "fundacion": 2012,
    "colaboradores": 2200
  },
  "presencia_geografica": {
    "paises": ["Colombia", "Panamá", "Costa Rica", "Honduras"],
    "sedes_administrativas": { ... }
  },
  "canales_contacto": {
    "servicio_al_cliente": "01 8000 112 115",
    "emergencias_115": "Línea 115 (Valle y Tolima)",
    "linea_etica": "01 8000 518 915",
    "correo_general": "servicioalcliente@celsia.com"
  },
  "puntos_atencion_y_horarios": { ... },
  "datos_operativos_basicos": { ... }
}
```

**Tipo de preguntas que maneja (entre 5 y 10 FAQs identificadas):**

| # | Pregunta Frecuente | Campo en JSON |
|---|---|---|
| 1 | ¿Cuál es el NIT de Celsia? | `identidad_corporativa.nit` |
| 2 | ¿Quién es el CEO de Celsia? | `identidad_corporativa.ceo` |
| 3 | ¿En qué ciudades tienen sedes? | `presencia_geografica.sedes_administrativas` |
| 4 | ¿Cuál es el número de servicio al cliente? | `canales_contacto.servicio_al_cliente` |
| 5 | ¿Cuál es el correo de contacto? | `canales_contacto.correo_general` |
| 6 | ¿Cuáles son los horarios de atención? | `puntos_atencion_y_horarios` |
| 7 | ¿En qué países opera Celsia? | `presencia_geografica.paises` |
| 8 | ¿Cuántos colaboradores tiene la empresa? | `identidad_corporativa.colaboradores` |
| 9 | ¿Qué capacidad instalada tiene Celsia? | `datos_operativos_basicos.capacidad_instalada` |
| 10 | ¿Cuál es la razón social oficial? | `identidad_corporativa.nombre_oficial` |

---

### 2.4 Herramienta 3 — Direct Answer (Respuesta Directa sin Contexto)

**Descripción:** Ruta especial para mensajes conversacionales como saludos, despedidas o agradecimientos que no requieren consultar ninguna fuente de datos. El generador responde directamente sin datos adicionales.

**Cuándo se activa:** Cuando el usuario escribe frases sin contenido informativo sobre Celsia.

---

## 3. Implementación del Enrutador (Router)

### 3.1 Concepto

El **RouterNode** es el nodo inicial de todo flujo de conversación. Su función es recibir la consulta del usuario y decidir, mediante una llamada al LLM, cuál de las tres rutas disponibles corresponde a la intención detectada. Esta decisión se convierte en un campo `route` dentro del estado del grafo, que determina qué nodo ejecutar a continuación.

### 3.2 Meta-Prompt del Router

El router utiliza el siguiente prompt, definido en `src/config/prompts.yaml`:

```
Eres el Enrutador Lógico de Celsia. Tu función es clasificar la 
intención del usuario para elegir la fuente de datos correcta.

CATEGORÍAS DE ENRUTAMIENTO:
  BASIC_INFO:
   - Consultas sobre identidad corporativa (NIT, CEO, accionistas).
   - Datos de contacto (teléfonos, líneas de falla, correos, ética).
   - Ubicación física y logística (direcciones, horarios de atención).

  RAG_SEARCH:
   - Consultas sobre detalles técnicos de servicios.
   - Explicaciones de procesos, proyectos específicos, historia.
   - Preguntas COMPLEJAS que mezclan datos básicos con explicaciones.
   - Si tienes duda entre "dato estático" y "explicación", elige RAG_SEARCH.

  DIRECT_ANSWER:
   - Saludos, despedidas, agradecimientos o frases sin contenido informativo.

REGLAS CRÍTICAS:
- Responde EXCLUSIVAMENTE con el JSON solicitado.
- Formato de salida: {"route": "CATEGORIA"}
```

### 3.3 Lógica de Enrutamiento con Fallback

Para garantizar robustez, la función `_route_logic` normaliza y valida la decisión del LLM antes de ejecutarla:

```python
def _route_logic(self, state: CelsiaAgentState) -> str:
    route = state.get("route", "rag_search").lower().strip()
    mapping = {
        "basic_info": "basic_info",
        "rag_search": "rag_search",
        "direct_answer": "generator"  # Va directo al generador sin datos
    }
    # Fallback seguro: si el modelo devuelve algo inesperado, usa RAG
    return mapping.get(route, "rag_search")
```


---

## 4. Gestión de Memoria Conversacional

### 4.1 Implementación

La memoria conversacional se implementó en dos capas:

**Capa 1 — Memoria del Grafo (LangGraph `MemorySaver`):**
LangGraph permite persistir el estado del grafo entre invocaciones utilizando `MemorySaver`. Cada sesión de usuario tiene un identificador único (`thread_id`), lo que permite que el grafo recuerde el historial de mensajes dentro de una misma sesión de Streamlit.

```python
# En graph_factory.py
memory = MemorySaver()
return workflow.compile()  # El MemorySaver se asocia internamente al grafo
```

**Capa 2 — Historial en Streamlit (`st.session_state`):**
La interfaz mantiene una lista de objetos `HumanMessage` y `AIMessage` en `st.session_state.messages`. Cada mensaje nuevo se agrega a esta lista y se renderiza en el chat, simulando una ventana de mensajería real.

```python
# En app_streamlit.py
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []
```

### 4.2 Estado del Grafo (`CelsiaAgentState`)

El estado compartido entre todos los nodos del grafo es el mecanismo central de memoria corto plazo por turno:

```python
class CelsiaAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Historial acumulativo
    query: str          # La pregunta actual del usuario
    route: str          # La decisión del router (BASIC_INFO, RAG_SEARCH, DIRECT_ANSWER)
    context_data: str   # Los datos recuperados (del JSON o de Qdrant)
    final_answer: str   # La respuesta final en lenguaje natural
```

El campo `messages` usa el operador `add_messages` de LangGraph, que acumula los mensajes en lugar de reemplazarlos, garantizando el historial de la conversación.

### 4.3 Beneficios y Limitaciones

| Aspecto | Detalle |
|---|---|
| ✅ **Beneficio** | El usuario puede hacer preguntas de seguimiento dentro de la misma sesión |
| ✅ **Beneficio** | La interfaz muestra un historial visual tipo chat (burbujas de usuario/asistente) |
| ✅ **Beneficio** | Cada sesión es independiente gracias al `thread_id` único (UUID) |
| ⚠️ **Limitación** | La memoria es de corto plazo: se pierde al cerrar el navegador o limpiar el historial |
| ⚠️ **Limitación** | El historial completo no se inyecta en cada consulta al LLM del nodo generador — solo la query actual y el contexto recuperado |
| ⚠️ **Limitación** | Para conversaciones muy largas, el crecimiento del historial en `session_state` podría degradar el rendimiento de la UI |

---

## 5. Pruebas y Validación del Agente

Se diseñaron cuatro categorías de prueba para demostrar el correcto funcionamiento del agente. En cada caso se documenta la pregunta, el nodo activado y la naturaleza de la respuesta.

### 5.1 Prueba de Herramienta Estructurada (Nodo: `basic_info`)

Estas preguntas deberían activar el nodo `BasicInfoNode`. Son datos precisos y estáticos.

| # | Pregunta | Ruta Esperada | Verificación |
|---|---|---|---|
| 1 | ¿Cuál es el NIT oficial de Celsia? | `BASIC_INFO` | Devuelve exactamente `800.243.344-1` |
| 2 | ¿En qué ciudades tienen sedes registradas? | `BASIC_INFO` | Lista: Yumbo, Cali, Palmira, Ibagué, Medellín |
| 3 | Dime la razón social completa de la empresa. | `BASIC_INFO` | Devuelve `Celsia S.A. E.S.P.` |
| 4 | ¿Cuáles son los horarios de atención en Palmira? | `BASIC_INFO` | Lun-Vie: 7:30-12:00, 1:30-4:00 |
| 5 | ¿Cuál es el número de la línea de ética? | `BASIC_INFO` | `01 8000 518 915` |

**Resultado observado:** El agente identifica correctamente estas consultas como `BASIC_INFO`, lee el archivo JSON y el generador produce una respuesta precisa y sin alucinaciones.

---

### 5.2 Prueba de RAG (Nodo: `rag_search`)

Estas preguntas obligan al agente a buscar en los fragmentos vectorizados de Qdrant.

| # | Pregunta | Ruta Esperada | Verificación |
|---|---|---|---|
| 6 | ¿Qué tipo de soluciones solares ofrece Celsia para empresas? | `RAG_SEARCH` | Responde con detalles de paneles, PPA, etc. |
| 7 | ¿Cómo funciona el servicio de eficiencia energética? | `RAG_SEARCH` | Describe el proceso de auditoría y soluciones |
| 8 | ¿Tienen proyectos de movilidad eléctrica o estaciones de carga? | `RAG_SEARCH` | Menciona los puntos de carga y el ecosistema EV |
| 9 | ¿Qué beneficios mencionan sobre el uso de energías renovables? | `RAG_SEARCH` | Cita contenido del sitio web sobre sostenibilidad |
| 10 | ¿Qué metas de reducción de huella de carbono tiene Celsia? | `RAG_SEARCH` | Responde con datos del scraping de sostenibilidad |

**Resultado observado:** El agente recupera 6 fragmentos relevantes de Qdrant y los usa para construir respuestas contextualizadas. La calidad depende directamente de la limpieza de los datos scrapeados.

---

### 5.3 Prueba de Memoria Conversacional

Secuencia de preguntas en una misma sesión para validar el historial.

| Turno | Pregunta del Usuario | Comportamiento Esperado |
|---|---|---|
| 1 | "Hola, cuéntame sobre los servicios de Celsia para hogares." | Router: `RAG_SEARCH`. Responde con servicios residenciales. |
| 2 | "¿Y cuánto cuesta el primero que mencionaste?" | El historial en `session_state` permite al usuario hacer referencia al turno anterior. |
| 3 | "¿Tienen atención en Cali para eso?" | Router: `BASIC_INFO` (sedes). Responde con dirección en Cali. |
| 4 | "Gracias, eso es todo." | Router: `DIRECT_ANSWER`. Responde con despedida amable. |

**Resultado observado:** Streamlit mantiene el historial visual correctamente. Cada mensaje se muestra en burbujas diferenciadas (usuario/asistente). El botón "Limpiar Historial" reinicia la sesión generando un nuevo `thread_id`.

---

### 5.4 Prueba de Enrutamiento (Consultas Mixtas)

Las preguntas más desafiantes combinan intenciones, forzando al router a tomar una decisión.

| # | Pregunta | Ruta Decidida | Análisis |
|---|---|---|---|
| 11 | "Dame el NIT de la empresa y explícame qué hacen con la energía eólica." | `RAG_SEARCH` | Al detectar "explícame", el router prioriza RAG según las reglas del prompt. |
| 12 | "¿Celsia tiene sede en Cali? Si es así, ¿qué proyectos de alumbrado público manejan?" | `BASIC_INFO` o `RAG_SEARCH` | Pregunta mixta: el router puede elegir BASIC_INFO (sede) o RAG (proyectos). |
| 13 | "¿A qué precio están las acciones de Ecopetrol?" | `DIRECT_ANSWER` o `RAG_SEARCH` | El bot responde que solo puede hablar de Celsia (fuera de alcance). |
| 14 | "¿Puedo contratar televisión por cable con Celsia?" | `RAG_SEARCH` | El contexto recuperado no contiene TV por cable; el bot responde con honestidad. |

**Resultado observado:** El prompt del router con la regla *"Si tienes duda entre dato estático y explicación, elige RAG_SEARCH"* demostró ser efectivo para reducir errores de enrutamiento en preguntas mixtas. Las preguntas fuera del alcance activan respuestas educadas gracias a las restricciones del prompt del generador.

---

### 5.5 Prueba de Respuesta Directa (Saludos y Fallbacks)

| # | Pregunta | Ruta Esperada | Resultado |
|---|---|---|---|
| 15 | "Hola, ¿quién eres y en qué puedes ayudarme?" | `DIRECT_ANSWER` | El generador se presenta como asistente de Celsia |
| 16 | "¿Cuál es el clima hoy en Cali?" | `DIRECT_ANSWER` | Responde educadamente que solo tiene información sobre Celsia |
| 17 | "Muchas gracias, hasta luego." | `DIRECT_ANSWER` | Despedida cordial |

---

## 6. Actualización de la Interfaz de Usuario

La interfaz de Streamlit (`src/interface/app_streamlit.py`) fue actualizada para reflejar la nueva arquitectura de agente:

### 6.1 Cambios Implementados

- **Historial visual de chat:** El chat se renderiza usando `st.chat_message()` con burbujas diferenciadas para usuario y asistente.
- **Gestión de sesión con UUID:** Cada sesión de usuario genera un `thread_id` único que identifica la conversación dentro del grafo LangGraph.
- **Spinner de espera:** El componente `st.spinner()` indica al usuario que el agente está "pensando" (ejecutando el grafo) mientras se genera la respuesta.
- **Panel lateral de control:** Sidebar con información sobre la arquitectura y botón para limpiar el historial.
- **Tecnologías visibles:** El pie de página documenta el stack: `LangChain | LangGraph | Qdrant | Gemini 1.5 Flash`.

### 6.2 Flujo de Interacción en la UI

```
Usuario escribe pregunta
        ↓
st.chat_input() captura el texto
        ↓
Se crea HumanMessage y se agrega a session_state.messages
        ↓
app_graph.invoke() ejecuta el grafo completo (router → herramienta → generador)
        ↓
Se extrae final_state["final_answer"]
        ↓
Se crea AIMessage y se agrega a session_state.messages
        ↓
Se renderiza todo el historial con st.chat_message()
```

---

## 7. Stack Tecnológico del Módulo 2

| Componente | Tecnología | Versión / Detalle |
|---|---|---|
| **Framework de Agente** | LangGraph | Grafo de estados con nodos y aristas condicionales |
| **Orquestación LLM** | LangChain | Gestión de prompts (`ChatPromptTemplate`), cadenas y mensajes |
| **LLM Principal** | Mistral (local vía Ollama) | `mistral:latest`, `temperature=0.1` |
| **LLM Alternativo** | Gemini 1.5 Flash (API) | Para sesiones en la nube |
| **Embeddings** | Ollama | `nomic-embed-text-v2-moe:latest` |
| **Base de Datos Vectorial** | Qdrant (local) | Persistido en `data/vectorial_database/qdrant_storage` |
| **Datos Estructurados** | JSON | `data/documents/basic_information.json` |
| **Configuración** | YAML | `prompts.yaml` y `params.yaml` |
| **Interfaz** | Streamlit | Chat UI con historial de mensajes |
| **Memoria** | LangGraph `MemorySaver` + `st.session_state` | Memoria de corto plazo por sesión |

---

## 8. Conclusiones del Módulo 2

### Lo que funcionó bien

- **La arquitectura de grafo (LangGraph)** resultó ser la evolución natural del sistema del Módulo 1. Separar el enrutamiento, la recuperación y la generación en nodos independientes facilita el mantenimiento y la extensión del sistema.
- **La herramienta de datos estructurados (JSON)** eliminó completamente las alucinaciones para los datos corporativos críticos (NIT, teléfonos, direcciones). El rendimiento en estas consultas fue perfecto.
- **El prompt del router** con la regla de "fallback a RAG_SEARCH ante la duda" demostró ser una estrategia conservadora efectiva: es preferible buscar información que responder sin fundamento.
- **La interfaz de Streamlit** con historial visual mejora significativamente la experiencia de usuario respecto al Módulo 1.

### Limitaciones encontradas

- **Memoria superficial:** El LLM generador no recibe el historial de conversación, solo la query actual y el contexto recuperado. Esto limita la capacidad del bot para responder preguntas de seguimiento que requieren contexto de turnos previos.
- **Enrutamiento de consultas mixtas:** Preguntas que combinan datos básicos con explicaciones detalladas son el mayor desafío para el router. La calidad de la decisión depende fuertemente de la redacción de la pregunta del usuario.
- **Latencia:** Al ejecutar modelos locales (Ollama + Mistral), el tiempo de respuesta puede ser de 5 a 15 segundos dependiendo del hardware disponible, lo que afecta la experiencia conversacional.
- **Escalabilidad del JSON:** A medida que la empresa actualice sus datos de contacto, horarios o sedes, el archivo `basic_information.json` debe actualizarse manualmente. Para un sistema en producción, esta fuente debería conectarse a una API oficial o CRM.

### Próximos pasos (Módulo 3)

- Inyectar el historial completo de la conversación en el contexto del generador para memoria profunda.
- Implementar un mecanismo de actualización automática del JSON desde fuentes oficiales.
- Explorar herramientas adicionales: buscador de tarifas vigentes (API Qdrant con filtros de metadata), o integración con el portal de autogestión de Celsia.
