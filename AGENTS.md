# Instrucciones de desarrollo — Producción Litúrgica OBS

Este archivo complementa el `README.md` y las instrucciones generales de desarrollo aportadas por el responsable del proyecto. Se aplica a todo el repositorio. No concede permisos nuevos ni sustituye las restricciones del entorno o las autorizaciones del usuario.

## 1. Propósito y límites del producto

Producción Litúrgica OBS es una herramienta **local y configurable** para preparar, controlar y mostrar gráficos en transmisiones realizadas con OBS Studio. Aunque nació de necesidades litúrgicas, debe servir a diferentes parroquias y comunidades: no codificar nombres, logos ni reglas particulares de una institución como valores obligatorios.

Principios del producto:

- El operador mantiene el control de lo que aparece al aire. **Preparar o previsualizar no equivale a publicar.**
- Proteger la continuidad de una transmisión tiene prioridad sobre una mejora estética.
- Una persona voluntaria debe poder utilizar las funciones esenciales sin configurar opciones avanzadas; un operador experimentado debe poder profundizar.
- Reutilizar una misma lógica de gráficos y configuración entre consola, biblioteca y Dock de OBS. Evitar implementaciones paralelas que terminen produciendo resultados distintos.
- Funcionar de forma local sin exigir cuentas, nube, internet o servicios adicionales para las funciones básicas.

## 2. Estado del proyecto: verificar, no asumir

La estructura base documentada en `main` incluye:

| Archivo | Responsabilidad actual |
|---|---|
| `launcher.py` | Inicio de la aplicación local |
| `servidor.py` | Servicio HTTP local y estado/configuración |
| `panel.html` | Consola de preparación y control |
| `overlay.html` | Salida visual para la Fuente de navegador de OBS |
| `README.md` | Instalación, uso, estructura y límites vigentes |
| `PLAN_V9.md` | Ideas previstas, no funciones ya entregadas |

En octubre de 2026 existen líneas de trabajo independientes que deben **comprobarse de nuevo antes de cada tarea**:

- Instalador y ZIP Windows: PR #2, rama `feature/windows-releases`; la compilación reportada no sustituye las pruebas reales en Windows y OBS.
- Biblioteca de lower thirds: PR #3, rama `feature/lower-thirds-studio`; la maqueta no controla por sí misma la salida real de OBS.
- Complejidad progresiva: PR #4, rama `feature/progressive-disclosure-ux`; existen criterios documentados y pruebas visuales/funcionales pendientes.
- Dock de OBS: rama `feature/obs-integrated-dock`; revisar código y comportamiento antes de afirmar que está integrado.
- Ministerios litúrgicos: PR #1, rama `feature/v9-ministerios-liturgicos`.

No tomar esta lista como estado actualizado de GitHub. Consultar ramas, PR, commits y verificaciones vigentes. Distinguir siempre: **implementado y verificado**, **implementado sin validar**, **prototipo**, **pendiente acordado** y **propuesta**.

## 3. Inicio y alcance de una tarea

1. Identificar repositorio, rama base, cambios pendientes y PR relacionados. No trabajar directamente en `main` salvo autorización expresa.
2. Leer `README.md`, este archivo y las especificaciones del módulo afectado; revisar el código real que ejecuta ese comportamiento.
3. Describir el resultado observable y los casos importantes: operación normal, entradas largas, datos ausentes, errores y vuelta al estado anterior.
4. Buscar componentes, estilos, servicios y reglas ya existentes antes de crear otros.
5. Delimitar una entrega funcional y verificable; registrar mejoras adicionales como pendientes, sin convertirlas automáticamente en una reescritura general.

Resolver decisiones rutinarias y reversibles dentro del alcance autorizado. Solicitar aprobación para publicar, fusionar, cambiar audiencia, introducir costos o realizar operaciones destructivas. Una instrucción de preparar una versión no autoriza a ponerla al aire en una transmisión real.

## 4. Arquitectura y fuente única de verdad

- Mantener separadas las responsabilidades de edición, estado/configuración, generación visual y publicación. No imponer frameworks, microservicios ni bases de datos sin una necesidad comprobada.
- Los valores que el operador debe editar (identidad, textos, medios, colores, plantillas, duraciones y preferencias) no deben exigir modificar código o recompilar.
- Definir una fuente autoritativa para cada valor compartido y hacer que consola, biblioteca, Dock y salida OBS consuman la misma regla. No guardar copias editables contradictorias.
- Distinguir **borrador**, **vista previa**, **estado publicado** y **preferencias de interfaz**. La preferencia de nivel de interfaz no es un cambio al gráfico emitido.
- En `main`, la documentación identifica `configuracion.json` y `media/` como datos locales. La migración de almacenamiento a `%LOCALAPPDATA%` forma parte del trabajo de Windows: comprobar si está integrada antes de utilizar esa ruta como contrato definitivo.
- Preservar configuraciones y medios al actualizar. Versionar formatos de importación/exportación cuando aparezcan, validar archivos y definir compatibilidad.
- Cuando cambie una regla o dato compartido, revisar todos sus consumidores: panel, overlay, Dock, plantillas, exportaciones y configuraciones guardadas.
- Conservar la configuración efectivamente publicada mientras el operador prepara cambios nuevos. No cambiar retrospectivamente un estado histórico cerrado sin autorización.

## 5. Interfaz con complejidad progresiva

Una sola aplicación, una sola lógica y tres niveles de exposición de controles:

| Nivel | Experiencia buscada |
|---|---|
| **Esencial** (predeterminado) | Seleccionar gráfico/plantilla, introducir contenido, preparar, publicar, limpiar y restaurar |
| **Personalizar** | Colores, tipografías, logos, composiciones y transiciones frecuentes |
| **Avanzado** | Duraciones, curvas de animación, capas, ajustes finos y controles especializados cuando existan |

Reglas obligatorias:

- La vista de programa, conexión/estado de emisión, **Imagen limpia** y **Restaurar** permanecen accesibles en todos los niveles.
- Cambiar de nivel es reversible: no borra datos, no restablece preferencias, no ejecuta `/api/update` ni publica cambios.
- Abrir opciones avanzadas muestra los valores efectivos y distingue predeterminados de personalizaciones.
- Los niveles no son roles ni conceden permisos. Mostrar menos controles nunca oculta errores, consecuencias o información crítica.
- Conservar controles utilizables por teclado, foco visible, contrastes adecuados y movimiento reducido cuando corresponda.
- Revisar `docs/UX_COMPLEJIDAD_PROGRESIVA.md` y `tests/VALIDACION_UX.md` cuando estén integrados en la rama de trabajo; no asumir que ya existen en `main`.

## 6. Biblioteca de gráficos y plantillas

Desarrollar gradualmente categorías útiles para transmisiones: lower thirds/cintillos, portadas, avisos, temporizadores, identificadores persistentes, pantallas completas y otras que se aprueben. **Una categoría propuesta no cuenta como implementada.**

Para cada nuevo tipo de gráfico, definir:

1. Propósito, campos editables, texto de ejemplo y límites (nombres largos, segunda línea, campos vacíos).
2. Plantillas iniciales reutilizables y apariencia personalizable sin perder el diseño predeterminado.
3. Vista previa fiel al formato de salida acordado (base actual: 1920 × 1080).
4. Relación entre borrador, plantilla guardada y contenido publicado.
5. Animación de entrada y salida, desactivación y compatibilidad con movimiento reducido cuando aplique.
6. Formato de persistencia, validación, versionado y recuperación ante configuraciones inválidas.

Las plantillas son **datos de configuración** y no copias completas de la lógica de renderizado. Compartir tokens de color, tipografía, espaciado y animación cuando tengan el mismo significado. Evitar que cambiar un estilo en el editor produzca un resultado distinto en la salida OBS.

No modificar ni redibujar logos o fotografías aportados por el usuario sin autorización. Preservar proporciones y calidad; gestionar licencias y procedencia de recursos incluidos en plantillas distribuidas.

## 7. Motor de animaciones y transiciones

- Reutilizar efectos y parámetros entre tipos de gráficos. No crear un motor diferente para cada plantilla.
- Permitir que entrada y salida tengan ajustes independientes cuando la función lo requiera.
- Utilizar unidades y límites claros para duración, retraso, dirección, velocidad/curva y opacidad. Prevenir combinaciones inválidas o saltos visuales.
- Mantener un efecto sencillo predeterminado y permitir desactivar animaciones.
- Probar el resultado visual real y su comportamiento al lanzar acciones repetidas, interrumpir una transición, limpiar la salida y restaurar.
- Mantener las animaciones acotadas en consumo de CPU/GPU; no prometer métricas de rendimiento sin pruebas en equipos representativos.

## 8. Seguridad operativa durante una transmisión

- Respetar la separación **Preparar → Previsualizar → Publicar en OBS**. Ningún cambio de texto, plantilla o nivel debe ir al aire accidentalmente.
- **Imagen limpia** debe actuar inmediatamente y sin confirmaciones bloqueantes; **Restaurar** debe recuperar el estado previsto. Mantener sus controles localizables.
- No avanzar automáticamente por momentos de una celebración litúrgica. Los avisos y transiciones de escena deben quedar bajo control del operador, salvo automatización específica aprobada.
- Mostrar con claridad conexión, estado actual, error y último resultado confirmado. No anunciar «Publicado» cuando solo se ha guardado localmente.
- No anunciar «AL AIRE» por el solo hecho de publicar en el servidor HTTP local: exigir confirmación de fuente activa en Programa y transmisión activa en OBS. Ante falta de verificación, indicar «SIN VERIFICAR».
- Diseñar una recuperación segura ante pérdida de conexión del Dock, recarga del navegador, archivo de medios ausente o fallo de animación.
- No impedir la transmisión principal si el programa auxiliar falla. Documentar el comportamiento de los gráficos ante reinicios.

## 9. Dock y comunicación con OBS

- El **panel web es el único lugar para configurar** gráficos generales, identidad, participantes y portadas. El Estudio configura las plantillas de Lower Thirds usando el mismo estado local.
- El Dock debe actuar exclusivamente como **lanzador y superficie operativa durante la transmisión**: mostrar gráficos preparados, cuenta regresiva, imagen limpia/restauración y elementos auxiliares. No duplicar formularios de edición ni crear configuración independiente.
- El formulario del panel debe mostrar campos apropiados para cada tipo de gráfico, con ayuda contextual y una distinción clara entre guardar preparación y mostrar en OBS.
- Comprobar el funcionamiento real del Dock en OBS antes de declarar la integración terminada. Una maqueta HTML o una URL que abre en navegador no prueban por sí solas el comportamiento en OBS.
- Mantener compatibilidad con la Fuente de navegador y el servicio local ya documentados; modificar contratos de API con pruebas de regresión y justificación.
- La configuración actual usa `127.0.0.1:8765`. No exponer el servidor a la red pública ni eliminar ese límite sin diseño de autenticación y autorización aprobado.

## 10. Verificación y criterios de entrega

Escoger pruebas proporcionales al cambio, pero no sustituir el recorrido completo por una compilación exitosa.

**Mínimo para cambios visuales o de gráficos:**

- Abrir el panel y preparar una plantilla con datos representativos, texto largo y campos vacíos.
- Comprobar vista previa, guardado, recarga y ausencia de publicación accidental.
- Publicar en una fuente de navegador de OBS de prueba; comprobar salida, entrada/salida de animación, Imagen limpia y Restaurar.
- Comprobar que consola y Dock (cuando esté integrado) muestran estados coherentes.
- Probar pérdida de conexión, archivos faltantes y acciones rápidas/repetidas si afectan el cambio.
- Revisar teclado, foco, tamaños de pantalla pertinentes y movimiento reducido.

**Mínimo para versiones Windows:** instalación o extracción, primera ejecución, puerto local, integración con OBS, cierre/reinicio, actualización que conserve datos y desinstalación cuando aplique. Verificar instalador `.exe` y ZIP portátil por separado. No declarar firma digital, compatibilidad o publicación en Releases sin evidencia.

Registrar comandos, sistema operativo, versión de OBS, casos ejecutados y resultados. Una prueba pendiente debe marcarse como pendiente. Las simulaciones y revisiones estructurales no equivalen a pruebas visuales o integraciones reales.

## 11. Repositorio, seguridad y publicación

- Trabajar por rama y PR; mantener `main` intacta hasta revisión e integración autorizadas. No fusionar automáticamente trabajos todavía pendientes de pruebas.
- Revisar diff y archivos modificados. Evitar cambios ajenos, reescritura de historia y eliminación de trabajo de terceros.
- Mantener secretos, información personal, `configuracion.json` operativo y `media/` fuera del repositorio. Usar datos ficticios en pruebas.
- Validar entradas y carga de archivos; no convertir contenido del operador en código ejecutable ni exponer información local mediante nuevas rutas sin controles.
- Mantener instrucciones de instalación, requisitos, versiones, pruebas y limitaciones actualizadas junto con los cambios de comportamiento.
- Preparar y publicar Releases solo con autorización y después de validar artefactos y flujo real; identificar commit, versión y método de recuperación.

## 12. Informe al terminar

Responder en español y de forma concreta:

- **Resultado:** qué cambió y para qué sirve al operador.
- **Estado:** propuesta, implementado, verificado, en revisión, integrado o publicado.
- **Verificación:** qué se ejecutó, dónde y con qué resultado.
- **Pendientes/límites:** especialmente pruebas en Windows/OBS y conexiones aún simuladas.
- **Enlace:** rama, PR, archivo o Release real cuando exista.
- **Siguiente paso:** la acción comprobable que corresponde.

No inventar enlaces, resultados, pruebas o funcionalidades. En los siguientes turnos recuperar el estado real del repositorio y las decisiones vigentes antes de seguir desarrollando.
