"""
____________________________________________________________________

  LGA_UI_Style_ToolPack v1.03 | Lega

  Punto UNICO de ajuste del look de las ventanas del ToolPack. Todo lo
  visual sale de aca: colores, fondos, bordes, esquinas, espaciados y
  anchos. Una tool ya migrada no define ningun hex suelto ni QSS propio.

  La migracion es de a una tool por vez, para poder volver atras una sola
  si no convence. Mientras dure, conviven ventanas migradas y sin migrar.

  Antes cada tool copiaba su propio bloque de estilos y los valores se
  fueron separando: el mismo gris de texto aparecia como #a7a7a7,
  #aeaeae, #aaaaaa y #cccccc, y el mismo fondo como #272727, #282828,
  #212121 y #1f1f1f. Vistas una detras de otra las ventanas no se leian
  como la misma app.

  La paleta de paths es la misma que usan las apps Qt/C++ de LGA
  (DialogStyle.h en lga_base_qt_c_py), asi que un path se lee igual en
  Nuke que en PipeSync o FileManagerS3.

  Uso:

      from LGA_UI_Style_ToolPack import Style, colorize_path, emphasis

      dialog.setStyleSheet(Style.WINDOW)
      button.setStyleSheet(Style.BTN_PRIMARY)
      label.setText("Saving to:<br>%s" % colorize_path(destination))

  v1.03: Variantes de texto de los colores semanticos (OK_TEXT,
         WARNING_TEXT, ERROR_TEXT) y el celeste informativo, y PROGRESS
         para las barras de progreso.
  v1.02: Style.FORM, la hoja completa de una ventana de ajustes, y
         SCROLLBAR como bloque suelto que comparten TABLE y FORM.
  v1.01: BTN_ICON para los botones cuadrados con un glifo, los colores
         de las dos etapas de un search & replace, y selection-color en
         los campos de texto.
  v1.00: Version inicial, con los valores que ya compartian de hecho
         LGA_RnW_PathsToRelative y LGA_mediaPathReplacer.
____________________________________________________________________
"""

# ---------------------------------------------------------------------------
#                                  Paleta
# ---------------------------------------------------------------------------
# Los nombres describen el ROL, no el color: cambiar el violeta de la marca
# no obliga a renombrar nada.


class Color(object):
    """Colores de la app. Un solo lugar donde tocarlos."""

    # --- superficies -------------------------------------------------------
    # Tres niveles de profundidad y nada mas. Antes habia siete fondos casi
    # iguales y la jerarquia no se leia.
    WINDOW = "#212121"  # fondo de la ventana
    SURFACE = "#272727"  # tablas, campos, cajas apoyadas sobre la ventana
    SURFACE_RAISED = "#2E2E2E"  # botones chicos, combos, elementos elevados
    SURFACE_HEADER = "#2B2B2B"  # cabecera de tabla
    SURFACE_SUNKEN = "#1A1A1A"  # bloques de detalle tecnico, hundidos

    # --- texto -------------------------------------------------------------
    # El cuerpo va gris y el blanco queda reservado para lo que importa. Con
    # todo el texto en blanco no hay jerarquia posible.
    TEXT = "#A7A7A7"  # cuerpo
    TEXT_STRONG = "#E8E8E8"  # titulos y lo destacado con emphasis()
    TEXT_DIM = "#6E6E6E"  # secundario, deshabilitado, metadatos
    TEXT_HEADER = "#999999"  # cabecera de tabla: entre el cuerpo y el dim
    TEXT_ON_ACCENT = "#FFFFFF"  # unico blanco puro: sobre el violeta lleno

    # --- bordes ------------------------------------------------------------
    BORDER = "#333333"  # borde de tablas y cajas
    BORDER_STRONG = "#444444"  # borde de controles interactivos
    BORDER_HOVER = "#555555"

    # Fondo del hover de los controles que no son el boton de accion, y de la
    # fila seleccionada de una tabla. Son dos escalones por encima de SURFACE:
    # se tienen que notar sin cambiar el peso del control.
    SURFACE_HOVER = "#383838"
    SURFACE_SELECTED = "#353535"

    # --- accion (el violeta de la app) -------------------------------------
    ACCENT = "#443A91"
    ACCENT_HOVER = "#774DCB"
    ACCENT_DISABLED = "#2A2540"
    ACCENT_TRACK = "#393959"  # riel de una barra de progreso

    # --- estados semanticos ------------------------------------------------
    # Verde: la operacion se puede hacer. Amarillo: se puede pero mirala.
    # Rojo: no se puede. Los tres desaturados para que no griten sobre gris.
    OK = "#6A9960"
    WARNING = "#B09040"
    ERROR = "#A06060"

    # Los mismos tres estados, pero para TEXTO adentro de un mensaje. Van mas
    # claros a proposito: los de arriba estan calibrados para una barra o un
    # fondo, donde un color saturado grita; una palabra suelta de 12 px sobre
    # el fondo de la ventana con esos valores casi no se lee.
    # OK_TEXT cierra la terna aunque hoy no lo use nadie: si faltara, el
    # primero que necesite un "listo" en verde volveria a inventar un hex.
    OK_TEXT = "#8FCB7E"
    WARNING_TEXT = "#FFD369"
    ERROR_TEXT = "#FF6B6B"

    # Informativo: ni bien ni mal, "esto es lo que va a pasar". Es el celeste
    # de la paleta de paths, asi que un destino resaltado en un mensaje se lee
    # con el mismo idioma que el path que lo acompana.
    INFO = "#6BC9FF"

    # Las dos etapas de un search & replace encadenado. No son estados: son
    # dos operaciones distintas que hay que poder separar de un vistazo sobre
    # el mismo path, asi que van en dos tonos que no se confunden entre si ni
    # con el verde de OK.
    MATCH_A = OK
    MATCH_B = "#C4787A"

    # --- paths -------------------------------------------------------------
    # La parte COMUN de un par origen/destino va en lavanda: es el mismo color
    # en los dos lados porque es lo mismo. Donde se corta el lavanda es donde
    # los paths se separan, y esa es la senal que el usuario busca.
    PATH_COMMON = "#C56CF0"
    PATH_SEPARATOR = "#6A6A6E"


# De la divergencia en adelante se recorre esta paleta en orden, IGUAL en los
# dos lados de un par: el color marca el NIVEL de directorio, no de que lado
# esta. Es la misma tupla que kPathPalette en DialogStyle.h de
# lga_base_qt_c_py, copiada al pie para que un path se lea igual en Nuke que
# en las apps Qt/C++. Son doce entradas con seis colores: repite recien a
# partir del sexto nivel, que en la practica ya cae fuera de lo que se compara
# de un vistazo.
PATH_PALETTE = (
    "#FFFF66",  # amarillo
    "#28B5B5",  # verde cian
    "#FF9A8A",  # naranja pastel
    "#0088FF",  # azul
    "#FFD369",  # amarillo mostaza
    "#28B5B5",  # verde cian
    "#FF9A8A",  # naranja pastel
    "#6BC9FF",  # celeste
    "#FFD369",  # amarillo mostaza
    "#28B5B5",  # verde cian
    "#FF9A8A",  # naranja pastel
    "#6BC9FF",  # celeste
)


# ---------------------------------------------------------------------------
#                                 Geometria
# ---------------------------------------------------------------------------
class Metric(object):
    """Medidas de la app. Mismos numeros en todas las ventanas."""

    # Un unico ancho minimo para los carteles: antes cada uno elegia el suyo
    # (360 / 400 / 460) y el salto se notaba al verlos seguidos.
    DIALOG_MIN_WIDTH = 460
    DIALOG_MARGIN = 18

    WINDOW_MARGIN = 16
    SPACING = 10

    RADIUS = 5  # esquinas de botones y cajas
    RADIUS_SMALL = 3  # esquinas de controles chicos

    ROW_HEIGHT = 24  # alto de fila de tabla
    SCROLLBAR_WIDTH = 10

    # La cruz de cerrar. 26 px es el minimo comodo para acertarle con el
    # mouse sin apuntar: mas chica se falla y se termina moviendo la ventana.
    CLOSE_BUTTON_SIZE = 26


# ---------------------------------------------------------------------------
#                                  Estilos
# ---------------------------------------------------------------------------
# Barra de scroll. Va suelta y no adentro de un estilo concreto porque la
# comparten la tabla, los campos de texto multilinea y cualquier area
# scrolleable: cuando estaba copiada en cada tool cada una le puso un ancho
# distinto (8 o 12 px) y el salto se notaba al comparar dos ventanas.
SCROLLBAR = """
QScrollBar:vertical {
    background: %(window)s;
    width: %(sb)dpx;
    margin: 0px;
    border-radius: %(sb_radius)dpx;
}
QScrollBar::handle:vertical {
    background: %(border)s;
    min-height: 30px;
    border-radius: %(sb_radius)dpx;
}
QScrollBar::handle:vertical:hover { background: %(border_hover)s; }
QScrollBar:horizontal {
    background: %(window)s;
    height: %(sb)dpx;
    margin: 0px;
    border-radius: %(sb_radius)dpx;
}
QScrollBar::handle:horizontal {
    background: %(border)s;
    min-width: 30px;
    border-radius: %(sb_radius)dpx;
}
QScrollBar::handle:horizontal:hover { background: %(border_hover)s; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; background: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
""" % {
    "window": Color.WINDOW,
    "border": Color.BORDER_STRONG,
    "border_hover": Color.BORDER_HOVER,
    "sb": Metric.SCROLLBAR_WIDTH,
    "sb_radius": Metric.SCROLLBAR_WIDTH // 2,
}


class Style(object):
    """QSS listo para usar. Se arma con la paleta de arriba, nunca con hex."""

    # Fondo de la ventana. Va sin border-radius: una ventana con esquinas
    # redondeadas y sin frame deja los cuatro angulos del rectangulo pintados
    # por debajo, que se ve peor que la esquina cuadrada.
    WINDOW = "background-color: %s; color: %s;" % (Color.WINDOW, Color.TEXT)

    # Caja apoyada sobre la ventana (avisos, agrupaciones).
    PANEL = "background-color: %s; border-radius: %dpx;" % (
        Color.SURFACE,
        Metric.RADIUS,
    )

    # --- botones -----------------------------------------------------------
    # El boton de accion. Es el unico violeta de la ventana: si hay dos, el
    # usuario no sabe cual ejecuta Enter.
    BTN_PRIMARY = """
QPushButton {
    background-color: %(accent)s;
    border: none;
    color: %(text_strong)s;
    padding: 7px 18px;
    border-radius: %(radius)dpx;
    font-weight: bold;
}
QPushButton:hover { background-color: %(accent_hover)s; color: %(on_accent)s; }
QPushButton:disabled { background-color: %(accent_dis)s; color: %(text_dim)s; }
""" % {
        "accent": Color.ACCENT,
        "accent_hover": Color.ACCENT_HOVER,
        "accent_dis": Color.ACCENT_DISABLED,
        "on_accent": Color.TEXT_ON_ACCENT,
        "text_strong": Color.TEXT_STRONG,
        "text_dim": Color.TEXT_DIM,
        "radius": Metric.RADIUS,
    }

    # El boton que NO ejecuta la accion (Cancel, Close). Misma caja que el
    # primario para que la fila quede pareja; lo unico que cambia es el color.
    BTN_SECONDARY = """
QPushButton {
    background-color: %(raised)s;
    border: 1px solid %(border)s;
    color: %(text)s;
    padding: 7px 18px;
    border-radius: %(radius)dpx;
    font-weight: bold;
}
QPushButton:hover { background-color: %(hover)s; color: %(text_strong)s; }
QPushButton:disabled { background-color: %(surface)s; color: %(text_dim)s; }
""" % {
        "raised": Color.SURFACE_RAISED,
        "surface": Color.SURFACE,
        "hover": Color.SURFACE_HOVER,
        "border": Color.BORDER_STRONG,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "text_dim": Color.TEXT_DIM,
        "radius": Metric.RADIUS,
    }

    # Boton auxiliar de una fila de herramientas (All / None / Swap / Reset).
    BTN_SMALL = """
QPushButton {
    background-color: %(raised)s;
    border: 1px solid %(border)s;
    color: %(text)s;
    padding: 3px 12px;
    border-radius: %(radius)dpx;
    font-size: 11px;
}
QPushButton:hover { background-color: %(hover)s; color: %(text_strong)s; }
QPushButton:disabled { background-color: %(surface)s; color: %(text_dim)s; }
""" % {
        "raised": Color.SURFACE_RAISED,
        "surface": Color.SURFACE,
        "hover": Color.SURFACE_HOVER,
        "border": Color.BORDER_STRONG,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "text_dim": Color.TEXT_DIM,
        "radius": Metric.RADIUS_SMALL,
    }

    # Boton cuadrado con un glifo adentro (swap, papelera). Va aparte de
    # BTN_SMALL porque ese reserva 12 px de padding horizontal por lado: en un
    # boton de ancho fijo no queda lugar para el glifo y Qt lo elide a "...".
    BTN_ICON = """
QPushButton {
    background-color: %(raised)s;
    border: 1px solid %(border)s;
    color: %(text)s;
    padding: 3px 2px;
    border-radius: %(radius)dpx;
    font-size: 11px;
}
QPushButton:hover { background-color: %(hover)s; color: %(text_strong)s; }
QPushButton:disabled { background-color: %(surface)s; color: %(text_dim)s; }
""" % {
        "raised": Color.SURFACE_RAISED,
        "surface": Color.SURFACE,
        "hover": Color.SURFACE_HOVER,
        "border": Color.BORDER_STRONG,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "text_dim": Color.TEXT_DIM,
        "radius": Metric.RADIUS_SMALL,
    }

    # La cruz de cerrar de las ventanas sin frame. Sin caja hasta el hover,
    # asi no compite con el boton de accion.
    BTN_CLOSE = """
QPushButton {
    background-color: transparent;
    border: none;
    color: %(text_dim)s;
    font-size: 16px;
    font-weight: bold;
    border-radius: %(radius)dpx;
}
QPushButton:hover { background-color: %(error)s; color: %(on_accent)s; }
""" % {
        "text_dim": Color.TEXT_DIM,
        "error": Color.ERROR,
        "on_accent": Color.TEXT_ON_ACCENT,
        "radius": Metric.RADIUS_SMALL,
    }

    # --- campos ------------------------------------------------------------
    LINE_EDIT = """
QLineEdit {
    background-color: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: %(radius)dpx;
    padding: 4px 8px;
    selection-background-color: %(accent)s;
    selection-color: %(text_strong)s;
}
QLineEdit:hover { border-color: %(border_hover)s; }
QLineEdit:focus { border-color: %(accent_hover)s; }
QLineEdit:disabled { color: %(text_dim)s; border-color: %(border)s; }
""" % {
        "surface": Color.SURFACE,
        "border": Color.BORDER_STRONG,
        "border_hover": Color.BORDER_HOVER,
        "accent": Color.ACCENT,
        "accent_hover": Color.ACCENT_HOVER,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "text_dim": Color.TEXT_DIM,
        "radius": Metric.RADIUS_SMALL,
    }

    COMBO = """
QComboBox {
    background-color: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: %(radius)dpx;
    padding: 4px 8px;
}
QComboBox:hover { border-color: %(border_hover)s; }
QComboBox:disabled { color: %(text_dim)s; border-color: %(border_soft)s; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; width: 0; height: 0; }
QComboBox QAbstractItemView {
    background-color: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border_soft)s;
    selection-background-color: %(selected)s;
    selection-color: %(text_strong)s;
}
""" % {
        "surface": Color.SURFACE,
        "border": Color.BORDER_STRONG,
        "border_soft": Color.BORDER,
        "border_hover": Color.BORDER_HOVER,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "text_dim": Color.TEXT_DIM,
        "selected": Color.SURFACE_SELECTED,
        "radius": Metric.RADIUS_SMALL,
    }

    CHECKBOX = "color: %s; padding: 2px; background: transparent;" % Color.TEXT

    # Barra de progreso. El riel va en un violeta apagado y el relleno en el
    # violeta de la app: es la misma senal que el boton de accion, asi que se
    # lee como "esto es lo que pediste, avanzando".
    PROGRESS = """
QProgressBar {
    background-color: %(track)s;
    border: none;
    border-radius: %(radius)dpx;
    text-align: center;
    color: %(text)s;
    font-size: 11px;
    min-height: 18px;
    max-height: 18px;
}
QProgressBar::chunk { background-color: %(accent)s; border-radius: %(radius)dpx; }
""" % {
        "track": Color.ACCENT_TRACK,
        "accent": Color.ACCENT,
        # El porcentaje se lee SOBRE el relleno violeta: con el gris del
        # cuerpo el contraste queda abajo de AA y el numero no se lee.
        "text": Color.TEXT_STRONG,
        "radius": Metric.RADIUS,
    }

    # --- ventana de formulario ---------------------------------------------
    # Hoja completa para una ventana de ajustes: en vez de llamar a
    # setStyleSheet widget por widget —que es como estaban las de Settings y
    # Enable Tools, o sea sin llamarlo nunca y heredando el tema de Nuke— se
    # aplica esta al contenedor y toma todos sus hijos.
    #
    # NO define un QPushButton default a proposito: el de accion se marca a
    # mano con BTN_PRIMARY y el resto con BTN_SECONDARY. Si el violeta viniera
    # por default, una ventana con cinco Save tendria cinco botones gritando
    # lo mismo.
    #
    # La excepcion son los QMessageBox: como son hijos de la ventana, el
    # QWidget { background-color } de abajo tambien los alcanza, y quedaban
    # con el fondo del pack y los botones del tema del host. Se les da el
    # boton secundario para que el cartel cierre coherente.
    FORM = """
QWidget { background-color: %(window)s; color: %(text)s; }
QLabel { background: transparent; color: %(text)s; }
QLabel[lgaTitle="true"] {
    color: %(text_strong)s;
    font-weight: bold;
    font-size: 11pt;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: %(border)s;
    border: none;
    max-height: 1px;
}
QCheckBox { color: %(text)s; background: transparent; padding: 2px; }
QMessageBox QPushButton {
    background-color: %(raised)s;
    border: 1px solid %(border_strong)s;
    color: %(text)s;
    padding: 5px 16px;
    border-radius: %(radius)dpx;
    min-width: 64px;
}
QMessageBox QPushButton:hover { background-color: %(hover)s; color: %(text_strong)s; }
QGroupBox {
    border: 1px solid %(border)s;
    border-radius: %(radius)dpx;
    margin-top: 10px;
    padding: 8px 4px 4px 4px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0px 4px;
    color: %(text_strong)s;
    font-weight: bold;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border_strong)s;
    border-radius: %(radius)dpx;
    padding: 4px 8px;
    selection-background-color: %(accent)s;
    selection-color: %(text_strong)s;
}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
    border-color: %(border_hover)s;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: %(accent_hover)s;
}
%(scrollbar)s
""" % {
        "scrollbar": SCROLLBAR,
        "window": Color.WINDOW,
        "surface": Color.SURFACE,
        "raised": Color.SURFACE_RAISED,
        "hover": Color.SURFACE_HOVER,
        "border": Color.BORDER,
        "border_strong": Color.BORDER_STRONG,
        "border_hover": Color.BORDER_HOVER,
        "accent": Color.ACCENT,
        "accent_hover": Color.ACCENT_HOVER,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "radius": Metric.RADIUS_SMALL,
    }

    # --- tabla -------------------------------------------------------------
    # La barra de scroll va incluida: cuando estaba suelta cada tool le ponia
    # un ancho distinto (8 / 12 px) y se notaba al comparar dos ventanas.
    TABLE = """
QTableWidget {
    background-color: %(surface)s;
    border: 1px solid %(border_soft)s;
    color: %(text)s;
    gridline-color: %(border_soft)s;
    outline: none;
}
QHeaderView::section {
    background-color: %(header_bg)s;
    color: %(header_fg)s;
    padding: 4px 8px;
    border: 0px;
    border-bottom: 1px solid %(border)s;
    font-weight: bold;
}
QTableWidget::item { padding-left: 6px; padding-right: 6px; }
QTableWidget::item:selected { background-color: %(selected)s; color: %(text_strong)s; }
%(scrollbar)s""" % {
        "surface": Color.SURFACE,
        "border_soft": Color.BORDER,
        "border": Color.BORDER_STRONG,
        "text": Color.TEXT,
        "text_strong": Color.TEXT_STRONG,
        "selected": Color.SURFACE_SELECTED,
        "header_bg": Color.SURFACE_HEADER,
        "header_fg": Color.TEXT_HEADER,
        "scrollbar": SCROLLBAR,
    }

    # Bloque de detalle tecnico (traceback, salida de un proceso). Va mas
    # oscuro que la ventana a proposito, para que se lea como un bloque de
    # datos pegado y no como una segunda parte del mensaje.
    DETAIL = """
QTextEdit {
    background-color: %(sunken)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: %(radius)dpx;
    padding: 8px;
}
""" % {
        "sunken": Color.SURFACE_SUNKEN,
        "border": Color.BORDER,
        "text": Color.TEXT,
        "radius": Metric.RADIUS_SMALL,
    }


# ---------------------------------------------------------------------------
#                                  Helpers
# ---------------------------------------------------------------------------
# Espacio de ancho cero. Qt corta linea en espacios y en "/", pero un path de
# Windows (T:\Proyectos\...\3_review) es para Qt UNA SOLA palabra impartible:
# si no entra en el ancho se sale y queda tapada.
_ZERO_WIDTH_SPACE = "&#8203;"


def emphasis(text):
    """
    Destaca en blanco un pedazo del mensaje. El cuerpo va gris, asi que esto
    es lo unico que se lee de un vistazo: usarlo SOLO en lo que decide la
    respuesta (cuantos archivos, donde, y la advertencia de que no se puede
    deshacer). Si se destaca todo, no se destaca nada.
    """
    return "<span style='color:%s'>%s</span>" % (Color.TEXT_STRONG, text)


def _escape(text):
    """Escapa el HTML de un segmento: un nombre de archivo puede traer & o <."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _split_path(path):
    """Parte un path en segmentos conservando el separador que los une."""
    return (path or "").replace("\\", "/").split("/")


def colorize_path(path):
    """
    Colorea un path recorriendo la paleta por nivel de directorio.

    Arranca por el lavanda —el mismo color con el que arranca la parte comun
    de un par— asi un path solo y un par se leen con el mismo lenguaje de
    color. Devuelve HTML: el label tiene que estar en modo rich text.
    """
    segments = _split_path(path)
    if not segments:
        return ""

    separator = "<span style='color:%s'>/</span>%s" % (
        Color.PATH_SEPARATOR,
        _ZERO_WIDTH_SPACE,
    )

    colors = (Color.PATH_COMMON,) + PATH_PALETTE
    painted = []
    for index, segment in enumerate(segments):
        if not segment:
            # El primer segmento vacio es la barra inicial de un path unix.
            painted.append("")
            continue
        color = colors[index % len(colors)]
        painted.append("<span style='color:%s'>%s</span>" % (color, _escape(segment)))

    return separator.join(painted)


def colorize_path_pair(from_path, to_path):
    """
    Colorea un origen y un destino mostrando donde se separan.

    La parte COMUN de los dos paths va en lavanda, igual en los dos lados
    porque es lo mismo. De ahi en adelante se recorre la paleta en el MISMO
    sentido en los dos lados: el color marca el nivel, no de que lado del par
    esta cada directorio, asi los dos paths se leen como una sola grilla en
    columnas en vez de como dos escalas distintas.

    Devuelve (from_html, to_html).
    """
    from_segments = _split_path(from_path)
    to_segments = _split_path(to_path)

    common = 0
    for left, right in zip(from_segments, to_segments):
        if left != right:
            break
        common += 1

    separator = "<span style='color:%s'>/</span>%s" % (
        Color.PATH_SEPARATOR,
        _ZERO_WIDTH_SPACE,
    )

    def paint(segments):
        painted = []
        for index, segment in enumerate(segments):
            if not segment:
                painted.append("")
                continue
            if index < common:
                color = Color.PATH_COMMON
            else:
                color = PATH_PALETTE[(index - common) % len(PATH_PALETTE)]
            painted.append(
                "<span style='color:%s'>%s</span>" % (color, _escape(segment))
            )
        return separator.join(painted)

    return paint(from_segments), paint(to_segments)
