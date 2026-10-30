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
- [ ] Abrir **Avanzado → Conexión y verificación de OBS** y configurar puerto, contraseña y nombre exacto de Fuente de navegador.
- [ ] Sin OBS conectado, comprobar que Dock y panel muestran **SIN VERIFICAR**, pero permiten usar Imagen limpia y Restaurar.
- [ ] Con OBS conectado y transmisión detenida, activar la fuente en programa: debe mostrarse **EN PROGRAMA**.
- [ ] Iniciar transmisión de prueba con la fuente activa y gráfico publicado: debe mostrarse **AL AIRE** en Dock y panel.
- [ ] Cambiar a una escena de programa sin la fuente: debe mostrarse **FUERA DE PROGRAMA**.
- [ ] Usar Imagen limpia: debe mostrarse **IMAGEN LIMPIA**; Restaurar debe recuperar el gráfico anterior.
- [ ] Cortar OBS WebSocket o simular reconexión: nunca debe permanecer falsamente **AL AIRE**.
- [ ] Confirmar que los botones del Dock identifican solo el gráfico preparado que coincide con el publicado, aunque otro gráfico del mismo tipo tenga nuevos textos.

**La integración con OBS y las pruebas visuales requieren ejecución en la computadora del operador.**
