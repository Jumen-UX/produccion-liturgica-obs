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
- [ ] En modo **Esencial**, localizar las tarjetas «1. Conectar OBS» y «2. Conectar teléfono o tableta» sin ir a Avanzado.
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

- [ ] **Prueba automatizada incorporada al CI:** instalar dos paquetes sucesivos con el mismo `AppId` y versiones de prueba distintas; verificar una sola entrada de desinstalación y persistencia de un archivo de datos. Marcar aprobado solo cuando lo confirme GitHub Actions.
- [ ] En una PC Windows de pruebas, instalar realmente una versión anterior publicada o entregada para pruebas (no una segunda compilación del mismo código).
- [ ] Preparar nombre de comunidad, logo, plantilla, participantes y acceso LAN; hacer respaldo privado de `%LOCALAPPDATA%\ProduccionLiturgicaOBS`.
- [ ] Cerrar el programa auxiliar y OBS cuando sea necesario para liberar el ejecutable; instalar la nueva versión **sin desinstalar primero**.
- [ ] Confirmar en **Aplicaciones instaladas** una sola entrada «Producción Litúrgica OBS», y que los accesos directos abren la versión nueva.
- [ ] Confirmar la conservación de `configuracion.json`, medios y `acceso_lan.json`; volver a introducir la clave OBS WebSocket (solo se conserva en memoria) y probar Dock, Fuente de navegador, QR y estado de programa.
- [ ] Desinstalar desde Windows y comprobar que las configuraciones y archivos personales permanecen recuperables. No borrar los datos antes de verificarlos.
- [ ] Si había carpetas de ZIP/EXE portátiles antiguos, retirarlas por separado **solo después** de confirmar la actualización; el instalador no debe eliminarlas automáticamente.

**La integración con OBS y las pruebas visuales requieren ejecución en la computadora del operador.**
