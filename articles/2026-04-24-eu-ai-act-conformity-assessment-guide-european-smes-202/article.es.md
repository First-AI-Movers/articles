> **TL;DR:** Guía paso a paso sobre la evaluación de la conformidad para las pymes de la UE que implementan IA de alto riesgo según el anexo III. Abarca la distinción entre el implementador y el proveedor, la documentación y la supervisión.

Para llevar a cabo correctamente la evaluación de la conformidad con la Reglamento de Inteligencia Artificial de la UE, hay que tener en cuenta una distinción clave: ¿es usted la organización que ha creado y comercializado el sistema de IA, o la organización que lo utiliza en sus propias operaciones? Por qué es importante: una empresa checa de tecnología de RR. HH. con 25 empleados que desarrolla una herramienta de selección de CV y la vende a sus clientes asume toda la carga de la evaluación. Eso implica documentación técnica, un sistema de gestión de la calidad, una declaración de conformidad y el marcado CE. Una empresa de logística holandesa con 40 empleados que adquiere la licencia de esa misma herramienta es un implementador con obligaciones sustancialmente menores. Acertar en esa clasificación determina si su proyecto de cumplimiento normativo durará dos semanas o seis meses.

Esta guía orienta a los responsables de cumplimiento, equipos técnicos y líderes de operaciones de empresas SaaS en crecimiento y empresas de software medianas a través del procedimiento de conformidad de cuatro pasos para implementadores, el conjunto completo de documentación exigido a los proveedores y las distinciones específicas que determinan qué vía se aplica a su organización.

---

## Cuándo se requiere la evaluación de conformidad

La evaluación de conformidad solo es necesaria para los sistemas de IA de alto riesgo del anexo III. No todas las herramientas de IA que utiliza una empresa de servicios profesionales o una empresa de SaaS en crecimiento cumplen los requisitos. La Reglamento de Inteligencia Artificial de la UE define ocho categorías de sistemas de alto riesgo en el anexo III, que abarcan ámbitos como la identificación biométrica, la gestión de infraestructuras críticas, la educación y la formación, las decisiones en materia de empleo, el acceso a servicios esenciales, la aplicación de la ley, la migración y el control de fronteras, y la administración de justicia.

Si su sistema de IA no entra en ninguna de esas categorías, no se requiere la evaluación de la conformidad. Es posible que siga teniendo obligaciones de transparencia en virtud del artículo 50 y obligaciones de gobernanza de datos del RGPD, pero no se aplica el conjunto completo de requisitos de cumplimiento del anexo III.

Si su sistema sí entra en el ámbito del anexo III, la siguiente pregunta es si usted es un proveedor o un implementador. El reglamento trata estas funciones de manera diferente.

**Proveedor:** una organización que desarrolla un sistema de IA, o que encarga su desarrollo, y lo comercializa bajo su propio nombre o marca. Comercializarlo significa poner el sistema a disposición de terceros.

**Implementador:** una organización que utiliza un sistema de IA en el marco de sus actividades profesionales. Los implementadores no comercializan el sistema. Lo ponen en servicio dentro de su propia organización.

La vía de conformidad para un proveedor es significativamente más exigente que para un implementador.

---

## Las obligaciones del implementador: el artículo 25 en la práctica

La mayoría de las pymes que utilizan herramientas de IA de terceros para la selección de personal, la evaluación crediticia u otros casos de uso del anexo III son implementadores. Las obligaciones previstas en el artículo 25 son proporcionales a esa función.

Como implementador de un sistema de IA de alto riesgo, su equipo de cumplimiento normativo es responsable de cuatro aspectos.

**Seguir las instrucciones de uso del proveedor.** El proveedor está obligado a proporcionar documentación técnica e instrucciones que describan la finalidad prevista, las condiciones en las que el sistema puede implementarse de forma segura y cualquier requisito de supervisión humana. La implementación fuera de la finalidad prevista transfiere la responsabilidad del proveedor a usted.

**Aplicar la supervisión humana del artículo 14.** El artículo 14 exige a los implementadores que asignen la supervisión a personas físicas con la competencia, la formación y la autoridad necesarias para comprender los resultados del sistema, identificar anomalías e intervenir o anular el sistema cuando sea necesario. La supervisión debe ser estructuralmente posible: el sistema no puede diseñarse de forma que impida la intervención humana.

**Supervise las modificaciones sustanciales.** Si el sistema se actualiza de forma que cambie su finalidad prevista o su perfil de riesgo, puede ser necesario repetir la evaluación de la conformidad. Como implementador, usted es responsable de señalar los cambios sustanciales a su proveedor.

**Regístrese en la base de datos de la UE cuando sea necesario.** Los implementadores de determinados sistemas de alto riesgo, especialmente en contextos de la administración pública, deben registrar su uso en la base de datos pública de IA de la UE. Para la mayoría de las pymes del sector privado, esta obligación se aplica principalmente a los proveedores y no a los implementadores.

---

## Las obligaciones del proveedor: el artículo 17 y el conjunto completo de requisitos de conformidad

Si su organización está desarrollando un sistema de IA que se comercializará, o si su equipo de operaciones ha encargado un sistema a medida que se comercializará, usted es un proveedor y se le aplican todas las obligaciones del anexo III.

El requisito fundamental es un sistema de gestión de la calidad (SGQ) conforme al artículo 17 que abarque todo el ciclo de vida del sistema de IA. El SGQ debe documentar su proceso de gestión de riesgos, sus prácticas de gobernanza de datos, su metodología de validación y ensayo, su plan de seguimiento poscomercialización y sus procedimientos para gestionar incidentes y no conformidades.

Más allá del SGQ, los proveedores deben elaborar un conjunto de documentación técnica, realizar una evaluación de la conformidad (se permite la autoevaluación para la mayoría de las categorías del anexo III; se requiere una evaluación por parte de un organismo notificado para la identificación biométrica y un pequeño número de otras categorías), redactar una declaración de conformidad de la UE y colocar el marcado CE en el sistema antes de comercializarlo.

Para una empresa de software de tamaño medio que desarrolla en un ámbito de IA regulado, se trata de una tarea considerable. La evaluación de la conformidad por sí sola suele requerir la participación de equipos jurídicos, técnicos y de datos, además de una revisión externa si se dirige a sectores regulados como los servicios financieros o la asistencia sanitaria.

---

## El procedimiento de conformidad para implementadores en cuatro pasos

Para la mayoría de las pymes, el procedimiento pertinente es la vía del implementador. A continuación se presenta un enfoque estructurado.

**Paso 1: Clasificar el sistema.** Confirme que el sistema de IA que va a implementar se encuentra realmente dentro del ámbito del anexo III. Revise la categoría específica en la que podría encajar y compruebe si se aplica alguna de las exclusiones del artículo 6. Es poco probable que un sistema de IA utilizado para una función claramente auxiliar (generar informes internos, resumir notas de reuniones) se considere de alto riesgo, incluso si entra en contacto con un ámbito regulado. Documente el razonamiento de su clasificación.

**Paso 2: Obtenga la documentación técnica del proveedor y la Declaración de Conformidad.** Antes de implementar cualquier sistema del anexo III, solicite al proveedor el paquete de documentación técnica y su Declaración de Conformidad de la UE. La Declaración de Conformidad es la declaración formal del proveedor de que el sistema cumple los requisitos de la Reglamento de Inteligencia Artificial de la UE. Si el proveedor no puede presentar estos documentos, no cumple con sus propias obligaciones como proveedor, y usted no debe implementar su sistema en un contexto del anexo III.

**Paso 3: Implemente las medidas de supervisión humana del artículo 14.** Basándose en las instrucciones de uso del proveedor, diseñe y documente su proceso de supervisión humana. Especifique quién de su equipo operativo es responsable de la supervisión, qué formación ha recibido, cómo puede intervenir en el sistema o anularlo, y cómo se revisan y registran las decisiones influidas por la IA.

**Paso 4: Documente sus procedimientos operativos.** Elabore un registro de implementación que incluya: la clasificación del sistema, la documentación del proveedor obtenida, su proceso de supervisión, cualquier decisión de configuración tomada y su procedimiento para el seguimiento y la notificación de incidentes. Este documento no tiene por qué ser muy detallado para la mayoría de las pymes, pero debe existir y mantenerse actualizado a medida que el sistema evoluciona.

---

## Documentación técnica: el conjunto mínimo

El conjunto mínimo de documentación técnica para un sistema del anexo III abarca seis áreas.

**Descripción del sistema.** Qué hace el sistema, cómo funciona a nivel funcional y cuál es su finalidad prevista. Esto incluye el enfoque de IA utilizado, las entradas y salidas, y el contexto de implementación.

**Declaración de finalidad prevista.** Una declaración precisa del caso de uso para el que se diseñó y validó el sistema. La implementación fuera de la finalidad prevista supone un riesgo de cumplimiento para el implementador y un riesgo de responsabilidad civil para el proveedor.

**Proceso de gestión de riesgos.** Cómo ha identificado, evaluado y mitigado el proveedor los riesgos asociados al sistema, incluidos los riesgos de error, sesgo y uso indebido.

**Documentación sobre gobernanza de datos.** Los conjuntos de datos utilizados para entrenar y validar el sistema, las medidas de calidad de los datos aplicadas y cualquier limitación o sesgo conocido en los datos de entrenamiento.

**Métricas de precisión, robustez y ciberseguridad.** Puntos de referencia cuantitativos del rendimiento del sistema, incluida la precisión en los conjuntos de validación y las medidas de seguridad que protegen al sistema contra la manipulación.

**Plan de seguimiento poscomercialización.** Cómo supervisará el proveedor el rendimiento del sistema tras su implementación, qué métricas seguirá y cómo comunicará las actualizaciones o los problemas identificados a los implementadores.

Como implementador, debe recibir los seis componentes de su proveedor antes de la puesta en marcha.

---

## Preguntas frecuentes

**¿Se aplica la evaluación de conformidad de la Reglamento de Inteligencia Artificial de la UE a las herramientas de IA que utilizamos internamente, y no solo a los productos que vendemos?**
Sí, si el uso interno entra dentro de una categoría del anexo III. La implementación interna de un sistema de IA de alto riesgo, por ejemplo, el uso de una herramienta de IA para evaluar el rendimiento de los empleados, da lugar a obligaciones para el implementador en virtud del artículo 25, aunque no se comercialice ningún producto.

**Somos una empresa SaaS en crecimiento que ofrece una función de IA como parte de una plataforma más amplia. ¿Somos un proveedor?**
Es casi seguro que sí, en lo que respecta al componente de la función de IA. Si pone esa función a disposición de los clientes, está comercializando un sistema de IA. Si la función desempeña una función del anexo III para sus clientes, se aplican todas las obligaciones del proveedor a dicha función, independientemente de si está integrada en un producto más amplio que no sea de IA.

**¿Podemos basarnos en el marcado CE de nuestro proveedor como prueba de nuestro propio cumplimiento?**
El marcado CE demuestra que el proveedor ha completado la evaluación de conformidad requerida. Como implementador, puede hacer referencia a él como prueba de que el sistema que está implementando ha sido evaluado. Sin embargo, no cubre sus obligaciones como implementador. La implementación de la supervisión humana prevista en el artículo 14 y la documentación de su implementación operativa siguen siendo su responsabilidad.

**¿Qué ocurre si modificamos un sistema de IA de alto riesgo de terceros que hemos implementado?**
Una modificación sustancial de un sistema de IA de alto riesgo puede reclasificar a la organización que realiza la modificación como el proveedor de esa versión modificada. La Reglamento de Inteligencia Artificial de la UE define la modificación sustancial de tal manera que incluye cambios que afectan a la finalidad prevista del sistema, a sus métricas de rendimiento o a su perfil de riesgo. Si su equipo técnico realiza cambios de ese alcance en un sistema con licencia, solicite asesoramiento jurídico antes de implementar la versión modificada.

---

## Lecturas recomendadas

- [Reglamento de Inteligencia Artificial de la UE: sistemas de alto riesgo. Lo que deben evaluar las pymes de la UE](https://radar.firstaimovers.com/eu-ai-act-high-risk-systems-assessment-european-smes-2026)
- [Reglamento de Inteligencia Artificial de la UE: sistemas de IA de uso general: lista de verificación de cumplimiento para agosto de 2026](https://radar.firstaimovers.com/eu-ai-act-gp-systems-august-2026-compliance-checklist)
- [Marco de gobernanza de la IA para las pymes europeas](https://radar.firstaimovers.com/ai-governance-framework-european-sme-2026)

Si es la primera vez que trabaja en la clasificación del anexo III y la planificación de la conformidad, la [Evaluación de preparación para la IA](https://radar.firstaimovers.com/page/ai-readiness-assessment) le ofrece una base estructurada antes de contratar a un asesor jurídico o comenzar con la documentación.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "EU AI Act Conformity Assessment: A Practical Guide for European SMEs",
  "description": "Step-by-step conformity assessment for EU SMEs deploying Annex III high-risk AI. Covers deployer vs provider split, documentation, and oversight.",
  "datePublished": "2026-04-24T10:32:37.598341+00:00",
  "dateModified": "2026-04-24T10:32:37.598341+00:00",
  "author": {
    "@type": "Person",
    "@id": "https://radar.firstaimovers.com/page/dr-hernani-costa#dr-hernani-costa",
    "name": "Dr. Hernani Costa",
    "url": "https://radar.firstaimovers.com/page/dr-hernani-costa"
  },
  "publisher": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://radar.firstaimovers.com/favicon.ico"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://radar.firstaimovers.com/eu-ai-act-conformity-assessment-guide-european-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=630&fit=crop&q=80",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [
      ".article-body > p:first-of-type",
      ".article-body > p:nth-of-type(2)"
    ],
    "xpath": [
      "/html/body//article//p[1]",
      "/html/body//article//p[2]"
    ]
  }
}
</script>
-->

---

**Autor:** [Dr. Hernani Costa](https://drhernanicosta.com) — Fundador de [First AI Movers](https://firstaimovers.com) y [Core Ventures](https://coreventures.xyz). Arquitecto de IA, asesor estratégico y CTO a tiempo parcial que ayuda a las principales empresas innovadoras mundiales a orientarse en las innovaciones de IA. Doctor en Lingüística Computacional, con más de 25 años de experiencia en tecnología.

*Publicado originalmente en [First AI Movers](https://radar.firstaimovers.com/eu-ai-act-conformity-assessment-guide-european-smes-2026) bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*