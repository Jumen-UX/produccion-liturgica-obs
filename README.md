# Producción Litúrgica OBS

Sistema local y configurable de gráficos para transmisiones de celebraciones litúrgicas mediante OBS Studio. **No está asociado a una parroquia específica.**

## Funciones existentes

- Identidad de parroquia o comunidad configurable (nombre, logo estático y logo animado).
- Cuenta regresiva, portadas, avisos con fotografía opcional y redes sociales.
- Colores y perfiles litúrgicos editables.
- Identificación de celebrante, diácono, lectores y monitores.
- Biblioteca de cuatro Lower Thirds personalizables con animaciones de entrada/salida y control real de borrador/publicación.
- Dock local para controlar la emisión y publicar identificaciones y Lower Thirds sin abandonar OBS.
- Separación entre preparación y publicación en OBS.
- Botones para limpiar/restaurar gráficos y cierre protegido.

## Descargas de Windows (al publicar una versión)

- Instalador: `ProduccionLiturgicaOBS-Setup.exe`, instalación por usuario, accesos directos y desinstalación.
- Portátil: `ProduccionLiturgicaOBS-Portable.zip`, descomprimir y abrir el EXE.
- Ninguna descarga necesita Python en el PC del operador.
- Los datos de cada parroquia se conservan en `%LOCALAPPDATA%\ProduccionLiturgicaOBS` fuera de la carpeta del programa.

### GitHub Actions

El flujo `.github/workflows/windows-release.yml` compila y prueba el ejecutable, crea instalador y ZIP. Los pull requests generan artefactos de prueba. Solo las etiquetas `vX.Y.Z` publican en GitHub Releases. **No publicar versiones estables sin validar en Windows y OBS.**

## Instalación en Windows (código fuente)

1. Extraer todo el ZIP a una carpeta **con permiso de escritura** (por ejemplo Documentos\Produccion-Liturgica). No ejecutarlo desde dentro del ZIP ni desde Archivos de programa.
2. Con Python 3 instalado, ejecutar `INICIAR_SIN_EXE.bat`; o construir el ejecutable usando `CREAR_EXE_WINDOWS.bat` desde Windows con Python 3.
3. Configurar el nombre de la comunidad en **Identidad de la comunidad**, guardar y publicar.
4. En OBS agregar una **Fuente de navegador** con `http://127.0.0.1:8765/overlay.html`, 1920 × 1080.
5. El panel se abre en `http://127.0.0.1:8765/panel.html`.

## Biblioteca de gráficos y Dock

- **Editor de Lower Thirds:** `http://127.0.0.1:8765/studio.html`, o el acceso desde el panel. Permite elegir Clásica, Minimalista, Litúrgica o Moderna, editar nombre/cargo/subtítulo, colores, opacidad y animaciones. «Probar entrada/salida» solo modifica la vista previa del editor.
- **Guardar preparación:** guarda el estilo y texto en la configuración local sin cambiar lo que OBS está emitiendo.
- **Publicar en OBS:** actualiza la salida para mostrar el Lower Third personalizado. «Imagen limpia» lo retira inmediatamente; «Restaurar» recupera la preparación vigente.
- **Dock:** `http://127.0.0.1:8765/dock.html`, para añadir como Dock de navegador personalizado en OBS. Comparte el mismo estado local con el panel y el editor; ofrece edición rápida del texto y acceso al editor completo.
- Los niveles **Esencial, Personalizar y Avanzado** controlan qué ajustes se ven, sin publicar ni borrar cambios.

Para verificar la integración en una PC de pruebas: abrir el editor, guardar un nombre y confirmar que no cambia OBS; publicar, comprobar animación; limpiar, restaurar, y repetir desde el Dock. No utilizar una transmisión real para la primera validación.

## Datos locales y privacidad

Cada instalación funciona en su propia PC, ligada a `127.0.0.1`; no usa cuentas ni sincronización en la nube. Las preferencias quedan en `configuracion.json`, y las imágenes/videos cargados en la carpeta `media/`. **Estos archivos no deben subirse a GitHub.** Para copia de seguridad, guardar ambos por separado en un lugar privado. El software no se actualiza automáticamente.

## Notas

Los colores de las fiestas y solemnidades deben comprobarse según el calendario litúrgico correspondiente. El operador mantiene el control de cuándo aparecen los gráficos; la aplicación no automatiza la celebración. El servidor no debe exponerse a internet sin añadir autenticación y medidas de seguridad.

## Desarrollo

`launcher.py`: aplicación de escritorio; `servidor.py`: servicio local; `panel.html`: consola; `studio.html`: editor de Lower Thirds; `dock.html`: Dock de control; `overlay.html`: salida OBS. `PLAN_V9.md`: otras mejoras previstas, no implementadas.

**Estado de esta rama de integración:** pruebas locales de contrato HTTP realizadas; validación visual y funcional en Windows/OBS y compilación de sus nuevos artefactos pendientes antes de integrar o publicar.

## Experiencia de uso

La interfaz emplea **complejidad progresiva**: niveles Esencial, Personalizar y Avanzado sin perder los controles críticos de transmisión. Consulta [principios de UX](docs/UX_COMPLEJIDAD_PROGRESIVA.md) y [lista de validación](tests/VALIDACION_UX.md).
