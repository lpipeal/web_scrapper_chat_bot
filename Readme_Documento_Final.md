# Integrantes:

### **Julián Payán Potes  </br> Luis Felipe Alvarez  </br> Sebastian Mena  </br> Mario Andrés Ramírez Navarro**


# Plan de Trabajo: Asistente Virtual para Celsia - Módulo 1

Este documento detalla el plan de acción paso a paso para construir la Base de Conocimiento Semántico y el Sistema Q&A para la empresa **Celsia**, cumpliendo con todos los requisitos de la actividad del Módulo 1.

> [!NOTE]
> Como solicitaste, este plan hace un énfasis especial en el primer paso: aprender y aplicar las mejores prácticas actuales de **Web Scraping** para extraer toda la información posible de Celsia.

## Fase 1: Extracción de Datos (Web Scraping de Celsia) 🕷️

El objetivo de esta fase es capturar el texto relevante del sitio web oficial (https://www.celsia.com/) y otras fuentes.

### 1.1 Extracción inicial de URLs
Primero se construyó un método para obtener las URLs desde el sitio web de Celsia. Ese proceso arrancaba desde una URL principal, en este caso el mapa del sitio o una página base de Celsia.

El sistema:

* Recibía una URL inicial.
*   Navegaba por los enlaces encontrados dentro de esa página.
*   Iba recopilando links relacionados.
*   Guardaba las URLs en una lista para luego procesarlas.

### 1.2 Problemas con el bloqueo del sitio
Al principio, el sitio bloqueaba el acceso porque detectaba el scrapping. Para evitarlo, se implementaron varias medidas:

*   Uso de user-agent para simular un navegador real.
*   Uso de browser type y ejecución en modo navegador.
*   Apertura de una ventana de Chrome en lugar de una extracción totalmente automática y silenciosa.
*   Desplazamiento automático hasta el final de la página para que cargara el contenido dinámico.
*   Espera adicional para dejar que terminara de cargar el JavaScript.

Eso permitió que el sitio cargara mejor el contenido y que se pudieran capturar más enlaces sin bloqueo.

## Fase 2: Preprocesamiento y Segmentación (Chunking) 🧹
### 2.1 Resumen del Estado Inicial
La información se consolidó a partir de la  fuentes con naturalezas distintas:

*   **Web Oficial Celsia:** Se extrajeron inicialmente 1200 links de información acerca de la empresa, al procesar esta cantidad de información el resultado del contexto fue muy grande, aproximanamente 52000 lineas, haciendo que el modelo no fuera capaz de procesar todo esto en su ventana de contexto. Por esta razon se dejo implementado solamente la extración del primer nivel de links que fueron 71 URLs, estas igualmente presentaban alto contenido de "ruido" (menús, footers, avisos legales).

### 2.2 Fase de Limpieza y Normalización
Para garantizar la calidad de las respuestas de la IA, se aplicaron tres capas de refinamiento:

1.  **Eliminación de Patrones Repetitivos:** Uso de expresiones regulares (Regex) para purgar frases como *"Acepto términos y condiciones"*, *"Línea de atención"* y avisos de privacidad.
2.  **Normalización de Texto:** Estandarización de caracteres especiales mediante la librería `unidecode` y remoción de saltos de línea huérfanos.
3.  **Deduplicación e Integración:** Filtro de unicidad por URL


### 2.3 Estrategia de Fragmentación / Chunking
Se implementó el algoritmo **RecursiveCharacterTextSplitter** de LangChain con los siguientes parámetros:

| Parámetro | Valor | Justificación Técnica |
| :--- | :--- | :--- |
| **Chunk Size** | 1.000 caracteres | Equilibrio ideal para mantener ideas completas dentro de la ventana de contexto. |
| **Chunk Overlap** | 100 caracteres | Garantiza la continuidad semántica, evitando cortes abruptos en oraciones clave. |
| **Separadores** | `\n\n`, `\n`, `. `, ` ` | Prioriza cortes naturales (párrafos y oraciones) sobre cortes arbitrarios. |


### 2.4 Categorización Semántica
Cada fragmento fue etiquetado para mejorar la relevancia en la búsqueda (RAG):
*   `Blog y Sostenibilidad`
*   `Noticias y Prensa`
*   `Información Regulatoria y Tarifas`
*   `Institucional y Cultura`
*   `Productos y Servicios`
*   **`Datos Financieros y Bursátiles`** (Aportado por el motor Tavily)


### 2.5 Resultados Finales
El proceso generó dos activos de conocimiento:

1.  **`master_context_text.txt`**: Documento maestro de 315kB organizado como texto plano.
2.  **`celsia_chunks_ia.json`**: Estructura de datos con **4.236 fragmentos** únicos, cada uno con su respectiva URL de fuente para garantizar la trazabilidad de las respuestas.

## Fase 3: Construcción del Sistema Q&A y Prompt Engineering 🧠

Teniendo en cuenta los pasos anteriores y la importancia de poder hacer pruebas en varios equipos de computo, se hizo importante haver un trabajo inicial de versionamiento de la data para alimentar la IA.

### 3.1 Tamaños de la base de conocimiento probada

En este trabajo se compararon varias versiones del contenido, teniendo en cuenta que el tamaño de la base obligaba a tener un poder de computo suficiente para poder procesar el archivo completo, esta idea se tomo de las recomendaciones del profesor, las versiones fueron:

*   Una versión pequeña de aproximadamente 2.500 líneas.

*   Una versión intermedia de cerca de 18.000 líneas.

*   Una versión grande de alrededor de 29.000 líneas.

*   Una versión todavía más depurada que bajó a cerca de 11.000 líneas tras aplicar filtros adicionales.

La idea fue encontrar el equilibrio entre:

*   Tener suficiente información.

*   Evitar repeticiones.

*   No sobrecargar el contexto del modelo.

### 3.2 Generación del System Prompt

Teniendo en cuenta que se busca una IA que pueda ser usada para para dar respuesta a las preguntas que puedan ser lanzadas por los usuarios respondiendo como un asistente virtual especializado en la empresa Celsia, se creo un Prompt base en el cual se busco definir el tono de la respuesta, el comportamiento del asistente, la seguridas y otros aspectos que se visualizan en el archivo **Readme_System_Prompt.md** con la siguiente estructura:
* Definicion de rol de la IA.
* Comportamiento general.
* Uso del conocimiento.
* Limites de alcance.
* Seguridad y privacidad.
* Prevención de fraude.
* Manejo de preguntas.
* Casos especiales.
* Objetivo final.

### 3.3 Generación de preguntas

Teniendo en cuenta lo visto en la clase, se busco la creacion de varios tipos de preguntas, preguntas simples, preguntas complejas y preguntas trampa con el fin de validar los lineamientos del asistente virtual, a continuación comparto las preguntas clasificadas:

####Historia e Información Corporativa:
1. ¿Qué es Celsia y en qué países opera?
2. ¿Cuál es el propósito principal o la misión de la empresa?
3. ¿Quién es el actual CEO o líder de Celsia?
4. ¿En qué año se fundó o inició operaciones la compañía?

####Productos y Servicios (Hogares):
5. ¿Cómo puedo solicitar la instalación de internet con Celsia?
6. ¿Qué requisitos necesito para instalar paneles solares en mi casa?
7. ¿Tienen algún programa para revisar el consumo de energía en mi hogar?
8. ¿Cómo puedo pagar mi factura de energía en línea?

#####Soluciones para Pymes y Empresas:
9. ¿Qué soluciones de eficiencia energética ofrecen para pequeñas empresas (Pymes)?
10. ¿Ofrecen auditorías energéticas para fábricas o industrias grandes?
11. Soy dueño de un local, ¿cómo me beneficia cambiarme a la energía solar de Celsia?
12. ¿Qué es el modelo de negocio de "Venta de Energía" o PPA que ofrecen a las empresas?

####Sostenibilidad y Movilidad Eléctrica:
13. ¿Qué metas de reducción de huella de carbono tiene Celsia?
14. ¿Cómo funciona el servicio de estaciones de carga para vehículos eléctricos?
15. ¿Qué proyectos de reforestación o protección ambiental lidera la empresa?
16. ¿Qué porcentaje de su energía proviene de fuentes renovables?

####Atención al Cliente y "Preguntas Trampa" (Para probar alucinaciones):
17. ¿Cuáles son los números de teléfono de atención al cliente en el Valle del Cauca?
18. ¿Dónde están ubicadas las oficinas principales de atención al usuario?
19. [Trampa] ¿A qué precio están vendiendo las acciones de Ecopetrol hoy? (El bot debe decir que no sabe).
20. [Trampa] ¿Puedo comprar un paquete de televisión por cable con Celsia? (El bot debe aclarar que ofrecen internet, no TV por cable, o decir que no tiene info si no está en el texto).

## Fase 4: Desarrollo de la Interfaz Web 🖥️

**Streamlit:** Creamos una interfaz web rápida en Python usando Streamlit aprovechando su capacidad para prototipar, en el realizamos una estructura básica de chatbot, donde encontramos:

  *   Título de Celsia.
  *   Input para que el usuario escriba su pregunta.
  *   Botón de enviar y área de despliegue de la respuesta generada por el LLM.
  *   Area de configuración, para seleccionar operador, modelo, prompt, parámetros, opción de web search.

llegar a esta solución la aplicación tomo varios cambios:

* **En la primera etapa:**
el objetivo fue crear un entorno de pruebas dinámico, por la cual se implemento barra lateral de configuración que permitía modificar el System Prompt en tiempo real; de esta manera poder evaluar cómo diferentes "personalidades" e instrucciones afectaban el comportamiento del modelo (en este caso, usando modelos locales como Gemma).

* **En la segunda etapa:**
se integró la opción de poder alternar entre modelos locales (Ollama) y modelos en la nube (Google Gemini) mediante API Keys, como también un botón para poder cargar archivos (.md o .txt) para introducir un "conocimiento Base" sobre la empresa Celsia, esto permitió realizar pruebas rápidas de Grounding.

* **En la versión final:**
se optó por gestionar el contexto de manera estático en un archivo, debido a que la ventana de contexto era muy grande y para darle majo a ese gran volumen de información recolectado se implementó una técnica de Chunking, optimizando la recuperación de información por parte del modelo. Se añadieron controles deslizantes para ajustar la Temperatura (creatividad vs. precisión) y el Top P (diversidad del vocabulario), permitiéndonos poder experimentar con varias configuraciones tratando de buscar el mejor resultado posible. y por último se integró la API de Tavily (Web Search) que nos permite que el chatbot, pueda consultar datos actualizados en la web, mitigando alucinaciones sobre eventos recientes o tarifas vigentes.

## Fase 5: Pruebas y Documentación 📋

En esta fase se docuementan las pruebas realizadas con el software y el proceso que se fue consolidando para poder elegir el la mejor combinación de caracteristicas para que nos de mejores resultados.

### 5.1 Pruebas por tipo de base de conocimiento

Se compararon varias versiones del contenido procesado:

*  **Markdown limpio:**
    * Tamaño aproximado: 29.000 líneas al inicio.
    * Luego, tras más filtros, bajó a alrededor de 11.455 líneas.
    * Resultado: mejoró bastante al eliminar botones, menús, redes sociales y otros elementos irrelevantes.

*  **Texto plano limpio:**
    * Tamaño aproximado: 11.000 líneas.
    * Resultado: se veía más conciso y útil para el modelo.

*  **Versión grande con más contexto:**
    * Tamaño inicial: cerca de 39.629 líneas.
    * Resultado: tenía más información, pero también más ruido y repetición.

*  **Versión pequeña:**
    * Tamaño aproximado: 2.593 líneas.
    * Resultado: más ligera, pero con menos cobertura.

**Conclusión de esta prueba**

La base de conocimiento más útil terminó siendo la versión de texto plano limpio, porque redujo duplicados y contenido basura. Eso ayudó a que las respuestas fueran más precisas.

### 5.2 Pruebas por modelo de IA
Probaron principalmente estos modelos:

**a) Gemini / Gema:**
* Resultado: respondió de forma más conversacional y humana.
* Ventaja: daba respuestas más “amables” y desarrolladas.
* Desventaja: en algunos casos alucinaba o se iba por ramas.
* Observación: cuando se ajustó mejor el prompt y la base, mejoró bastante.

**b) Mistral**
* Resultado: fue el más rápido.
* Ventaja: respuestas más concisas y, en varias pruebas, más acertadas.
* Desventaja: a veces era más seco o menos “humano” en el tono.
* Observación: terminó siendo de los modelos más fuertes para este caso.

**c) Otros modelos probados**
* También se mencionaron pruebas con variantes de Gemini 1.5 / 2.5 / 3 flash y versiones “preview”.

**Resultado general:** 

El comportamiento cambiaba bastante según la versión, y algunas no estaban disponibles o daban error de configuración. El modelo mas acertado costo beneficio fue Mistral.

### 5.3 Pruebas por temperatura
Se hicieron pruebas con diferentes temperaturas.

**Temperatura alta**
* Ejemplos mencionados: valores cercanos a 0.9.
* Resultado: respuestas más humanas, más amplias y más “naturales”.
* Riesgo: mayor probabilidad de inventar cosas o mezclar información.

**Temperatura media / baja**
* Ejemplos mencionados: alrededor de 0.2 a 0.5.
* Resultado: respuestas más precisas, más controladas y menos alucinadas.
* Ventaja: mejor para un chatbot informativo como el de Celsia.

**Temperatura muy baja o cero**
* Resultado: más rigidez, menos creatividad.
* Ventaja: útil cuando se quiere exactitud.
* Desventaja: respuestas menos fluidas.

**Conclusión de temperatura**

Para este proyecto, la temperatura baja o media baja funcionó mejor, porque el objetivo era precisión y no creatividad.

### 5.4 Pruebas por top_p
También se habló de ajustar top_p para controlar la variedad de la respuesta.

**top_p más alto**
* Resultado: respuestas más estables y menos erráticas.
* Ventaja: menos riesgo de alucinación.

**top_p bajo**
* Resultado: mayor variedad en el texto.
* Desventaja: podía introducir más ruido o respuestas menos controladas.

**Conclusión de top_p**

La idea fue mantenerlo alto, dado que al combinarlo con el promp del sistema la temperatura baja y la base de conocimiento, era la combinación que daba mejores respuestas.

### 5.5 Resultado general de las pruebas
#### **Lo que mejor funcionó**
- Base de conocimiento depurada
* Mistral para rapidez y precisión
* Gemini para respuestas más humanas
* Temperatura baja o media-baja
* Top_p alto
* Prompt restrictivo y bien estructurado
#### **Lo que peor funcionó**
* Bases muy grandes con contenido repetido
* Markdown o texto con demasiados botones, enlaces y elementos basura
* Temperaturas altas cuando se quería precisión
* Prompts demasiado libres
#### **Conclusión final**
El equipo comprobó que la calidad del chatbot depende más de la limpieza del contenido y del control del prompt que del modelo por sí solo. Mistral se mostró como una opción muy fuerte para el caso, mientras que Gemini fue útil cuando se buscaba un tono más natural. La configuración ideal fue la que combinó: datos limpios, temperatura baja, top_p alto y un prompt estricto.
