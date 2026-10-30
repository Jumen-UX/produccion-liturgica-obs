# Guía de acceso remoto por red local

El acceso remoto permite lanzar los gráficos preparados desde teléfonos y tabletas sin trasladar la configuración de OBS ni crear una cuenta en la nube.

## Preparación en la computadora principal

1. Conecta la computadora que ejecuta OBS a la red que usarán los demás dispositivos. Puede ser Ethernet y Wi-Fi del mismo router; el router debe permitir comunicación entre ellos.
2. Abre `http://127.0.0.1:8765/panel.html` y selecciona **Avanzado**.
3. Busca **Acceso remoto por red local**. La función inicia desactivada.
4. Escribe una contraseña nueva de operador de **12 a 128 caracteres**. Si habrá alguien que solo observará el estado, escribe otra contraseña para **solo consulta**. Evita reutilizar contraseñas personales.
5. Marca **Habilitar acceso desde otros dispositivos** y guarda. El puerto predeterminado es **8766**; puedes cambiarlo si otro programa lo usa.
6. En la misma sección, selecciona la dirección que corresponde a tu red. Abre esa dirección en el teléfono o escanea el QR mostrado.
7. Si Windows muestra una advertencia del firewall, permite el acceso **solo para redes privadas** cuando confíes en la red. Si no aparece y el móvil no conecta, configura manualmente una regla de entrada TCP para el puerto LAN elegido, restringida al perfil **Privado** y a la **subred local**. Esta regla puede requerir permisos de administrador.

No se necesitan aplicaciones adicionales en el celular. El QR contiene la dirección de acceso, **no** contiene la clave.

## Qué puede hacer cada persona

| Perfil | Consultar estado | Lanzar/limpiar/restaurar | Configurar gráficos/OBS |
| --- | --- | --- | --- |
| Operador remoto | Sí | Sí | No |
| Solo consulta | Sí | No | No |
| Administrador en la PC de OBS | Sí | Sí | Sí |

El **Dock de OBS** continúa funcionando en `http://127.0.0.1:8765/dock.html`. La **Fuente de navegador** conserva `http://127.0.0.1:8765/overlay.html`. El teléfono utiliza el **puerto LAN**, no el del overlay.

## Qué significa el indicador

- **AL AIRE:** el monitor local de OBS confirma transmisión activa y fuente gráfica activa en Programa.
- **EN PROGRAMA:** la fuente está activa en Programa, pero no hay transmisión activa.
- **FUERA DE PROGRAMA:** OBS no detecta la fuente activa en Programa.
- **IMAGEN LIMPIA:** el servidor ha ocultado el gráfico.
- **SIN VERIFICAR:** faltan datos o la comunicación con OBS no se ha confirmado. No implica que la emisión esté funcionando.

El panel remoto recibe notificaciones de cambios por eventos del servidor (SSE) y además comprueba periódicamente el estado. Si se interrumpe la red, indica desconexión y vuelve a consultar al recuperar comunicación.

## Seguridad, acceso y recuperación

- El acceso LAN está **desactivado por defecto**. La configuración administrativa nunca se ofrece por el puerto remoto.
- La contraseña se verifica con un hash derivado PBKDF2-SHA256 y sal aleatoria. El archivo `acceso_lan.json` no contiene contraseñas de texto; exclúyelo de respaldos públicos y de Git.
- Cada inicio de sesión recibe una cookie `HttpOnly` y `SameSite=Strict`. Las sesiones caducan a las **8 horas**, se invalidan al cambiar la configuración y pueden revocarse manualmente.
- Tras **5 contraseñas fallidas en 5 minutos** desde un mismo dispositivo, se limita temporalmente el acceso.
- Usa una red Wi-Fi **privada, protegida y de confianza**. El servicio LAN funciona con HTTP sin cifrado de transporte; no uses Wi-Fi de invitados no confiable ni abras el puerto hacia Internet. El cifrado HTTPS o una VPN es requisito para otros escenarios de red.
- Si el teléfono se pierde o cambia el operador, entra en Avanzado desde la computadora de OBS, pulsa **Desconectar dispositivos** y cambia la contraseña. Para una medida inmediata, desactiva el acceso remoto y guarda.
- Si el servicio LAN falla, la consola local, el Dock y el overlay continúan independientes en el puerto 8765.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No aparece dirección ni QR | Comprueba conexión LAN, dirección IPv4 del equipo y dependencia `qrcode` si ejecutas desde Python fuente. |
| El QR abre una página que no responde | Revisa red privada, reglas TCP del firewall para el puerto elegido y aislamiento de dispositivos en el router. |
| Contraseña rechazada | Utiliza la clave de operador o de consulta establecida en esta instalación; espera cinco minutos si hubo múltiples fallos. |
| Se ven gráficos pero no se pueden lanzar | Has iniciado sesión con el perfil de solo consulta. |
| Dice «SIN VERIFICAR» | Configura el monitor OBS WebSocket en el panel de la PC; el acceso LAN no cambia esa configuración. |
| Después de desactivar, el móvil se desconecta | Es el comportamiento esperado. El panel de OBS permanece accesible localmente. |

## Validación antes de una transmisión real

Prueba con dos teléfonos en la misma LAN: uno con permisos de operador y otro de consulta. Guarda un gráfico en el panel de la PC sin publicarlo; confirma que no aparece en OBS, lánzalo desde el móvil, comprueba el estado en el otro dispositivo, limpia y restaura. Prueba a deshabilitar el acceso y verifica que ninguno de los dos pueda seguir dando órdenes. La instalación real en Windows y la verificación visual en OBS deben completarse antes de publicar una versión estable.
