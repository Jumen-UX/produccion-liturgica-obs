# Principio de diseño: complejidad progresiva

## Objetivo
Una sola aplicación, utilizable por un voluntario nuevo y por un productor experimentado. Las funciones deben descubrirse según la tarea sin obligar a configurar opciones que no hacen falta.

## Niveles de interfaz
- **Esencial (predeterminado):** identidad básica, preparación y publicación, participantes, cuenta regresiva y control inmediato de OBS.
- **Personalizar:** paletas litúrgicas, portadas, anuncios con fotografías, redes sociales y logo.
- **Avanzado:** funciones menos frecuentes o de producción, como logo animado persistente.

Los niveles **no son permisos ni roles de seguridad**. Son preferencias reversibles de visualización, guardadas en el navegador local. Cambiar de nivel no modifica ni publica datos.

## Reglas obligatorias
1. **Siempre visible:** estado del servidor, estado de emisión, botón Imagen limpia, botón Restaurar y vista de programa.
2. **Preparar ≠ Emitir:** los cambios de datos o diseño no aparecen al aire hasta pulsar Publicar en OBS.
3. **No usar temporización para avanzar automáticamente en la liturgia:** el operador decide cuándo cambiar.
4. **Una tarea sencilla no exige abrir ajustes avanzados**; desde la vista esencial se ofrecen accesos contextuales a Personalizar.
5. **Reversibilidad:** controles de restauración, guardado de configuración local y valores predeterminados.
6. **Accesibilidad:** etiquetas, tabulación, foco visible, contraste, indicación textual de los estados y animaciones reducidas si el sistema lo solicita.
7. **Estabilidad:** agregar capas visuales sin cambiar las API ni perder configuraciones anteriores.
8. **Seguridad en directo:** no tapar el control de imagen limpia; no poner confirmación bloqueante al limpiar la emisión.
9. **Respeto litúrgico:** durante la plegaria eucarística se recomienda imagen limpia; no activar anuncios automáticos en esos momentos.

## Aplicación por módulo
| Módulo | Esencial | Personalizar | Avanzado |
|---|---|---|---|
| Configuración | Nombre de comunidad | Logo, color, portada | Biblioteca de marca y presets |
| Celebración | Momento y participantes | Secuencia editable | Guiones reutilizables y asignaciones |
| Gráficos | Plantilla y texto | Colores, tipo y transición | Composición y capas |
| Avisos | Mensaje breve | Imágenes y orden | Programación contextual |
| OBS | Mostrar, limpiar, restaurar | Logo y redes | Escenas y controles avanzados |

**Aplicación actual:** el panel web centraliza la configuración. El formulario de gráficos revela campos según el tipo seleccionado y tiene accesos directos a logo, color y portada. El Estudio de Lower Thirds incorpora sus niveles progresivos y un regreso al panel. El Dock integrado es un lanzador de gráficos ya configurados y mantiene visibles controles críticos (Imagen limpia y Restaurar), sin editores ni formularios.

## Criterios de aceptación
- Al abrir una instalación nueva aparece Esencial.
- Cambiar de nivel no llama a /api/update ni publica nada.
- Se puede regresar a Esencial sin perder el formulario ya preparado.
- Imagen limpia y Restaurar permanecen visibles en los tres niveles.
- Estado de conexión y estado de emisión permanecen visibles.
- En Personalizar se accede al logo, portadas, avisos y redes.
- El logo persistente se muestra en Avanzado.
- La preferencia se conserva al recargar (si localStorage está habilitado).
- Navegación por teclado y pantallas estrechas mantienen los controles críticos accesibles.
- Se realizan pruebas de regresión de guardar borrador / publicar / limpiar / restaurar.
- El Dock no tiene campos de configuración: sus botones de lanzamiento usan los valores preparados por el panel y el Estudio.
- El formulario principal presenta únicamente los datos relevantes al gráfico seleccionado, con ayuda contextual.

## Futuras decisiones
- Diferenciar preferencia de interfaz de permisos de operador, si se incorporan perfiles.
- Integrar estas reglas en Biblioteca de Gráficos, Dock OBS y asistente inicial.
- Evaluar si hay que guardar preferencias de nivel por operador, no por máquina.
