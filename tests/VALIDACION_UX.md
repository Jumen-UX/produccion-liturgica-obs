# Validación manual — complejidad progresiva

Entorno: Windows, navegador Chromium/Edge y dock de OBS cuando esté integrado.

- [ ] Entrar por primera vez. Debe aparecer **Esencial**.
- [ ] Comprobar que **Imagen limpia**, **Restaurar**, la vista de emisión y el estado de conexión están siempre presentes.
- [ ] Elegir **Personalizar** y verificar acceso a colores, portada, fotografías, avisos, redes y logo.
- [ ] Elegir **Avanzado** y verificar logo persistente y opciones de video.
- [ ] Volver a Esencial. Confirmar que no se perdieron los valores editados.
- [ ] Recargar. Debe conservar la última vista, sin publicar cambios.
- [ ] Durante una emisión de prueba, editar un nombre y cambiar de nivel. OBS debe seguir mostrando el valor publicado anteriormente.
- [ ] Pulsar Publicar en OBS. Solo entonces debe actualizarse la salida.
- [ ] Activar Imagen limpia desde cada vista. La salida debe limpiar inmediatamente.
- [ ] Restaurar y comprobar la salida previa prevista.
- [ ] Probar navegación de teclado, foco visible y pantalla estrecha.
- [ ] Verificar que errores de almacenamiento local no impiden usar la consola.
- [ ] En modo **Esencial**, abrir «Conexiones · OBS y teléfono» y localizar las tarjetas «1. Conectar OBS» y «2. Conectar teléfono o tableta» sin ir a Avanzado.
- [ ] Con OBS abierto, comprobar detección automática de la fuente de navegador de `overlay.html`; si hay dos coincidencias, no debe seleccionar una arbitrariamente.
- [ ] Comprobar que el QR aparece en la segunda tarjeta solo al activar acceso remoto con una contraseña válida y que el enlace abre en un móvil de la misma red.
- [ ] Sin OBS conectado, comprobar que Dock y panel muestran **SIN VERIFICAR**, pero permiten usar Imagen limpia y Restaurar.
- [ ] Con OBS conectado y transmisión detenida, activar la fuente en programa: debe mostrarse **EN PROGRAMA**.
- [ ] Iniciar transmisión de prueba con la fuente activa y gráfico publicado: debe mostrarse **AL AIRE** en Dock y panel.
- [ ] Cambiar a una escena de programa sin la fuente: debe mostrarse **FUERA DE PROGRAMA**.
- [ ] Usar Imagen limpia: debe mostrarse **IMAGEN LIMPIA**; Restaurar debe recuperar el gráfico anterior.
- [ ] Cortar OBS WebSocket o simular reconexión: nunca debe permanecer falsamente **AL AIRE**.
- [ ] Confirmar que los botones del Dock identifican solo el gráfico preparado que coincide con el publicado, aunque otro gráfico del mismo tipo tenga nuevos textos.

## Actualizaciones y desinstalación en Windows

- [x] **Prueba automatizada incorporada al CI:** instalar dos paquetes sucesivos con el mismo `AppId` y versiones de prueba distintas; verificar una sola entrada de desinstalación y persistencia de un archivo de datos. [GitHub Actions #13: aprobado](https://github.com/Jumen-UX/produccion-liturgica-obs/actions/runs/41211102589).
- [ ] En una PC Windows de pruebas, instalar realmente una versión anterior publicada o entregada para pruebas (no una segunda compilación del mismo código).
- [ ] Preparar nombre de comunidad, logo, plantilla, participantes y acceso LAN; hacer respaldo privado de `%LOCALAPPDATA%\ProduccionLiturgicaOBS`.
- [ ] Cerrar el programa auxiliar y OBS cuando sea necesario para liberar el ejecutable; instalar la nueva versión **sin desinstalar primero**.
- [ ] Confirmar en **Aplicaciones instaladas** una sola entrada «Producción Litúrgica OBS», y que los accesos directos abren la versión nueva.
- [ ] Confirmar la conservación de `configuracion.json`, medios y `acceso_lan.json`; volver a introducir la clave OBS WebSocket (solo se conserva en memoria) y probar Dock, Fuente de navegador, QR y estado de programa.
- [ ] Desinstalar desde Windows y comprobar que las configuraciones y archivos personales permanecen recuperables. No borrar los datos antes de verificarlos.
- [ ] Si había carpetas de ZIP/EXE portátiles antiguos, retirarlas por separado **solo después** de confirmar la actualización; el instalador no debe eliminarlas automáticamente.

**La integración con OBS y las pruebas visuales requieren ejecución en la computadora del operador.**

## Comprobación de conexión persistente y panel compacto

- El operador confirmó en este chat que pudo conectar desde el móvil y que funciona; esto no acredita todavía todos los casos de la lista.
- [ ] Con OBS configurado, mantener el panel abierto varios minutos y confirmar que cesan los avisos repetidos de conexión/desconexión.
- [ ] Reiniciar OBS y comprobar reconexión y ausencia de un indicador AL AIRE obsoleto.
- [ ] Verificar que Conexiones, Identidad y Guía se despliegan por teclado y que los botones de conectar abren los ajustes.
- [ ] Confirmar que preparar, publicar, limpiar, restaurar y observar la salida siguen accesibles con los ajustes plegados.

## Interfaces adaptativas: Dock, remoto y panel web

- Prueba reproducible: `node tests/test_responsive_interfaces.cjs` (Chrome/Edge instalado, o ruta en `CHROME_BINARY`).
- Verificado localmente en Windows/Chromium: 48 combinaciones (anchos 240, 280, 320, 375, 480, 768, 960 y 1280; alturas 360 y 800), sin desbordamiento horizontal, con secciones desplegadas.
- Eventos reales del navegador con HTTP/OBS simulados: guardar frente a publicar, lanzar, limpiar/restaurar, temporizador, logo/redes, accesos a ajustes, consulta sin permisos, desconexión y prevención de clics duplicados mientras una orden sigue pendiente.
- Dock y remoto: estado y controles de salida primero; gráficos preparados después; logo y redes en un desplegable. La cabecera operativa permanece al desplazar cuando la altura permite hacerlo.
- Panel web estrecho: salida antes de preparación; vista previa desplegable; participantes agrupados, con apertura directa desde «Ir a participantes». Controles críticos en la barra compacta, sin botones duplicados en el monitor.
- [ ] Redimensionar el Dock dentro de OBS real y probar cada control en una transmisión simulada.
- [ ] Comprobar el remoto en el teléfono real, en vertical/horizontal y con textos largos.
- [ ] Revisar teclado/foco y uso con zoom del navegador en el panel.
- Estas pruebas simuladas no certifican la salida real de OBS ni reemplazan la validación del dispositivo.

## Biblioteca de producción, redes y vista previa real (PR #8)

- [ ] En **Biblioteca de producciones**, crear una producción, agregar tres Lower Thirds, editarlos, duplicarlos, reordenarlos y desactivar uno. Verificar que el Dock solo permite lanzar los habilitados.
- [ ] Confirmar que guardar o editar elementos no modifica la emisión hasta pulsar **Lanzar**.
- [ ] Comparar **Estudio → Vista previa** con la Fuente de navegador OBS configurada a **1920 × 1080**: plantilla, colores, nombre, posiciones y tamaño. Las animaciones de entrada y salida deben usar el mismo motor.
- [ ] Comparar **Biblioteca → Vista previa** con OBS para Lower Thirds, lectura, avisos, frases y redes. No confundir vista previa local con una salida publicada.
- [ ] Verificar que el marco de vista previa conserva 16:9 al cambiar tamaño y en teléfono, sin cortar texto ni estirar elementos.
- [ ] Probar que la vista previa NO llama a `/api/update`, no altera `/api/state` y no detiene los gráficos activos.
- [ ] En la biblioteca social, cargar PNG/JPG/WEBP personalizado en una red, guardarlo, volver a abrir la edición y comprobar que persiste. El icono de la plataforma debe aparecer cuando no exista logo personalizado.
- [ ] Configurar tres redes distintas con frases individuales como «Síguenos», «Dale like y comparte» y «Estamos en vivo», e iniciar rotación desde panel y Dock.
- [ ] Confirmar que solo aparece UNA red a la vez, respetando duración, intervalo, orden y ubicación (espera/directo/cierre). Comprobar modo sin repetición.
- [ ] Cambiar de gráfico durante la rotación: el contenido debe continuar sin tapar los Lower Thirds.
- [ ] Detener la rotación desde el Dock y comprobar desaparición sin interrumpir la transmisión.
- [ ] Con OBS en programa, distinguir **EN PROGRAMA** de **AL AIRE**; no atribuir a un ítem un estado confirmado si la fuente no está activa o WebSocket no responde.
- [ ] Cerrar y reabrir el programa: comprobar persistencia de producciones, logos y ajustes de rotación.
- [ ] Comprobar la salida real dentro de OBS y, si difiere del navegador, revisar tamaño de Fuente de navegador (1920 × 1080), zoom y fuentes instaladas. Los motores Chromium de OBS y del navegador pueden presentar pequeñas diferencias de tipografía.
