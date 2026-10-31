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

## Inicio directo en Windows

Al ejecutar `ProduccionLiturgicaOBS.exe`, el servidor arranca en segundo plano y se abre automáticamente `http://127.0.0.1:8765/panel.html` en el navegador predeterminado. **No aparece una ventana de bienvenida separada** cuando la bandeja de sistema funciona. El icono de Producción Litúrgica OBS, junto al reloj de Windows (puede estar dentro de los iconos ocultos), permite **Abrir panel web** o **Cerrar sistema** con confirmación. Cerrar la pestaña del navegador no detiene el servidor ni la salida de OBS.

Si se ejecuta de nuevo el EXE, se abre el panel de la instancia existente sin iniciar otro servidor. Si otro proceso ocupa el puerto, se muestra un error y no se abre una página ajena. Si Windows no puede mostrar el icono de bandeja por falta de dependencias, aparece un control mínimo de respaldo para abrir el panel y cerrar el servidor de forma segura. Configuración de OBS y red LAN siguen dentro del panel.

## Descargas de Windows (al publicar una versión)

- Instalador: `ProduccionLiturgicaOBS-Setup.exe`, instalación por usuario, accesos directos y desinstalación.
- Portátil: `ProduccionLiturgicaOBS-Portable.zip`, descomprimir y abrir el EXE.
- Ninguna descarga necesita Python en el PC del operador.
- Los datos de cada parroquia se conservan en `%LOCALAPPDATA%\ProduccionLiturgicaOBS` fuera de la carpeta del programa.
- Para actualizar una instalación hecha con el instalador, **cierra primero la aplicación y ejecuta el nuevo instalador**: el identificador de instalación (`AppId`) se mantiene fijo para actualizar en el mismo lugar. No desinstales manualmente ni borres los datos de `%LOCALAPPDATA%`. Si usabas un ZIP portátil o un EXE suelto, elimina las copias antiguas solo después de verificar que la nueva abre y conserva tus datos.

### GitHub Actions

El flujo `.github/workflows/windows-release.yml` compila y prueba el ejecutable, crea instalador y ZIP. Además, en un **runner Windows desechable**, compila una versión anterior simulada del mismo paquete y prueba instalarla, actualizarla y desinstalarla, comprobando que hay una sola entrada instalada y que los datos locales sobreviven. **Esta prueba automatizada no sustituye actualizar una versión verdaderamente antigua en una PC del operador.** Los pull requests generan artefactos de prueba. Solo las etiquetas `vX.Y.Z` publican en GitHub Releases. **No publicar versiones estables sin validar en Windows y OBS.**

## Instalación en Windows (código fuente)

1. Extraer todo el ZIP a una carpeta **con permiso de escritura** (por ejemplo Documentos\Produccion-Liturgica). No ejecutarlo desde dentro del ZIP ni desde Archivos de programa.
2. Con Python 3 instalado, ejecutar `INICIAR_SIN_EXE.bat`; o construir el ejecutable usando `CREAR_EXE_WINDOWS.bat` desde Windows con Python 3.
3. Configurar el nombre de la comunidad en **Identidad de la comunidad**, guardar y publicar.
4. En OBS agregar una **Fuente de navegador** con `http://127.0.0.1:8765/overlay.html`, 1920 × 1080.
5. El panel se abre en `http://127.0.0.1:8765/panel.html`.

Si ejecutas desde código fuente (sin EXE) y quieres generar QR, instala una vez `python -m pip install qrcode` antes de iniciar el programa. El EXE Windows incorpora esa dependencia.

## Biblioteca de producciones (primera fase)

Desde el panel principal entra a **Biblioteca de producciones**, o abre `http://127.0.0.1:8765/biblioteca.html`. Permite crear producciones, guardar varios recursos por categoría, editarlos, duplicarlos, habilitarlos/deshabilitarlos, eliminarlos y cambiar su orden. Incluye una producción de ejemplo editable y almacena el catálogo en `%LOCALAPPDATA%\\ProduccionLiturgicaOBS\\producciones.json` (o junto al código en ejecución de desarrollo). No sobrescribe la configuración existente `configuracion.json`.

Los Lower Thirds y los elementos de texto (títulos, lecturas, salmos, avisos y frases) admiten **lanzamiento individual** tanto desde la biblioteca como desde una sección específica del Dock. El diseño de cada Lower Third puede heredar la plantilla guardada en Estudio o personalizarla por elemento (nombre, cargo, plantilla, colores y animaciones). Los ítems sin soporte de lanzamiento siguen siendo **registros preparados**: vídeos, imágenes, créditos y otros formatos necesitan una fase posterior.

### Rotación individual de redes
En la categoría **Redes sociales** añade tantos ítems como necesites. Cada registro tiene nombre, plataforma, usuario/enlace, frase e icono de la red. Puedes sustituir el icono por un PNG/JPG/WEBP propio desde el panel local. La lista incluye ejemplos editables; no se exige conectar cuentas externas.

Configura la duración visible (3 a 30 segundos), intervalo entre inicios (hasta 900 segundos), repetición y ubicación (espera, directo, cierre o todos). Pulsa **Iniciar rotación** en Biblioteca o Dock. La salida muestra **solo una red por turno**, nunca toda la lista simultáneamente. Pulsa **Detener rotación** para ocultar las redes. Una rotación ya iniciada conserva la lista original hasta que la reinicies; las ediciones no alteran inadvertidamente el contenido en directo.

### Vista previa fiel a la salida OBS
El panel web, el Estudio y la Biblioteca emplean **el mismo motor HTML/CSS de `overlay.html`**, con un marco de 1920 × 1080 reducido proporcionalmente. La vista previa recibe una configuración local aislada y **no cambia el gráfico publicado**, ni depende de que OBS esté transmitiendo. Para comparar, configura la Fuente de navegador de OBS a 1920 × 1080 y sin CSS personalizado que altere el tamaño. Diferencias menores pueden deberse a las fuentes y a la versión de Chromium integrada en OBS.

El indicador **AL AIRE** continúa dependiendo de OBS WebSocket: un dibujo en la vista previa no confirma que el gráfico esté en Programa ni que se esté transmitiendo. La prueba visual en OBS real sigue pendiente.

## Biblioteca de gráficos y Dock

- **Editor de Lower Thirds:** `http://127.0.0.1:8765/studio.html`, o el acceso desde el panel. Permite elegir Clásica, Minimalista, Litúrgica o Moderna, editar nombre/cargo/subtítulo, colores, opacidad y animaciones. «Probar entrada/salida» solo modifica la vista previa del editor.
- **Guardar preparación:** guarda el estilo y texto en la configuración local sin cambiar lo que OBS está emitiendo.
- **Publicar en OBS:** actualiza la salida gráfica para mostrar el Lower Third personalizado. «Imagen limpia» lo retira inmediatamente; «Restaurar» recupera exactamente el último gráfico visible, aunque el borrador haya cambiado. El estado «Gráfico visible» no indica si OBS ha iniciado la transmisión.
- **Panel web:** `http://127.0.0.1:8765/panel.html`. Aquí se preparan los gráficos, los participantes, la portada, el logo y las paletas. El formulario «Preparar un gráfico» muestra solo los campos adecuados al tipo elegido: por ejemplo, título y referencia para lecturas, o título y mensaje para la espera. «Guardar sin mostrar» conserva la preparación; «Mostrar en OBS» la emite.
- **Dock:** `http://127.0.0.1:8765/dock.html`, para añadir como Dock de navegador personalizado en OBS. Es exclusivamente un **lanzador durante la transmisión**: gráficos preparados en el panel, Lower Third, participante, pantalla de espera, cuenta regresiva, imagen limpia, logo y redes. No permite editar nombres, textos ni diseños; ofrece enlaces al panel y al Estudio para configurarlos.
- **Volver al panel:** el Estudio incluye el acceso «Volver al panel principal».
- Los niveles **Esencial, Personalizar y Avanzado** controlan qué ajustes se ven, sin publicar ni borrar cambios.

### Comprobación del gráfico en programa de OBS

1. Utilizar preferentemente **OBS Studio 28 o posterior**, que ya incluye **obs-websocket 5.x**. No es necesario instalar un plugin adicional. Dentro de OBS, habilitar **Herramientas → Ajustes del servidor WebSocket**. El puerto usual es `4455`; mantener la autenticación activada.
2. En el panel, despliega **Conexiones · OBS y teléfono** y abre **1. Conectar OBS** (disponible incluso en el modo Esencial). Pulsa **«Detectar OBS y fuente automáticamente»**: con OBS abierto y WebSocket activado, la aplicación busca la Fuente de navegador que apunte a `http://127.0.0.1:8765/overlay.html` y, si encuentra exactamente una, guarda su nombre automáticamente. Si OBS exige contraseña, introdúcela y repite. El puerto **4455** ya está preconfigurado. En caso de varias fuentes coincidentes o ninguna, utiliza **«Configurar manualmente»**; el programa nunca elige una fuente dudosa.
3. El Dock y el panel mostrarán **AL AIRE** solamente si el gráfico está publicado, la fuente aparece activa en la salida de programa y OBS confirma una transmisión activa. **EN PROGRAMA** indica que la fuente está en programa sin transmisión activa. **FUERA DE PROGRAMA** significa que la fuente no está activa en programa. **SIN VERIFICAR** indica que falta configuración, conexión o confirmación de OBS.
4. «Imagen limpia» y «Restaurar» siguen disponibles aunque OBS WebSocket no esté conectado; no se bloquea la operación de los gráficos.

El monitor mantiene una conexión WebSocket durante las consultas periódicas; la reutiliza hasta que falla o cambia la configuración. El diagnóstico aprovecha las confirmaciones recientes para evitar conexiones adicionales mientras OBS responde.

**Diagnóstico automático:** al abrir el panel se prueba la conexión local con WebSocket 5.x, incluso antes de configurar el nombre de la fuente. Si falta contraseña, es incorrecta, responde un protocolo incompatible o el servidor no está accesible, aparece una advertencia en **todos los niveles** (incluido Esencial) con instrucciones y el botón «Volver a comprobar». Cuando el puerto no responde, el programa **no afirma que el complemento esté ausente**: también puede ocurrir porque OBS está cerrado, el servidor está deshabilitado o el puerto es distinto. El instalador de Windows muestra estos requisitos; **no modifica OBS ni instala automáticamente plugins**. En OBS antiguos, actualizar a la versión 28 o posterior es la opción recomendada.

La conexión consulta solamente `GetStreamStatus` y `GetSourceActive`; no inicia ni detiene transmisiones y nunca modifica escenas. El nombre y puerto se conservan en `conexion_obs.json`; **la contraseña solo permanece en memoria durante la ejecución**, no se guarda en archivos ni se envía de vuelta a los navegadores. Por seguridad, la conexión se limita a `127.0.0.1`.

La comprobación de actividad de una fuente no puede detectar si otra capa opaca la tapa visualmente; verifica su participación en el programa de OBS, no analiza píxeles de la transmisión final. La prueba real en Windows/OBS sigue pendiente.

## Control remoto en la misma red

El panel y la Fuente de navegador de OBS **siguen siempre en `127.0.0.1:8765`**. El acceso remoto es un segundo servicio, inicialmente desactivado, que al habilitarse escucha en el puerto `8766` (configurable) de la red local. **No uses el puerto 8766 como fuente de navegador de OBS.**

1. En la computadora que ejecuta OBS, abre el panel. Despliega **Conexiones · OBS y teléfono** para acceder a **«2. Conectar teléfono o tableta»**, también en **Esencial**.
2. Establece una contraseña de **operador** de al menos 12 caracteres, marca **«Permitir control desde la misma red»** y pulsa **«Activar y generar QR»**. El puerto **8766** ya viene configurado. Para un usuario de **solo consulta**, despliega «Opciones adicionales de red y permisos».
3. La misma tarjeta mostrará una o varias direcciones y un **QR**. Selecciona la dirección correspondiente al Wi-Fi/LAN usado por los dispositivos. Si el servidor no arranca o el QR falla, aparece un mensaje explicativo. El QR contiene solo la URL de inicio de sesión, nunca una contraseña.
4. En el teléfono o tableta, conéctate a la **misma red privada** y escanea el QR. Introduce la contraseña. El operador puede lanzar, limpiar y restaurar gráficos, controlar la cuenta regresiva, el logo y las redes; el perfil de consulta solo observa.
5. Los cambios de otros operadores aparecen automáticamente mediante notificaciones locales del servidor; «AL AIRE» sigue dependiendo de la verificación de OBS configurada en el panel principal.
6. Para expulsar dispositivos, usa «Desconectar dispositivos»; para terminar el acceso, desactiva la casilla y guarda.

**Comprobación importante:** «Servidor LAN activo» y «QR generado» significan que el servicio funciona en la computadora y el código representa una dirección válida. **No prueban** que el teléfono pueda entrar; eso depende también del firewall, la red y el router. La validación se completa al abrir la dirección desde el teléfono, iniciar sesión y observar/ejecutar un gráfico en una prueba con OBS.

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

## Tamaño de los controles

El Dock, el control remoto y el panel web se reorganizan según el ancho disponible: los botones y las filas pasan a una columna en espacios estrechos y los textos pueden ocupar varias líneas. En ventanas bajas, los controles superiores dejan de ser fijos para no tapar el contenido.

En el Dock y el remoto, el estado y los botones de limpiar/restaurar aparecen antes de los gráficos preparados. Logo y redes están en un desplegable. En el panel web estrecho, el monitor de salida aparece primero; «Ver vista de salida» abre la previsualización y «Ir a participantes» abre los nombres. Los ajustes de conexión e identidad siguen accesibles sin publicar ningún gráfico.

Prueba automatizada de interfaz con Chromium y servidor simulado: `node tests/test_responsive_interfaces.cjs`. La comprobación final dentro de OBS y en el teléfono sigue siendo necesaria.
