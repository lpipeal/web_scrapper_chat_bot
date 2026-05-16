Historia e Información Corporativa:
1. ¿Qué es Celsia y en qué países opera?
2. ¿Cuál es el propósito principal o la misión de la empresa?
3. ¿Quién es el actual CEO o líder de Celsia?
4. ¿En qué año se fundó o inició operaciones la compañía?

Productos y Servicios (Hogares):
5. ¿Cómo puedo solicitar la instalación de internet con Celsia?
6. ¿Qué requisitos necesito para instalar paneles solares en mi casa?
7. ¿Tienen algún programa para revisar el consumo de energía en mi hogar?
8. ¿Cómo puedo pagar mi factura de energía en línea?

Soluciones para Pymes y Empresas:
9. ¿Qué soluciones de eficiencia energética ofrecen para pequeñas empresas (Pymes)?
10. ¿Ofrecen auditorías energéticas para fábricas o industrias grandes?
11. Soy dueño de un local, ¿cómo me beneficia cambiarme a la energía solar de Celsia?
12. ¿Qué es el modelo de negocio de "Venta de Energía" o PPA que ofrecen a las empresas?

Sostenibilidad y Movilidad Eléctrica:
13. ¿Qué metas de reducción de huella de carbono tiene Celsia?
14. ¿Cómo funciona el servicio de estaciones de carga para vehículos eléctricos?
15. ¿Qué proyectos de reforestación o protección ambiental lidera la empresa?
16. ¿Qué porcentaje de su energía proviene de fuentes renovables?

Atención al Cliente y "Preguntas Trampa" (Para probar alucinaciones):
17. ¿Cuáles son los números de teléfono de atención al cliente en el Valle del Cauca?
18. ¿Dónde están ubicadas las oficinas principales de atención al usuario?
19. [Trampa] ¿A qué precio están vendiendo las acciones de Ecopetrol hoy? (El bot debe decir que no sabe).
20. [Trampa] ¿Puedo comprar un paquete de televisión por cable con Celsia? (El bot debe aclarar que ofrecen internet, no TV por cable, o decir que no tiene info si no está en el texto).



## Questions V2
1. Pruebas de Información Básica (JSON)
Estas preguntas deberían activar el nodo basic_info. Son datos precisos y estructurados.

"¿Cuál es el NIT oficial de Celsia?"

"¿En qué ciudades tienen sedes registradas?"

"Dime la razón social completa de la empresa."

Cuales son las sedes administrativas?

lineas de atención

2. Pruebas de Conocimiento Detallado (RAG/Qdrant)
Estas preguntas obligan al bot a buscar en los documentos que scrapeaste. Aquí verás qué tan bien se hizo la limpieza de texto y la creación de fragmentos.

"¿Qué tipo de soluciones solares ofrece Celsia para empresas?"

"¿Cómo funciona el servicio de eficiencia energética?"

"¿Tienen proyectos de movilidad eléctrica o estaciones de carga?"

"¿Qué beneficios mencionan sobre el uso de energías renovables?"

3. Pruebas de "Estrés" (Consultas Mixtas)
Estas son las más interesantes porque el Router debe decidir si prioriza el RAG o el JSON.

"Dame el NIT de la empresa y explícame brevemente qué hacen con la energía eólica."

"¿Celsia tiene sede en Cali? Si es así, ¿qué proyectos de alumbrado público manejan?"

4. Pruebas de Cortesía y Fallbacks
Para ver si el bot mantiene la personalidad o si el flujo de direct_answer funciona.

"Hola, ¿quién eres y en qué puedes ayudarme?"

"¿Cuál es el clima hoy en Cali?" (Aquí debería decirte educadamente que solo sabe de Celsia).