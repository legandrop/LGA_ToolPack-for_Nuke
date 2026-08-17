# Estilo de las ventanas — cómo se hace una UI de las tools

Fuente de verdad de **cómo se ve** una ventana de las tools de LGA. El módulo es
`py/LGA_UI_Style_ToolPack.py` y existe una copia en cada uno de los otros tres
repos.

> **Las cuatro copias están divergidas hoy.** El módulo de este repo pasó a
> temas en `v1.11` y los otros tres siguen en el cuerpo anterior. Todo lo que
> este documento dice de los temas vale **sólo acá**; lo demás sigue valiendo
> en los cuatro. Sincronizarlos es una decisión pendiente, no un olvido: ver
> "Las cuatro copias".

## La regla

**Ningún script define un color, una medida ni un bloque de QSS propio.** Todo
sale del módulo:

```python
from LGA_UI_Style_ToolPack import SCROLLBAR, Color, Metric, Style, colorize_path

dialog.setStyleSheet(Style.WINDOW)
convert_button.setStyleSheet(Style.BTN_PRIMARY)
cancel_button.setStyleSheet(Style.BTN_SECONDARY)
label.setText("Saving to:<br>%s" % colorize_path(destination))
```

El motivo no es cosmético. Antes cada tool copiaba su propio bloque de estilos y
los valores se fueron separando: el mismo gris de texto aparecía como `#a7a7a7`,
`#aeaeae`, `#aaaaaa` y `#cccccc`, y el mismo fondo como `#272727`, `#282828`,
`#212121` y `#1f1f1f`. Vistas una detrás de otra, las ventanas no se leían como
la misma app. Y cada copia arrastraba sus propios bugs: la barra de estado de
`Paths to Relative` nunca se vio en ninguna versión, y el alto de `Write Presets`
y de `Color Space Favs` estaba calculado con la barra de título clavada en 20 px.

## Las cuatro copias

| Repo | Módulo |
|---|---|
| `LGA_ToolPack` | `py/LGA_UI_Style_ToolPack.py` |
| `LGA_ToolPack-B` | `py/LGA_UI_Style_ToolPackB.py` |
| `LGA_ToolPack-Layout` | `py/LGA_UI_Style_ToolPack_Layout.py` |
| HieroTools | `LGA_NKS_Shared/LGA_UI_Style_HieroTools.py` |

**Nacieron código idéntico a propósito.** Los cuatro repos son independientes y
un usuario puede tener instalado uno solo, así que no pueden importarse entre
sí. Lo único que difería era el docstring: nombre del módulo, su propio
historial de versiones y la ruta del ejemplo de import.

**Hoy no lo son.** El de este repo está en `v1.15` con los seis temas y los
otros tres quedaron en el cuerpo de antes, que es la mitad de largo. La regla
de "se cambia en las cuatro" sigue siendo la que se quiere, pero aplicarla
ahora significa portar los temas a los otros tres repos y revisar sus ventanas
una por una, que es un trabajo aparte y no una copia de archivo. Mientras
tanto: un valor que se toque en el cuerpo COMÚN se toca igual en las cuatro; lo
que es propio de los temas vive sólo acá.

**Cómo verificarlo**, comparando el cuerpo a partir de la línea del
`class Color`:

```bash
python - <<'EOF'
import io
def body(p):
    s = io.open(p, encoding="utf-8").read()
    return s[s.index("#                                  Paleta"):]
a = body("LGA_ToolPack/py/LGA_UI_Style_ToolPack.py")
for p in ("LGA_ToolPack-B/py/LGA_UI_Style_ToolPackB.py",
          "LGA_ToolPack-Layout/py/LGA_UI_Style_ToolPack_Layout.py",
          "Python/Startup/LGA_HieroTools/LGA_NKS_Shared/LGA_UI_Style_HieroTools.py"):
    print(p, body(p) == a)
EOF
```

Los nombres de módulo son distintos justamente porque los tres `py/` conviven en
el path de Nuke: con el mismo nombre, el primero de la lista le ganaría a los
otros dos y un pack terminaría usando el estilo de otro sin que nada avise.

## Temas (sólo en este repo, desde `v1.11`)

La paleta dejó de ser un juego de constantes y pasó a ser un **tema que cada
tool elige**. Hay seis: `pack`, `lga`, `graphite`, `slate`, `nuke` y
`high-contrast`, en ese orden.

```python
from LGA_UI_Style_ToolPack import Style, Color   # el tema BASE, "pack"
from LGA_UI_Style_ToolPack import theme

UI = theme("lga")                                # otro tema
ventana.setStyleSheet(UI.Style.WINDOW)
label.setStyleSheet("color: %s;" % UI.Color.TEXT)
```

- **El tema base es `pack`, o sea lo que había siempre.** Una tool que hace
  `from ... import Style, Color` recibe exactamente lo mismo de antes: las
  ventanas ya migradas no cambiaron ni de aspecto ni de código.
- **Se referencian por `id` y nunca por índice**, ni acá ni en el `.ini` de una
  tool: agregar uno en el medio de la lista no puede cambiar cuál es el default
  ni qué tema tiene guardado el usuario.
- **El orden de `THEMES` es sólo para la UI**: es el orden en que una ventana
  de ajustes dibuja la tira de botones. `pack` va primero porque es el base, y
  el de más a la izquierda tiene que ser el default. Que sea el primero no es
  lo que lo hace default —eso lo dice `BASE_THEME`, por id—.
- **Sin estado global.** Cada tema es su propio par de objetos, así que dos
  ventanas con temas distintos pueden estar abiertas a la vez. Las hojas ya no
  se arman en el cuerpo de la clase —una sola vez al importar— sino en
  `_build_styles()`, que recibe la paleta.
- **Los seis definen exactamente los mismos tokens.** `Theme()` lo valida y
  explota si a uno le falta o le sobra una clave, en vez de dejar un color
  viejo pegado de la paleta anterior.

**Algunos tokens no se escriben a mano en cada tema: se derivan.** Los escribe
`_derivados()` mezclando otros dos, para que un tema nuevo no obligue a
calcular hexes a ojo. Son el fondo de una celda de estado en la fila
seleccionada (`OK_BG_SELECTED` y sus dos hermanos, mezclados contra el gris de
selección) y los cinco de `Outside`, que se mezclan contra el fondo de **ese**
tema.

**Fuentes del pack.** `load_fonts()` registra Inter y JetBrains Mono desde
`py/fonts/`, y `font_family()` / `mono_family()` devuelven el nombre real de la
familia. Si no cargan se usa la del host. La mono es sólo para un campo de ruta
editable: ahí las rutas son relativas y con una proporcional los `../` no se
distinguen, el punto y la barra se pegan.

## Qué usar en cada caso

| Situación | Qué usar |
|---|---|
| Fondo de una ventana | `Style.WINDOW` |
| Ventana de ajustes, con campos y grupos | `Style.FORM` (toma todos los hijos) |
| Caja apoyada sobre la ventana | `Style.PANEL` |
| El botón que ejecuta la acción | `Style.BTN_PRIMARY` |
| Cancel, Close, cualquier otro | `Style.BTN_SECONDARY` |
| Botón auxiliar de una fila de herramientas | `Style.BTN_SMALL` |
| Botón cuadrado con un glifo (swap, `+`, `-`) | `Style.BTN_ICON` |
| La cruz de cerrar de una ventana sin frame | `Style.BTN_CLOSE` |
| Tabla | `Style.TABLE` |
| Área scrolleable que no es tabla ni form | `SCROLLBAR` (concatenado a lo tuyo) |
| Barra de progreso | `Style.PROGRESS` |
| Pastilla de estado con texto encima | `Color.OK_BG` / `WARNING_BG` / `ERROR_BG` |
| Lo mismo, en la fila seleccionada | `Color.OK_BG_SELECTED` / `WARNING_BG_SELECTED` / `ERROR_BG_SELECTED` |
| Un archivo que está afuera del shot | `Color.OUTSIDE_BG` (y `_SELECTED`) |
| Afuera de toda scan location, que es un dato y no un error | `Color.OUTSIDE_BG_INFO` (y `_SELECTED`) |
| El punto de color de un estado | `Color.DOT_OK` / `DOT_WARNING` / `DOT_ERROR` / `DOT_OUTSIDE` / `DOT_OUTSIDE_INFO` |
| Un path en un mensaje | `colorize_path()` |
| Un origen y un destino | `colorize_path_pair()` |
| Destacar en blanco una palabra | `emphasis()` |

## Las reglas que no son negociables

- **El botón de acción va SIEMPRE último, a la derecha, y es el único violeta.**
  Si hay dos violetas, el usuario no sabe cuál ejecuta Enter. Si el diálogo
  *traga* Enter a propósito —porque hay más de una opción válida y ninguna es la
  recomendada— entonces **no se marca ninguno**: un botón marcado que Enter no
  activa es un cartel que miente.
- **El cuerpo del mensaje va gris (`Color.TEXT`), el blanco se reserva.**
  `Color.TEXT_STRONG` es solo para lo que decide la respuesta: cuántos, dónde, y
  la advertencia. Si se destaca todo, no se destaca nada.
- **Todo path va coloreado y en su propia línea**, debajo del texto. Embebido en
  el medio de una oración se corta por donde cae el wrap y se vuelve ilegible.
- **La jerarquía de fondos no se invierte.** `WINDOW` es el fondo, `SURFACE` va
  encima, `SURFACE_RAISED` encima de eso. Una tabla más oscura que su propia
  ventana se lee hundida — pasaba en `Media Path Replacer`, `Write Presets` y
  `Color Space Favs`, en los tres al revés.
- **`Metric.CLOSE_BUTTON_SIZE` es 26 px y no baja.** Una cruz de 20 px sin caja
  obliga a apuntarle, y errarle arrastra la ventana en vez de cerrarla.
- **Textos de UI en inglés.** Comentarios, logs y changelog en castellano.

## Trampas conocidas

Cada una de estas apareció en una tool real y costó una corrección.

**Un `QWidget` pelado no pinta el `background` del QSS.** Hace falta
`setAttribute(Qt.WA_StyledBackground, True)`. `QLabel` y `QFrame` sí lo pintan.

**El `padding` de `QTableWidget::item` también se le aplica al widget de la
celda.** Una columna de 5 px con `padding: 6px` a cada lado deja el widget en
**0 px de ancho**. Para una barra de color de estado, pintar el fondo del
`QTableWidgetItem` en vez de meter un cell widget.

**El campo de adentro de un `QSpinBox` es un `QLineEdit`** y le cae la regla de
`QLineEdit` del form: suma un segundo borde y un segundo padding adentro de su
propia caja. Por eso `Style.FORM` lo neutraliza explícitamente. Y el spinbox se
deja **nativo**: en cuanto el QSS le define caja o flechas, Qt deja de dibujar
los triángulos y la sub-control termina tapando el número.

**Un alto de ventana calculado con números fijos se rompe al primer cambio.**
Sumar lo que *mide* cada parte: márgenes del layout, `spacing() * (count() - 1)`
—con un solo item no hay ningún hueco—, alto real de la barra de título, del
botón, del header de la tabla y de cada fila. Con layouts anidados hay que
recorrerlos todos.

**Para fijar el alto de apertura de algo que puede crecer**, poner el
`setMaximumHeight`, llamar `adjustSize()` y **soltarlo enseguida**
(`QWIDGETSIZE_MAX`). Dejado puesto, agrandar la ventana deja la caja clavada
flotando en el medio de un hueco.

**El `&` de un título de `QGroupBox` se lo come Qt** como marca de mnemónico.
`ALIGN & DISTRIBUTE` sale `ALIGN  DISTRIBUTE`. Se duplica: `title.replace("&", "&&")`.

**Una tabla cuyo fondo lo pinta un delegado propio no lleva `Style.TABLE`.**
La regla `QTableWidget::item:selected` de la hoja le gana al `setBackground()`
del item y a la paleta que setea el delegado, así que al seleccionar una fila se
pierde su color — y si ese color es la información, se pierde la información.
`CopyCat Cleaner` lo resuelve anulando la regla; `Update Folder Favs` directamente
no aplica la hoja.

**`Style.FORM` incluye `QWidget { background-color }`, que alcanza a los
`QMessageBox` hijos.** Por eso trae también una regla para sus botones: sin ella
el cartel queda con el fondo del pack y los botones del tema del host.

**Los tooltips los aplica `LGA_tooltip_helper`**, que sólo agrega su CSS si el
stylesheet no tiene ya un `QToolTip`. Por eso `Style.FORM` **no** define uno. El
helper vive sólo en el ToolPack: los otros packs usan `Style.TOOLTIP` como
fallback cuando no está.

## Cómo verificar un cambio sin abrir Nuke

Las ventanas son PySide puro. Se pueden instanciar y `grab()` a PNG stubbeando
`nuke` y el adapter, con el **mismo PySide6 que trae Nuke** (6.5.3 en Nuke 17):

```python
import sys, types
nuke = types.ModuleType("nuke")
class _Any(types.ModuleType):
    def __getattr__(self, name):
        return lambda *a, **k: None
nuke.__class__ = _Any
sys.modules["nuke"] = nuke

from PySide6 import QtWidgets, QtGui, QtCore
adapter = types.ModuleType("LGA_QtAdapter_ToolPack")
adapter.QtWidgets, adapter.QtGui, adapter.QtCore = QtWidgets, QtGui, QtCore
sys.modules["LGA_QtAdapter_ToolPack"] = adapter

app = QtWidgets.QApplication([])
import LGA_RnW_PathsToRelative as T
w = T.PathsToRelativeWindow(rows, skipped, False, anchor, state, raw)
w.show(); app.processEvents(); w.grab().save("out.png")
```

Es mucho más rápido que reiniciar Nuke y permite medir píxeles en vez de mirar a
ojo. Para chequear que un QSS parsea, instalar un `qInstallMessageHandler` y
confirmar que no llegue ningún `Could not parse stylesheet`.

## La trampa que más veces mordió: `WA_StyledBackground`

**Qt resuelve la hoja de estilo y no pinta nada** si el widget no tiene
`Qt.WA_StyledBackground`. La regla es correcta, gana en especificidad, y no se
dibuja un solo píxel. Es un modo de fallar particularmente difícil de ver
leyendo el código, porque no hay nada mal escrito.

Pasa con `QWidget` y `QFrame` a los que se les pone `background-color` o
`border` por hoja propia. En el port del Media Manager mordió **tres veces**:
la caja de la tabla de ajustes con su cabecera y sus separadores, el fondo de
la ventana de ajustes, y el separador vertical de la barra de herramientas.

```python
caja.setFrameShape(QFrame.NoFrame)   # que el borde lo dibuje la hoja, no el estilo nativo
caja.setAttribute(Qt.WA_StyledBackground, True)
caja.setObjectName("lgaCaja")        # y la regla por #id, no por clase:
caja.setStyleSheet("#lgaCaja { background-color: %s; }" % Color.SURFACE)
```

**El `objectName` no es opcional.** Una regla `QFrame { ... }` sin selector se
le aplica también a todos los `QFrame` hijos.

No hace falta en un `QLabel`, un `QPushButton` ni un `QLineEdit`: esos ya
pintan su fondo por hoja. Es el contenedor pelado el que no.

## Dónde tocar

`py/LGA_UI_Style_ToolPack.py` y sus tres copias. Nada más. Cambiar un valor ahí
lo cambia en todas las ventanas migradas a la vez — que es el punto.

Con temas hay un lugar más donde no hay que tocar: **un token que cambia con el
tema va en los seis dicts de `THEMES`, no en la clase `Color`.** Lo que se
escribe en `Color` es el valor del tema base y, para los derivados, lo que
`_derivados()` va a sobreescribir; dejarlo ahí y no en los temas hace que un
tema lo herede sin poder cambiarlo.
