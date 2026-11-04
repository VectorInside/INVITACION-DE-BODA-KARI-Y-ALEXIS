# Registro de decisiones de la entrega

Este registro explica el resultado actual para el equipo que no participó en el chat. No contiene conversaciones privadas, grabaciones ni credenciales adicionales.

| Decisión | Motivo | Consecuencia o límite |
| --- | --- | --- |
| Película voluntaria como entrada narrativa | El material de entrevistas y fotos es el centro de la experiencia | La información y los formularios son accesibles sin verla |
| Aviso de audífonos y horizontal antes del iframe | Cuidar escucha e imagen desde celular | No se fuerza orientación ni fullscreen del dispositivo |
| YouTube para el montaje final | El archivo final local era de cientos de MB | Dependencia de calidad adaptativa y permisos del proveedor; comprobar iframe en dominio final |
| Azul, dorado y marfil | Preferencia del responsable y carácter de la celebración | Mantener contraste y legibilidad al modificar colores |
| Tipografía editorial + sans serif | Equilibrar emoción y datos prácticos | Fuentes locales, licencias incluidas |
| Logo blanco original con transparencia | Firma de Vector Inside sin un rectángulo negro en el pie | HTML usa nombre de asset nuevo para evitar caché previa |
| Galería de 12 con pequeñas y completas | Mantener peso bajo al recorrer sin perder ampliación | Respetar rutas y correspondencia del visor |
| Abanico de 5 fotos que reutiliza la galería | Adaptar la profundidad vista en la referencia de movimiento | No son 5 fotos nuevas ni cambian el conteo del álbum |
| Desplazamiento nativo | Favorecer uso táctil y accesibilidad | Sin scroll secuestrado ni dependencia de una librería de animación |
| Reducción de movimiento por preferencia del sistema | Evitar imponer efectos a quien los desactiva | Mantener fallback visible al tocar CSS/JS |
| Respuesta no disponible tras juego breve | Mantener tono lúdico solicitado sin impedir declinar | No convertirlo en un botón imposible de usar |
| RSVP guardado primero, WhatsApp opcional | Tener totales reales en el panel | El mensaje de WhatsApp no es la fuente de esos totales |
| Token de edición por navegador | Permitir correcciones de una respuesta sin cuenta | Puede haber duplicados entre dispositivos; no es verificación de identidad |
| Acompañantes declarados | Ofrecer un primer conteo útil sin lista nominal provista | No asigna ni valida cupos individuales |
| QR con URL de Google Maps, datos del invitado impresos aparte | Facilitar llegada al lugar y conservar cotejo manual por referencia | El QR no firma, valida ni automatiza acceso |
| Fotos pendientes hasta aprobación | Evitar publicar cualquier envío sin revisión | Necesita que organizadores revisen la cola |
| Ocultar en vez de borrar desde el panel | Facilitar corregir decisiones de publicación | Los archivos continúan consumiendo almacenamiento |
| Panel bajo /admin con contraseña compartida | Operación sencilla para un solo evento | No hay identidad o auditoría por organizador |
| Contraseña en README, por instrucción expresa | El responsable pidió entregarla así al equipo | En repo público es conocida; debe acordarse protección externa antes de usar datos reales |
| Backend local Python + SQLite | Validar todas las interacciones sin configurar servicios cloud | El alojamiento público y su endurecimiento siguen pendientes |
| Git con fuente y recursos preparados | Que el equipo pueda continuar sin depender del entorno del chat | Datos operativos y material privado no deben viajar con el código |

## Fuente de datos de la boda

Los nombres completos y sus acentos fueron confirmados directamente por el responsable. La grabación de conversación proporcionada confirmó recepción 1 p. m., ceremonia a las 2 y vestimenta formal, con excepción de azul marino para hombres. El responsable confirmó después el año 2026 y que la ceremonia se realiza en el mismo salón de Residencial Alboreto. Google Maps se consultó para verificar el residencial y su dirección. No se derivaron horarios de EXIF ni se inventó el tipo de ceremonia.

## Material audiovisual conservado

Se incluye el contenido de `dist/assets/` que tenía la entrega de revisión, incluidas piezas preliminares. El montaje final publicado por el responsable dura 5:23 y se carga desde YouTube. No se recrea ni se reexporta la película final al instalar el proyecto. Los originales de entrevistas, música y conversaciones no son necesarios para ejecutar la aplicación y no se incluyen en este repositorio público.

## Priorización de adecuaciones finales

1. Elegir destino de publicación con backend persistente y HTTPS.
2. Verificar la película insertada en ese destino.
3. Acordar protección del panel público considerando la contraseña documentada.
4. Decidir si se necesita lista nominal, límite de acompañantes por invitación y validación real de QR.
5. Ajustar frecuencia de fotos por IP para la red que se usará durante la boda.
6. Probar de principio a fin con iPhone y Android y realizar respaldo de recuperación.
7. Refinar movimiento, recortes y copy sin cambiar datos confirmados accidentalmente.

## Actualización V13

La película final se reserva para el evento. Las referencias históricas anteriores a la experiencia de video no describen el comportamiento actual: la portada usa fotografía animada y MP3 con inicio voluntario; ver README actualizado. Los archivos MP4 y VTT se retiraron de la carpeta pública. No introducir de nuevo enlaces al montaje final en la invitación.
