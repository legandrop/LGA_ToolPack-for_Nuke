> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Implementación LGA SnapShot Buttons

## Descripción
Sistema de botones personalizados para el viewer de Nuke que permite tomar snapshots, mostrar el último snapshot y acceder a una galería de snapshots organizados por proyecto.

## Archivos del Sistema

### 1. `LGA_ToolPack/init.py`
- **Función**: Registra el callback `OnViewerCreate` que se ejecuta cuando se crea un viewer
- **Importa**: `LGA_viewer_SnapShot_Buttons` para el sistema personalizado de botones

### 2. `LGA_ToolPack/LGA_viewer_SnapShot_Buttons.py`
- **Función**: Script principal que maneja la inserción de botones en el viewer
- **Características**:
  - Inserta tres botones en el viewer de Nuke
  - Los tres contenedores son `QWidget`, **nunca `QDialog`** (ver "Por qué los botones no son QDialog")
  - Los `QPushButton` van con `NoFocus`, así no se comen los atajos del viewer
  - Primer botón (`Take_SnapShotButton`): Ejecuta `take_snapshot()` con detección de Shift (componer) y Ctrl (motor Write)
  - Segundo botón (`Show_SnapShotButton`): Ejecuta `show_snapshot_hold()` con comportamiento hold
  - Tercer botón (`Gallery_SnapShotButton`): Abre la galería de snapshots
  - Usa iconos `snap_camera.png`, `sanp_picture.png` y `sanp_gallery.png`
  - Tooltips en inglés: "Take snapshot and save to gallery - Shift+Click to append it to the right of the previous one", "Show last snapshot in viewer", "Open snapshot gallery"
  - Importación única del módulo para mantener el estado entre llamadas

### 3. `LGA_ToolPack/LGA_viewer_SnapShot.py`
- **Función**: Contiene la lógica principal de snapshot
- **Características**:
  - Compatibilidad con PySide/PySide2
  - Dos motores de captura: `_snapshot_con_capture()` (por defecto) y `_snapshot_con_write()` (el viejo, detrás de Ctrl)
  - Verificaciones de canales válidos antes de renderizar, sólo en el motor Write
  - Recorte del vacío del viewport con `_parece_uniforme()`, `_medir_bandas()` y `_rect_visible()`
  - Función `take_snapshot(save_to_gallery=True, use_write=False, compare=False)` para capturar imagen del viewer
  - Función `show_snapshot_hold()` para mostrar snapshot con control manual
  - Sistema de galería organizado por proyecto con `save_snapshot_to_gallery()`
  - Funciones de proyecto: `get_project_info()`, `get_next_gallery_number()`
  - Función `get_viewer_info()` para obtener información del viewer activo con nodo conectado
  - Función `get_viewer_info_for_show()` para obtener información del viewer permitiendo trabajar sin nodo conectado
  - Integración con sistema RenderComplete para manejo de sonido
  - Sistema de numeración ascendente para snapshots únicos (evita problemas de cache)
  - Funciones auxiliares: `get_next_snapshot_number()`, `cleanup_old_snapshots()`, `get_latest_snapshot_path()`

### 4. `LGA_ToolPack/LGA_viewer_SnapShot_logging.py`
- **Función**: Logger compartido de los otros tres módulos
- **Escribe en**: `LGA_ToolPack/logs/LGA_viewer_SnapShot.log` (ver "Logging")
- **Exporta**: `debug_print()` y `log_error()`, que reemplazan a los `debug_print` sueltos que tenía cada módulo

### 5. `LGA_ToolPack/LGA_viewer_SnapShot_Gallery.py`
- **Función**: Interfaz de galería de snapshots con thumbnails
- **Características**:
  - Ventana con estilo consistente y área de scroll
  - Función principal `open_snapshot_gallery()` 
  - Organización por proyectos con thumbnails redimensionables
  - Toolbar superior con slider de tamaño (50px - 500px)
  - Thumbnails ordenados alfabéticamente por proyecto
  - Soporte para múltiples formatos de imagen (jpg, png, tiff, exr)
  - Interfaz responsiva con hover effects en thumbnails
  - `get_hierotools_image_editor()` resuelve el ejecutable del editor (ver "Editor de imágenes")

## Funcionamiento del Sistema

### Flujo de Trabajo
1. **Inicialización**: Al abrir Nuke, `init.py` se carga automáticamente
2. **Creación de Viewer**: Se ejecuta el callback `OnViewerCreate()`
3. **Inserción de Botones**: `LGA_viewer_SnapShot_Buttons.launch()` busca el frameslider y agrega los botones
4. **Funcionalidad Activa**: Los botones ejecutan las funciones correspondientes

### Verificaciones de Seguridad
- **Viewer activo**: Verifica que hay un viewer disponible
- **Nodo válido**: Para `take_snapshot()` confirma que hay un nodo conectado al viewer
- **Canales válidos**: Sólo en el motor Write. Verifica que el nodo tiene canales de color (RGB/RGBA) ANTES de cualquier procesamiento. El motor por defecto no renderiza nada, así que no aplica
- **Permisos de archivo**: Confirma acceso a carpeta temporal para guardar snapshots
- **Flexibilidad**: `show_snapshot_hold()` funciona con o sin nodo conectado al viewer

## Estructura de Clases

### Take_SnapShotButton
- **Función**: Botón para tomar snapshots
- **Icono**: `snap_camera.png`
- **Tooltip**: "Take snapshot and save to gallery - Shift+Click to append it to the right of the previous one"
- **Comportamiento**: Ejecuta `take_snapshot()` al hacer clic y siempre guarda en galería. Shift compone con el snapshot anterior; Ctrl usa el motor Write, sin anunciarse en el tooltip
- **Requisito**: Necesita nodo conectado al viewer

### Show_SnapShotButton
- **Función**: Botón para mostrar snapshot con control manual
- **Icono**: `sanp_picture.png`
- **Tooltip**: "Show last snapshot in viewer"
- **Comportamiento**: Ejecuta `show_snapshot_hold()` con eventos pressed/released
- **Flexibilidad**: Funciona con o sin nodo conectado al viewer
- **Importación**: Carga el módulo una sola vez para mantener estado entre llamadas

### Gallery_SnapShotButton
- **Función**: Botón para abrir galería de snapshots
- **Icono**: `sanp_gallery.png`
- **Tooltip**: "Open snapshot gallery"
- **Comportamiento**: Ejecuta `open_snapshot_gallery()` del módulo LGA_viewer_SnapShot_Gallery
- **Funcionalidad**: Abre ventana de galería con thumbnails organizados por proyecto y slider de tamaño

## Clases de la Galería

### ThumbnailWidget
- **Función**: Widget personalizado para mostrar un thumbnail de imagen
- **Acciones**: Click abre el JPG en el visor por defecto, Shift+click lo abre en el ShareX Image Editor y Alt+click lo revela en el explorador
- **Características**:
  - Carga y escala imágenes manteniendo relación de aspecto
  - Redimensionamiento dinámico con el slider
  - Estilo visual con bordes y hover effects
  - Manejo de errores con placeholder para imágenes no válidas

### ProjectFolderWidget
- **Función**: Contenedor que agrupa thumbnails por proyecto
- **Características**:
  - Título del proyecto con estilo destacado
  - Layout horizontal para thumbnails
  - Actualización dinámica del tamaño de todos los thumbnails
  - Mensaje informativo cuando no hay imágenes

### SnapshotGalleryWindow
- **Función**: Ventana principal de la galería
- **Características**:
  - Toolbar superior con slider de tamaño (50px - 500px)
  - Área de scroll para navegación fluida
  - Carga automática de proyectos y organización alfabética
  - Soporte para múltiples formatos de imagen
  - Mensajes informativos para estados vacíos

## Logging

Los cuatro módulos escriben a **`LGA_ToolPack/logs/LGA_viewer_SnapShot_<pid>.log`**
a través de `LGA_viewer_SnapShot_logging.py`, siguiendo el esquema de
`docs/Docu_Logging_System.md`: sólo a archivo, sin ensuciar el Script Editor, y
seguro entre hilos con `QueueHandler` + `QueueListener`.

Existe por un caso concreto: el botón del viewer desapareció y **no quedó ni una
línea en ningún lado**. La tool usaba `debug_print` contra la consola con
`DEBUG = False`, así que no había nada que leer. Se resolvió inspeccionando el
estado en vivo, algo que se habría perdido con sólo reiniciar Nuke.

Se aparta del logger del Media Manager en dos cosas, a propósito:

- **Appendea, no trunca.** El caso que motivó todo esto se diagnosticó al día
  siguiente: si el log se vaciara en cada arranque, reiniciar Nuke —lo primero
  que uno hace cuando algo se rompe— borraría la evidencia.
- **Un archivo por proceso**, con el pid en el nombre. Con dos Nukes abiertos
  sobre el mismo archivo, al cruzar el tamaño de rotación los dos rotan a la vez
  y uno falla; ese traceback sale por stderr, o sea al Script Editor, que es
  justo lo que este sistema existe para evitar. Al arrancar se borran las
  sesiones viejas y quedan las `MAX_SESIONES` más recientes.
- **Rota por tamaño** (1 MB × 2 backups), que es la contracara de no truncar.

Qué queda registrado, elegido a partir de lo que no se pudo ver aquella vez:

- La inserción de los botones y **qué botones previos se removieron**, que es el
  punto ciego que hubo que diagnosticar a mano
- Cuando se encuentra el viewer pero no su frame slider, o cuando se agotan los
  reintentos: los dos van como `error`
- El motor usado, si compone, y contra qué
- Las bandas medidas y el rect del recorte
- Si el portapapeles salió por `CF_DIB` o cayó al camino de Qt, que es una
  degradación silenciosa que conviene ver
- Los `traceback` completos de los errores que hoy sólo muestran un `nuke.message`

Los flags están en el módulo de logging: `DEBUG` apaga todo, `DEBUG_LOG` escribe
al archivo y `DEBUG_CONSOLE` además al Script Editor. El archivo va prendido por
defecto: la escritura es asincrónica y es la única forma de saber qué pasó
cuando algo falla una sola vez.

El log es **asincrónico**: en un crash duro de Nuke se pueden perder las últimas
líneas encoladas, que es justo el escenario que más interesa. Para eso está el
`faulthandler` de la raíz del `.nuke`, que es sincrónico y cubre ese caso.

`logs/` está excluido en tres capas —el `.git/info/exclude` del pack, el
`.gitignore` del contenedor y el generador de release—, así que no se publica ni
viaja en el zip. Tener presente igual que el archivo acumula **nombres de
proyectos de clientes** (`nuke.root().name()`, rutas de la galería): si alguna
vez hay que mandarle el log a alguien para debuggear, va con esos nombres
adentro.

## Por qué los botones no son QDialog

Los tres contenedores de los botones del viewer son `QWidget`. Fueron `QDialog`
hasta la v1.06, y eso causaba que el botón desapareciera después de usarlo.

Un `QDialog` se sigue portando como diálogo aunque esté metido en el layout de
un toolbar: con el foco puesto, un **Escape** le dispara `reject()`, y eso
termina en `hide()`. El widget quedaba **vivo y en el layout, pero invisible**,
así que no había crash ni error en la consola: el botón simplemente ya no
estaba. Y desaparecía sólo el que se había clickeado, porque era el único que
tenía el foco.

Reproducido con Qt 6.5.3: mismo árbol de widgets con `QDialog` de contenedor, un
Escape y `isVisible()` pasa a `False`; con `QWidget` no pasa ni con Escape ni
con Enter.

Los `QPushButton` además llevan `setFocusPolicy(Qt.NoFocus)`. Un botón dentro
del viewer que se queda con el foco de teclado después del click se come los
atajos que el usuario le manda a Nuke.

## Motores de captura

La tool tiene dos motores. El que corre por defecto es el de `capture()`; el del
Write se mantiene porque es el único que da resolución completa del proyecto, y
se llega a él con **Ctrl+Click en el botón del viewer**. No se anuncia en
tooltips ni en el README.

No tiene atajo de teclado, y no por olvido: en Nuke un shortcut necesita un ítem
de menú, y esconder ese ítem con `MenuItem.setVisible(False)` le da de baja la
acción de Qt y con ella el shortcut. No se puede tener escondido y con atajo a
la vez.

| | `_snapshot_con_capture()` | `_snapshot_con_write()` |
|---|---|---|
| Resolución | la del viewport, según el zoom | la del formato del proyecto |
| Look | con viewerProcess, gain y gamma del viewer | el que dé el Write |
| Encuadre | lo que se está viendo | la imagen entera |
| Costo | una llamada, sin nodos ni callbacks | crea y borra un Write, dispara render |

### `_snapshot_con_capture(output_path, view_node, input_node)`
Llama a `view_node.capture(path)`, que escribe el framebuffer del viewer sin
renderizar nada. Es lo mismo que hace el botón Capture del viewer —ver
`nukescripts/captureViewer.py` adentro de Nuke—, pero sin tocar el knob `file`
del Viewer ni pasar por `executeMultiple`. Después le aplica el recorte.

### `_snapshot_con_write(output_path, input_node)`
El motor histórico: selecciona el nodo conectado al viewer, crea un Write
temporal, lo ejecuta con `nuke.execute()`, lo borra y restaura la selección
original. Silencia el wav de RenderComplete mientras dura el render.

## Recorte del viewport

`capture()` devuelve el viewport entero, así que cuando la imagen no lo llena
quedan bandas de fondo alrededor. `_rect_visible()` las mide y las recorta eje
por eje: si sobra vacío arriba y abajo se recorta en Y, y si a los costados la
imagen desborda no se toca X. No hace falta saber si el usuario quiso ver la
imagen entera o está zoomeando; se recorta el vacío que sobre.

La medición se valida sola, porque el zoom del viewer es un solo número para
los dos ejes: con banda en los dos, el zoom deducido de cada uno tiene que
coincidir; con banda en uno solo, ese zoom tiene que predecir que el otro eje
desborda el viewport. Cuando no cierra —un plate con letterbox quemado, un
fundido a negro—, no se recorta nada.

Hay dos cortes antes de eso. `_parece_uniforme()` mira una grilla rala y sale
sin recortar si todo el viewport es de un color, lo que además evita que el
escaneo fino recorra a mano el 45% de cada borde. Y si alguna banda llega al
tope de `CROP_LIMITE`, la medición se descarta: no se encontró el borde de la
imagen, se frenó el escaneo.

## Tira de comparación

`compare=True` genera **dos imágenes**: la captura individual (snapshot N, va a
la galería pero no al portapapeles) y la compo con el snapshot anterior pegado a
su izquierda (snapshot N+1, galería y portapapeles). Sirve para armar de a un
shortcut la tira que se le manda al vendor —plate, lo que hizo, lo que haría— en
vez de montarla a mano en Photoshop, conservando además cada captura suelta.

El encadenado no necesita ningún archivo de estado. La compo lleva el número más
alto, así que la próxima vez `get_latest_snapshot_path()` la devuelve a ella y la
tira crece de a una captura por vez. Una captura sin `compare` arranca una tira
nueva, porque pasa a ser el último snapshot.

El alto lo manda la más alta de las dos; la más baja se ancla **abajo**, con el
relleno negro arriba. No hay separador entre una imagen y otra.

La compo se guarda con calidad JPEG 100: la parte vieja se re-comprime en cada
paso, y a la tercera o cuarta captura la pérdida acumulada se notaría.

No hay archivo temporal: la captura nace como snapshot numerado. Si la compo
falla —la tira pasó el ancho máximo del JPEG—, la captura ya es un snapshot
válido, queda sola y arranca una tira nueva; no hay nada que rescatar.

## Portapapeles

El snapshot se publica como `CF_DIB` con `SetClipboardData` (ctypes sobre
user32/kernel32), no con `QClipboard.setImage()`.

El motivo: Qt publica el portapapeles por OLE con **renderizado diferido**.
Anuncia los formatos pero no materializa los bytes hasta que alguien se los
pide, y para contestar necesita que el proceso vuelva al event loop. Como justo
después de copiar venían el guardado en la galería y la limpieza de temporales
—las dos IO sincrónica—, Nuke no llegaba a contestar.

Medido con Qt 6.5.3: con **0,3 s** de hilo bloqueado después del `setImage`, el
snapshot ya no entra al historial de Windows; el portapapeles queda con los
formatos anunciados y los datos en `NULL`, y cualquier otra app que intente
pegar en ese momento recibe `ACCESS_DENIED`. Eso es lo que se veía como "se
borra el historial": no se borraba, se rompía la entrada.

Con `CF_DIB` los bytes quedan materializados en el acto —10 ms en HD, 35 ms en
4K— y no dependen de que el proceso conteste nada. Es lo mismo que hace ShareX,
que por eso nunca falla. Windows sintetiza `CF_BITMAP` y `CF_DIBV5` solo, así
que alcanza con publicar `CF_DIB`.

`_copiar_al_portapapeles()` cae al camino de Qt si algo falla, así que fuera de
Windows y ante cualquier error se comporta como antes. Y la copia quedó como
**lo último** de `take_snapshot()`, después de toda la IO: con `CF_DIB` ya no
haría falta, pero si se usa el respaldo de Qt, dejar IO después de copiar es
justamente lo que rompe la entrada.

Detalles que importan si se toca ese código:

- Hay que declarar `argtypes` y `restype` de las funciones de la API. Sin eso
  ctypes asume enteros de 32 bits y trunca los handles.
- El DIB clásico es bottom-up, así que la imagen va espejada en vertical.
- Si `SetClipboardData` tiene éxito, el dueño del `HGLOBAL` pasa a ser el
  sistema y liberarlo sería un doble free sobre memoria ajena. Por eso el
  handle se pone en `None` **en esa misma línea**, no al salir: si algo
  posterior —un `print`, el `CloseClipboard`— llegara a tirar, el `except`
  general lo liberaría. La invariante tiene que estar impuesta por el código,
  no depender de que nada falle.
- El `CloseClipboard` va en un `finally`: un portapapeles abierto cuelga a las
  demás aplicaciones.
- Corre en el hilo de GUI. `EmptyClipboard` manda un `WM_DESTROYCLIPBOARD` a la
  ventana que tenía el portapapeles por OLE, y desde un worker ese `SendMessage`
  puede quedarse esperando al hilo principal.

## Editor de imágenes

`Shift+click` sobre un thumbnail abre el JPG en el **ShareX Image Editor LGA**, el
mismo que usa el panel de HieroTools para anotar capturas — y con el mismo
modificador que alla.

El ejecutable no es del pack: lo trae HieroTools, que es un repo aparte y puede
no estar instalado. `get_hierotools_image_editor()` lo busca subiendo dos niveles
desde `py/` para llegar al `.nuke`, y prueba también la carpeta del usuario por si
el pack se instaló en otro lado. Devuelve `None` si no está, o si el sistema no es
Windows —el editor es un `.exe`, así que sólo se busca la grafía `Python/Startup`—.

El resultado se cachea por sesión, porque la galería crea un thumbnail por
archivo y si no serían dos accesos a disco por cada uno. `open_snapshot_gallery()`
invalida esa caché al abrir, así que si las HieroTools se instalan con Nuke
abierto alcanza con cerrar y reabrir la galería.

De ese resultado dependen las dos puntas: la fila `Shift-click` del tooltip sólo
se arma si hay editor; `Alt-click` (revelar) se lista siempre. Sin editor, el
Shift+click cae en el visor por defecto.

En `mousePressEvent` Shift se evalúa antes que Alt, así que **Alt+Shift+click
abre el editor cuando está instalado, y revela en el explorador cuando no** —los
dos `if` son independientes, la intención de Alt no se pierde—. Ojo con la
asimetría: en el menú, `Alt+Shift+F9` es el que compone la tira. La misma
combinación hace cosas distintas según dónde se apriete.

Al editor se le pasa **el archivo como argumento**, igual que hace `ReviewPic` en
HieroTools. La versión del panel de Hiero manda la imagen por el portapapeles
porque ahí no existe como archivo; acá sí, así que no hace falta pisarle el
portapapeles al usuario.

## Funciones Principales

### `take_snapshot(save_to_gallery=True, use_write=False, compare=False)`
- **Verificaciones iniciales**: Viewer activo y nodo conectado
- **Numeración única**: Genera snapshots con nombres `LGA_snapshot_N.jpg` donde N es ascendente
- **Proceso**: Despacha a uno de los dos motores (ver "Motores de captura") y después hace lo mismo en los dos casos: portapapeles, galería y limpieza
- **Motor**: `use_write=False` (por defecto) captura el viewport; `use_write=True` renderiza con un Write temporal
- **Tira**: `compare=True` genera captura y compo como dos snapshots (ver "Tira de comparación"). Si no hay anterior, la captura queda sola y arranca la tira
- **Galería por defecto**: Si `save_to_gallery=True` (comportamiento por defecto), guarda copia en `snapshot_gallery/proyecto/`
- **Organización por proyecto**: Crea subcarpetas basadas en nombre del proyecto sin versión
- **Numeración secuencial**: Archivos en galería usan formato `proyecto_vXX_N.jpg`
- **Limpieza automática**: Elimina snapshots anteriores después del guardado exitoso
- **Salida**: Copia imagen al portapapeles y mantiene archivo temporal
- **Integración**: Maneja sistema RenderComplete si está disponible
- **Requisito**: Necesita nodo conectado al viewer con canales válidos

### `_componer_con_anterior(anterior_path, nueva_path, salida_path)`
- **Función**: Pega la imagen nueva a la derecha de la anterior sobre un lienzo negro
- **Medidas**: ancho = suma de los dos anchos; alto = el mayor de los dos
- **Anclaje**: las dos imágenes se dibujan en `y = alto_total - alto_propio`, o sea pegadas abajo
- **Retorna**: `True` si pudo leer las dos imágenes y guardar el resultado
- **Fallo**: Si el guardado falla —una tira que pasa los 65535 px de ancho del JPEG, disco lleno— borra el archivo que Qt dejó en cero bytes. Si quedara, sería el snapshot más alto y rompería el Hold y la cadena siguiente

### `show_snapshot_hold(start)`
- **Función**: Muestra snapshot con control manual del usuario
- **start=True**: Busca el snapshot más reciente y lo muestra en viewer
- **start=False**: Elimina nodo Read temporal y restaura estado original
- **Estado**: Usa variable global para mantener información entre llamadas
- **Posicionamiento inteligente**: 
  - Con nodo conectado: Posiciona Read debajo del nodo existente
  - Sin nodo conectado: Posiciona Read arriba del viewer
- **Sin cache**: No necesita reload ya que cada snapshot tiene nombre único
- **Restauración**: Reconecta nodo original o desconecta viewer según estado inicial
- **Rendimiento**: Incluye `processEvents()` para evitar bloqueos de UI

### `get_viewer_info()`
- **Función**: Obtiene información del viewer activo con nodo conectado requerido
- **Retorna**: Tupla con (viewer, view_node, input_index, input_node)
- **Uso**: Para funciones que requieren nodo conectado como `take_snapshot()`
- **Manejo de errores**: Verificaciones robustas con debug prints

### `get_viewer_info_for_show()`
- **Función**: Obtiene información del viewer activo permitiendo trabajar sin nodo conectado
- **Retorna**: Tupla con (viewer, view_node, input_index, input_node) donde input_node puede ser None
- **Uso**: Para `show_snapshot_hold()` que puede funcionar sin nodo conectado
- **Flexibilidad**: Permite mostrar snapshots en viewers vacíos

### Funciones Auxiliares de Numeración

### `get_next_snapshot_number()`
- **Función**: Obtiene el siguiente número para snapshot verificando archivos existentes
- **Retorna**: Número entero siguiente al más alto encontrado
- **Patrón**: Busca archivos `LGA_snapshot_*.jpg` en carpeta temporal

### `cleanup_old_snapshots(current_number)`
- **Función**: Elimina snapshots con número menor al actual
- **Proceso**: Mantiene solo el snapshot más reciente para ahorrar espacio
- **Seguridad**: Manejo de errores en eliminación de archivos

### `get_latest_snapshot_path()`
- **Función**: Obtiene la ruta del snapshot con número más alto
- **Retorna**: Ruta completa del archivo o None si no encuentra ninguno
- **Uso**: Para `show_snapshot_hold()` al buscar el snapshot más reciente

### Funciones de Galería

### `get_project_info()`
- **Función**: Analiza el nombre del proyecto actual de Nuke
- **Retorna**: Tupla (nombre_sin_version, nombre_completo)
- **Lógica**: Detecta versiones en formato `_vXX` al final del nombre
- **Uso**: Para organizar snapshots por proyecto en la galería

### `get_next_gallery_number(project_dir, project_name)`
- **Función**: Obtiene el siguiente número secuencial para archivos de galería
- **Retorna**: Número entero siguiente al más alto encontrado para el proyecto
- **Patrón**: Busca archivos `proyecto_vXX_*.jpg` en la carpeta del proyecto

### `save_snapshot_to_gallery(snapshot_path)`
- **Función**: Guarda snapshot en galería organizada por proyecto
- **Proceso**: Crea subcarpeta del proyecto, numera archivo secuencialmente
- **Estructura**: `snapshot_gallery/proyecto_sin_version/proyecto_vXX_N.jpg`
- **Retorna**: Ruta del archivo guardado o None si hay error

## Implementación del Control Hold

El segundo botón usa eventos nativos de PySide2 para máxima responsividad:
- **pressed()**: Inicia la visualización del snapshot
- **released()**: Termina la visualización y restaura estado
- **Estado persistente**: Variable global mantiene información entre eventos
- **Módulo único**: Importación una sola vez evita reseteo de variables
- **Posicionamiento adaptativo**: Se adapta a viewers con o sin nodos conectados
- **Sistema único**: Cada snapshot tiene nombre único, evita problemas de cache

## Características Técnicas

### Manejo de Errores
- **Verificación de canales**: Previene errores de "has no valid channels"
- **Limpieza robusta**: Eliminación correcta de nodos temporales
- **Mensajes descriptivos**: Errores claros para debugging
- **Manejo de referencias**: Previene errores de "PythonObject not attached"
- **Verificación de estado**: Manejo seguro de viewers con/sin nodos conectados

### Optimización de Rendimiento
- **processEvents()**: Evita bloqueos de UI en puntos críticos
- **Importación única**: Módulo se carga una vez por botón
- **Estado global**: Mantiene información entre llamadas press/release
- **Limpieza automática**: Eliminación de nodos temporales y snapshots antiguos garantizada
- **Numeración inteligente**: Sistema ascendente evita conflictos y problemas de cache

### Integración con Sistemas
- **RenderComplete**: Manejo automático de sonido durante snapshot
- **Portapapeles**: Copia automática de imagen generada
- **Archivos temporales**: Gestión de snapshots en carpeta del sistema
- **Galería de proyecto**: Sistema organizado por proyecto con numeración secuencial
- **Iconos**: Sistema de iconos personalizados para botones (`snap_camera.png`, `sanp_picture.png`, `sanp_gallery.png`)
- **Nuke API**: Uso correcto de `node["reload"].execute()` para recargar Read nodes
- **Galería visual**: Thumbnails redimensionables con soporte para múltiples formatos
- **UI responsiva**: Slider de tamaño en tiempo real y área de scroll optimizada

## Notas de Implementación
- Los tres botones se insertan buscando el widget con tooltip "frameslider range"
- Se limpian botones existentes antes de agregar los nuevos
- Detección de tecla Shift para evitar guardar en galería (comportamiento invertido: sin Shift guarda, con Shift no guarda)
- Organización automática por proyecto basada en nombre del archivo de Nuke
- Debug prints disponibles para seguimiento de ejecución
- Restauración automática del estado del viewer en todos los casos
- Compatibilidad con versiones antiguas y nuevas de Nuke/PySide
- Soporte completo para viewers vacíos en función de mostrar snapshot
- Galería con thumbnails organizados alfabéticamente por proyecto
- Slider de tamaño dinámico (50px - 500px) para thumbnails
- Soporte para formatos jpg, png, tiff, exr en la galería

 