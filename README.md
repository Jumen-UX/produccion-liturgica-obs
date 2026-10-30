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
- Indicador de gráfico **AL AIRE**, **EN PROGRAMA**, **FUERA DE PROGRAMA** o **SIN VERIFICAR**, consultando OBS WebSocket en el equipo local.
- Acceso remoto LAN opcional, mediante QR, con contraseñas de operador/consulta, sesiones revocables y actualización del estado sin recargar la página.

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

Si ejecutas desde código fuente (sin EXE) y quieres generar QR, instala una vez `python -m pip install qrcode` antes de iniciar el programa. El EXE Windows incorpora esa dependencia.

## Biblioteca de gráficos y Dock

- **Editor de Lower Thirds:** `http://127.0.0.1:8765/studio.html`, o el acceso desde el panel. Permite elegir Clásica, Minimalista, Litúrgica o Moderna, editar nombre/cargo/subtítulo, colores, opacidad y animaciones. «Probar entrada/salida» solo modifica la vista previa del editor.
- **Guardar preparación:** guarda el estilo y texto en la configuración local sin cambiar lo que OBS está emitiendo.
- **Publicar en OBS:** actualiza la salida gráfica para mostrar el Lower Third personalizado. «Imagen limpia» lo retira inmediatamente; «Restaurar» recupera exactamente el último gráfico visible, aunque el borrador haya cambiado. El estado «Gráfico visible» no indica si OBS ha iniciado la transmisión.
- **Panel web:** `http://127.0.0.1:8765/panel.html`. Aquí se preparan los gráficos, los participantes, la portada, el logo y las paletas. El formulario «Preparar un gráfico» muestra solo los campos adecuados al tipo elegido: por ejemplo, título y referencia para lecturas, o título y mensaje para la espera. «Guardar sin mostrar» conserva la preparación; «Mostrar en OBS» la emite.
- **Dock:** `http://127.0.0.1:8765/dock.html`, para añadir como Dock de navegador personalizado en OBS. Es exclusivamente un **lanzador durante la transmisión**: gráficos preparados en el panel, Lower Third, participante, pantalla de espera, cuenta regresiva, imagen limpia, logo y redes. No permite editar nombres, textos ni diseños; ofrece enlaces al panel y al Estudio para configurarlos.
- **Volver al panel:** el Estudio incluye el acceso «Volver al panel principal».
- Los niveles **Esencial, Personalizar y Avanzado** controlan qué ajustes se ven, sin publicar ni borrar cambios.

### Comprobación del gráfico en programa de OBS

1. Dentro de OBS, habilitar **Herramientas → Ajustes del servidor WebSocket**. El puerto usual es `4455`; utilizar autenticación cuando esté disponible.
2. En el panel web, abrir **Avanzado → Conexión y verificación de OBS**. Escribir el nombre **exacto** de la Fuente de navegador usada para `overlay.html` (por ejemplo, «Navegador 2»), el puerto y la contraseña WebSocket, si OBS la exige. Pulsar «Guardar y verificar OBS».
3. El Dock y el panel mostrarán **AL AIRE** solamente si el gráfico está publicado, la fuente aparece activa en la salida de programa y OBS confirma una transmisión activa. **EN PROGRAMA** indica que la fuente está en programa sin transmisión activa. **FUERA DE PROGRAMA** significa que la fuente no está activa en programa. **SIN VERIFICAR** indica que falta configuración, conexión o confirmación de OBS.
4. «Imagen limpia» y «Restaurar» siguen disponibles aunque OBS WebSocket no esté conectado; no se bloquea la operación de los gráficos.

La conexión consulta solamente `GetStreamStatus` y `GetSourceActive`; no inicia ni detiene transmisiones y nunca modifica escenas. El nombre y puerto se conservan en `conexion_obs.json`; **la contraseña solo permanece en memoria durante la ejecución**, no se guarda en archivos ni se envía de vuelta a los navegadores. Por seguridad, la conexión se limita a `127.0.0.1`.

La comprobación de actividad de una fuente no puede detectar si otra capa opaca la tapa visualmente; verifica su participación en el programa de OBS, no analiza píxeles de la transmisión final. La prueba real en Windows/OBS sigue pendiente.

## Control remoto en la misma red

El panel y la Fuente de navegador de OBS **siguen siempre en `127.0.0.1:8765`**. El acceso remoto es un segundo servicio, inicialmente desactivado, que al habilitarse escucha en el puerto `8766` (configurable) de la red local. **No uses el puerto 8766 como fuente de navegador de OBS.**

1. En la computadora que ejecuta OBS, abre el **Panel → Avanzado → Acceso remoto por red local**.
2. Establece una contraseña de **operador** de al menos 12 caracteres; opcionalmente, una diferente de **solo consulta**. Activa el acceso y pulsa «Guardar acceso remoto».
3. La sección mostrará una o varias direcciones y un **QR**. Selecciona la dirección correspondiente al Wi-Fi/LAN usado por los dispositivos. El QR contiene solo la URL de inicio de sesión, nunca una contraseña.
4. En el teléfono o tableta, conéctate a la **misma red privada** y escanea el QR. Introduce la contraseña. El operador puede lanzar, limpiar y restaurar gráficos, controlar la cuenta regresiva, el logo y las redes; el perfil de consulta solo observa.
5. Los cambios de otros operadores aparecen automáticamente mediante notificaciones locales del servidor; «AL AIRE» sigue dependiendo de la verificación de OBS configurada en el panel principal.
6. Para expulsar dispositivos, usa «Desconectar dispositivos»; para terminar el acceso, desactiva la casilla y guarda.

**Seguridad y limitaciones:** las contraseñas se guardan como verificadores PBKDF2, no en texto plano, en `acceso_lan.json` dentro de los datos locales. Las sesiones se mantienen en memoria hasta ocho horas o revocación; hay límite de intentos fallidos. El puerto LAN ofrece exclusivamente las páginas de inicio de sesión/control, estado y comandos de operador permitidos. No expone `/panel.html`, `/studio.html`, `/overlay.html`, archivos internos, carga de medios ni configuración OBS. No habilites reenvío de puertos en el router.

**El HTTP de red local no cifra credenciales ni comandos en tránsito.** Utiliza solo una red privada y de confianza, con acceso Wi-Fi protegido; no lo uses en redes públicas ni lo publiques en Internet. Para acceso a través de redes no confiables será necesaria una solución futura con TLS o VPN.

Si el móvil no puede conectar, revisa la dirección IP correcta, el firewall de Windows (permite el **puerto TCP configurado solo en redes privadas y subred local**) y que el router no tenga aislamiento de clientes/invitados. El instalador no cambia automáticamente las reglas del firewall. Consulta [la guía detallada](docs/ACCESO_REMOTO_LAN.md).

Para verificar la integración en una PC de pruebas: abrir el editor, guardar un nombre y confirmar que no cambia OBS; publicar, comprobar animación; limpiar, restaurar, y repetir desde el Dock. No utilizar una transmisión real para la primera validación.

## Datos locales y privacidad

Cada instalación funciona en su propia PC sin nube. El panel administrativo y el overlay siguen ligados a `127.0.0.1`; el acceso LAN es opcional. Las preferencias quedan en `configuracion.json`, la configuración no secreta de OBS en `conexion_obs.json`, los verificadores de acceso en `acceso_lan.json` y las imágenes/videos en `media/`. **Estos archivos no deben subirse a GitHub.** Para copia de seguridad, guardar esos datos por separado en un lugar privado. El software no se actualiza automáticamente.

## Notas

Los colores de las fiestas y solemnidades deben comprobarse según el calendario litúrgico correspondiente. El operador mantiene el control de cuándo aparecen los gráficos; la aplicación no automatiza la celebración. El servidor no debe exponerse a internet sin añadir autenticación y medidas de seguridad.

## Desarrollo

`launcher.py`: aplicación de escritorio; `servidor.py`: servicio local y rutas HTTP; `lan_access.py`: credenciales, roles y servicio LAN; `login.html` y `remote.html`: acceso desde móviles; `obs_monitor.py`: consulta WebSocket local de OBS; `panel.html`: consola; `studio.html`: editor de Lower Thirds; `dock.html`: Dock de control; `overlay.html`: salida OBS. `PLAN_V9.md`: otras mejoras previstas, no implementadas.

**Estado de esta rama de integración:** pruebas locales de contrato HTTP realizadas; validación visual y funcional en Windows/OBS y compilación de sus nuevos artefactos pendientes antes de integrar o publicar.

## Experiencia de uso

La interfaz emplea **complejidad progresiva**: niveles Esencial, Personalizar y Avanzado sin perder los controles críticos de transmisión. Consulta [principios de UX](docs/UX_COMPLEJIDAD_PROGRESIVA.md) y [lista de validación](tests/VALIDACION_UX.md).
