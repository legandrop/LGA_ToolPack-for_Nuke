"""
____________________________________________________________________

  LGA_UI_Style_ToolPack v1.11 | Lega

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

  v1.11: La paleta pasa a ser un TEMA que cada tool elige, no
         constantes fijas del modulo. Seis temas en THEMES y un
         theme(id) que devuelve su paleta y sus hojas.

         El tema BASE es "pack", o sea lo que habia hasta ahora: una
         tool que hace `from ... import Style, Color` recibe exactamente
         lo mismo de siempre y no hay que tocarle una linea. La que
         quiera otro aspecto lo pide -theme("lga")- y eso no le cambia
         el color a ninguna otra.

         Cada tema tiene sus propios objetos y no se muta nada global:
         asi dos ventanas con temas distintos pueden estar abiertas a la
         vez. Las hojas se armaban en el cuerpo de la clase Style, o sea
         una sola vez al importar; ahora las escribe _build_styles(),
         que recibe la paleta.
         Suma las fuentes del pack (load_fonts), los tokens que faltaban
         -ROW_LINE, FIELD_BG, PATH_FIELD, MARK_BG, los DOT_* y los tres
         *_BG_SELECTED derivados- y el tamano de letra de las tablas.
         Arregla la clave "border" repetida en el dict de CHECKBOX, que
         dejaba muerto a CHECKBOX_BORDER, y le da al checkbox
         deshabilitado-y-tildado su propio fondo: con el tilde apagado
         solo, la fila pasaba por destildada.
  v1.10: El checkbox deshabilitado se distingue del habilitado, y
         Style.WINDOW tambien lo lleva: era la hoja de casi todas
         las ventanas que quedaban con el checkbox del host.
  v1.09: El checkbox se dibuja con el indicador de las apps Qt de LGA
         en vez del nativo, que cambia con el tema del host.
  v1.08: Metric.BUTTON_HEIGHT, para que el boton marcado y el
         secundario midan lo mismo en una fila de acciones.
  v1.07: OK_BG, WARNING_BG y ERROR_BG, para el fondo de una pastilla
         de estado con texto encima.
  v1.06: Style.FORM pinta tambien los QSpinBox. Las flechitas NO se
         tocan: estilarlas sin redefinir ::up-arrow deja el boton
         gris y sin el triangulo, o sea sin senal de que se clickea.
  v1.05: Color.ENTITY, para destacar el nombre de una task o de un
         nodo sin colgarse del color de la paleta de paths.
  v1.04: Style.TOOLTIP, para que un pack sin el helper de tooltips
         del ToolPack igual los pinte como los demas.
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

import os


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

    # --- checkbox ----------------------------------------------------------
    # Los mismos valores que usan las apps Qt/C++ de LGA (el dark_theme.qss de
    # lga_base_qt_c_py), asi que un checkbox se ve igual en Nuke que en
    # PipeSync o FileManagerS3. El apagado es un violeta casi neutro y el
    # prendido el violeta de la marca, los dos mas oscuros que un boton porque
    # el indicador es chico y a plena intensidad grita.
    CHECKBOX_OFF = "#2A2832"
    CHECKBOX_OFF_HOVER = "#3A3744"
    CHECKBOX_ON = "#393455"
    CHECKBOX_ON_HOVER = "#4C4770"
    CHECKBOX_BORDER = "#272727"

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

    # Los mismos tres estados otra vez, pero para el FONDO de una pastilla con
    # texto encima. Van oscurecidos: un verde de fondo a la intensidad de OK se
    # come cualquier texto que le pongas arriba.
    OK_BG = "#244C19"
    WARNING_BG = "#6B4A0F"
    ERROR_BG = "#5A1A1A"

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

    # El campo de ruta EDITABLE de un formulario. Va mas apagado que
    # PATH_COMMON a proposito: ahi el violeta es un path coloreado por nivel,
    # aca es texto que se escribe, y a plena intensidad le gana al campo de
    # al lado. No cambia con el tema.
    PATH_FIELD = "#9C8CE0"

    # Fondo del tramo que coincide con lo buscado, en un filtro en vivo.
    MARK_BG = "#5B4A16"

    # --- superficies que faltaban ------------------------------------------
    ROW_LINE = "#2C2C2C"  # separador entre filas de una tabla
    FIELD_BG = "#232323"  # fondo de un campo inline, sin caja hasta el hover

    # --- checkbox deshabilitado PERO tildado --------------------------------
    # Es un estado propio y no "el tildado con opacidad": una location que otra
    # ya incluye tiene que seguir leyendose como TILDADA, solo que no editable.
    # Bajarle la opacidad al tilde la hacia pasar por destildada, que es
    # exactamente lo contrario de lo que hay que comunicar.
    CHECKBOX_ON_DISABLED = "#39325F"
    CHECKBOX_ON_DISABLED_BORDER = "#4A4278"
    CHECKBOX_ON_DISABLED_TICK = "#C6BFEA"

    # --- punto de color de un estado ----------------------------------------
    # Van mas claros que OK/WARNING/ERROR: esos estan calibrados para pintar
    # una barra o un fondo, y un punto de 9 px con esos valores no se ve.
    DOT_OK = "#5CB85C"
    DOT_WARNING = "#D6AE4A"
    DOT_ERROR = "#D65C5C"

    # --- fondo de estado en una fila SELECCIONADA ---------------------------
    # Los escribe apply_theme() mezclando el fondo del estado con el gris de la
    # seleccion. No se aclara el color: aclarar sube el brillo pero no desatura,
    # y la celda queda mas roja en vez de mas gris.
    OK_BG_SELECTED = "#2C4027"
    WARNING_BG_SELECTED = "#403723"
    ERROR_BG_SELECTED = "#402727"

    # Nombre propio de una entidad del pipeline destacado en un mensaje: una
    # task, un preset, un nodo. Hoy vale lo mismo que PATH_COMMON y se ve
    # igual, pero tiene token propio para que retocar la paleta de paths no le
    # cambie el color a algo que no es un path.
    ENTITY = "#C56CF0"


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
    # Alto de un boton de una fila de acciones. Va fijo en los dos roles porque
    # BTN_SECONDARY suma un borde de 1 px sobre el mismo padding que
    # BTN_PRIMARY: sin fijarlo, el secundario queda 2 px mas alto.
    BUTTON_HEIGHT = 30
    SCROLLBAR_WIDTH = 10

    # La cruz de cerrar. 26 px es el minimo comodo para acertarle con el
    # mouse sin apuntar: mas chica se falla y se termina moviendo la ventana.
    CLOSE_BUTTON_SIZE = 26

    # --- tamano de letra de las TABLAS --------------------------------------
    # Lo elige el usuario. Toca SOLO las tablas y no el resto de la ventana:
    # si escalara todo, la ventana crece sin control y los iconos quedan
    # chicos al lado del texto.
    TABLE_FONT_SIZE = 13
    TABLE_FONT_SIZE_MIN = 9
    TABLE_FONT_SIZE_MAX = 20

    # El path va un punto MAS GRANDE que el resto de la tabla. Un path se lee
    # caracter por caracter -un 8 contra un 3, un _v02 contra un _v03- y a la
    # misma medida que el resto es lo primero que cuesta. Subir el ajuste
    # entero para que se lean bien agranda toda la ventana sin necesidad.
    PATH_FONT_OFFSET = 1


# ---------------------------------------------------------------------------
#                                   Temas
# ---------------------------------------------------------------------------
# Un tema es la paleta entera. Los seis definen EXACTAMENTE los mismos tokens:
# si uno agrega o saca una clave, apply_theme() lo grita en vez de dejar un
# color viejo pegado de la paleta anterior.
#
# Se referencian por "id" y NUNCA por indice, ni aca ni en el .ini de la tool:
# agregar un tema en el medio de la lista no puede cambiar cual es el default
# ni que tema tiene guardado el usuario.
#
# Los valores del tema "lga" salen del codigo de las apps Qt/C++ de LGA, no de
# una captura: COLOR_VARS en LGA_Base_QT_C_Py/src/ui/mainwindow/MainWindow.cpp,
# resources/styles/dark_theme.qss y include/lga_base_qt_c_py/DialogStyle.h.
# Ahi el violeta es el MISMO del pack (#443a91 / #774dcb) y no hay un solo
# texto blanco: txt_principal es #B2B2B2 y ese es tambien el color del texto de
# los botones, incluido el violeta de accion.

THEMES = (
    {
        "id": "lga",
        "label": "LGA",
        "desc": (
            "Los colores exactos de las apps Qt/C++ de LGA (FileManager S3, PipeSync). Como el del pack pero mas oscuro, y sin ningun texto blanco."
        ),
        "colors": {
            "WINDOW": "#161616",
            "SURFACE": "#1D1D1D",
            "SURFACE_RAISED": "#2A2A2A",
            "SURFACE_HEADER": "#1A1A1A",
            "SURFACE_HOVER": "#383838",
            "SURFACE_SELECTED": "#2E2E2E",
            "ROW_LINE": "#232323",
            "FIELD_BG": "#1A1A1A",
            "TEXT": "#B2B2B2",
            "TEXT_STRONG": "#D0D0D0",
            "TEXT_DIM": "#7B7B7B",
            "TEXT_HEADER": "#8F8F8F",
            "TEXT_ON_ACCENT": "#D0D0D0",
            "BORDER": "#303030",
            "BORDER_STRONG": "#3A3A3A",
            "BORDER_HOVER": "#4A4A4A",
            "ACCENT": "#443A91",
            "ACCENT_HOVER": "#774DCB",
            "CHECKBOX_OFF": "#2A2832",
            "CHECKBOX_OFF_HOVER": "#3A3744",
            "CHECKBOX_ON": "#393455",
            "CHECKBOX_ON_HOVER": "#4C4770",
            "CHECKBOX_BORDER": "#272727",
            "CHECKBOX_ON_DISABLED": "#332F4A",
            "CHECKBOX_ON_DISABLED_BORDER": "#413C5E",
            "CHECKBOX_ON_DISABLED_TICK": "#B5AFD2",
            "OK_BG": "#1D4413",
            "WARNING_BG": "#44330E",
            "ERROR_BG": "#461616",
            "SURFACE_SUNKEN": "#0E0E0E",
            "ACCENT_DISABLED": "#272445",
            "ACCENT_TRACK": "#362F6C",
            "DOT_OK": "#5FA855",
            "DOT_WARNING": "#C4A048",
            "DOT_ERROR": "#C45E5E",
            "PATH_COMMON": "#C56CF0",
            "PATH_SEPARATOR": "#5A5A5E",
            "MARK_BG": "#4E3F0E",
        },
    },
    {
        "id": "pack",
        "label": "Pack",
        "desc": (
            "Lo que hay hoy en LGA_UI_Style_ToolPack: gris 212121 y el violeta de la marca."
        ),
        "colors": {
            "WINDOW": "#212121",
            "SURFACE": "#272727",
            "SURFACE_RAISED": "#2E2E2E",
            "SURFACE_HEADER": "#2B2B2B",
            "SURFACE_HOVER": "#383838",
            "SURFACE_SELECTED": "#353535",
            "ROW_LINE": "#2C2C2C",
            "FIELD_BG": "#232323",
            "TEXT": "#A7A7A7",
            "TEXT_STRONG": "#E8E8E8",
            "TEXT_DIM": "#6E6E6E",
            "TEXT_HEADER": "#999999",
            "TEXT_ON_ACCENT": "#FFFFFF",
            "BORDER": "#333333",
            "BORDER_STRONG": "#444444",
            "BORDER_HOVER": "#555555",
            "ACCENT": "#443A91",
            "ACCENT_HOVER": "#774DCB",
            "CHECKBOX_OFF": "#2A2832",
            "CHECKBOX_OFF_HOVER": "#3A3744",
            "CHECKBOX_ON": "#393455",
            "CHECKBOX_ON_HOVER": "#4C4770",
            "CHECKBOX_BORDER": "#444444",
            "CHECKBOX_ON_DISABLED": "#39325F",
            "CHECKBOX_ON_DISABLED_BORDER": "#4A4278",
            "CHECKBOX_ON_DISABLED_TICK": "#C6BFEA",
            "OK_BG": "#244C19",
            "WARNING_BG": "#6B4A0F",
            "ERROR_BG": "#5A1A1A",
            "SURFACE_SUNKEN": "#1A1A1A",
            "ACCENT_DISABLED": "#2A2540",
            "ACCENT_TRACK": "#393959",
            "DOT_OK": "#5CB85C",
            "DOT_WARNING": "#D6AE4A",
            "DOT_ERROR": "#D65C5C",
            "PATH_COMMON": "#C56CF0",
            "PATH_SEPARATOR": "#6A6A6E",
            "MARK_BG": "#5B4A16",
        },
    },
    {
        "id": "graphite",
        "label": "Graphite",
        "desc": (
            "Mas oscuro y con mas contraste entre niveles. El violeta sube para no perderse contra el fondo."
        ),
        "colors": {
            "WINDOW": "#171717",
            "SURFACE": "#1E1E1E",
            "SURFACE_RAISED": "#272727",
            "SURFACE_HEADER": "#222222",
            "SURFACE_HOVER": "#323232",
            "SURFACE_SELECTED": "#2E2E2E",
            "ROW_LINE": "#262626",
            "FIELD_BG": "#1A1A1A",
            "TEXT": "#A2A2A2",
            "TEXT_STRONG": "#F0F0F0",
            "TEXT_DIM": "#6A6A6A",
            "TEXT_HEADER": "#8F8F8F",
            "TEXT_ON_ACCENT": "#FFFFFF",
            "BORDER": "#2C2C2C",
            "BORDER_STRONG": "#3D3D3D",
            "BORDER_HOVER": "#525252",
            "ACCENT": "#5B4FC4",
            "ACCENT_HOVER": "#8A62E0",
            "CHECKBOX_OFF": "#242230",
            "CHECKBOX_OFF_HOVER": "#332F42",
            "CHECKBOX_ON": "#5B4FC4",
            "CHECKBOX_ON_HOVER": "#6F62DC",
            "CHECKBOX_BORDER": "#1E1E1E",
            "CHECKBOX_ON_DISABLED": "#3B3468",
            "CHECKBOX_ON_DISABLED_BORDER": "#4E4682",
            "CHECKBOX_ON_DISABLED_TICK": "#CDC6F0",
            "OK_BG": "#1E4415",
            "WARNING_BG": "#45330D",
            "ERROR_BG": "#471515",
            "SURFACE_SUNKEN": "#0F0F0F",
            "ACCENT_DISABLED": "#312C59",
            "ACCENT_TRACK": "#473E90",
            "DOT_OK": "#63C463",
            "DOT_WARNING": "#DFB753",
            "DOT_ERROR": "#E06666",
            "PATH_COMMON": "#C56CF0",
            "PATH_SEPARATOR": "#5E5E62",
            "MARK_BG": "#54430F",
        },
    },
    {
        "id": "slate",
        "label": "Slate",
        "desc": (
            "Superficies con tinte azul frio y el acento corrido a indigo. Los paths de colores calidos resaltan mas."
        ),
        "colors": {
            "WINDOW": "#1B1E24",
            "SURFACE": "#21252D",
            "SURFACE_RAISED": "#2A2F39",
            "SURFACE_HEADER": "#252A33",
            "SURFACE_HOVER": "#333945",
            "SURFACE_SELECTED": "#2F343E",
            "ROW_LINE": "#282D36",
            "FIELD_BG": "#1D2128",
            "TEXT": "#A3ACBA",
            "TEXT_STRONG": "#E9EDF3",
            "TEXT_DIM": "#6B7484",
            "TEXT_HEADER": "#939CAA",
            "TEXT_ON_ACCENT": "#FFFFFF",
            "BORDER": "#2E3440",
            "BORDER_STRONG": "#3E4553",
            "BORDER_HOVER": "#4E5666",
            "ACCENT": "#4A55C8",
            "ACCENT_HOVER": "#6E7BE8",
            "CHECKBOX_OFF": "#262B37",
            "CHECKBOX_OFF_HOVER": "#333A49",
            "CHECKBOX_ON": "#4A55C8",
            "CHECKBOX_ON_HOVER": "#5F6BDC",
            "CHECKBOX_BORDER": "#21252D",
            "CHECKBOX_ON_DISABLED": "#333A6B",
            "CHECKBOX_ON_DISABLED_BORDER": "#454E85",
            "CHECKBOX_ON_DISABLED_TICK": "#C3C9EF",
            "OK_BG": "#1F4A2C",
            "WARNING_BG": "#4A3A18",
            "ERROR_BG": "#4A2024",
            "SURFACE_SUNKEN": "#121417",
            "ACCENT_DISABLED": "#2D3362",
            "ACCENT_TRACK": "#3C4497",
            "DOT_OK": "#5FC287",
            "DOT_WARNING": "#DDB35C",
            "DOT_ERROR": "#E0687A",
            "PATH_COMMON": "#C56CF0",
            "PATH_SEPARATOR": "#5A626E",
            "MARK_BG": "#57461A",
        },
    },
    {
        "id": "nuke",
        "label": "Nuke",
        "desc": (
            "Grises mas claros, cerca de los de Nuke, para que la ventana no sea una mancha negra adentro del host."
        ),
        "colors": {
            "WINDOW": "#2B2B2B",
            "SURFACE": "#333333",
            "SURFACE_RAISED": "#3B3B3B",
            "SURFACE_HEADER": "#373737",
            "SURFACE_HOVER": "#464646",
            "SURFACE_SELECTED": "#434343",
            "ROW_LINE": "#3A3A3A",
            "FIELD_BG": "#2E2E2E",
            "TEXT": "#B4B4B4",
            "TEXT_STRONG": "#EFEFEF",
            "TEXT_DIM": "#828282",
            "TEXT_HEADER": "#A6A6A6",
            "TEXT_ON_ACCENT": "#FFFFFF",
            "BORDER": "#3F3F3F",
            "BORDER_STRONG": "#505050",
            "BORDER_HOVER": "#616161",
            "ACCENT": "#5346A8",
            "ACCENT_HOVER": "#8058D8",
            "CHECKBOX_OFF": "#38363F",
            "CHECKBOX_OFF_HOVER": "#464350",
            "CHECKBOX_ON": "#5346A8",
            "CHECKBOX_ON_HOVER": "#6857C6",
            "CHECKBOX_BORDER": "#333333",
            "CHECKBOX_ON_DISABLED": "#474071",
            "CHECKBOX_ON_DISABLED_BORDER": "#585089",
            "CHECKBOX_ON_DISABLED_TICK": "#CFC9EC",
            "OK_BG": "#2F5A24",
            "WARNING_BG": "#5A481D",
            "ERROR_BG": "#5A2828",
            "SURFACE_SUNKEN": "#1C1C1C",
            "ACCENT_DISABLED": "#3A355A",
            "ACCENT_TRACK": "#473E82",
            "DOT_OK": "#6FC46F",
            "DOT_WARNING": "#DDB85E",
            "DOT_ERROR": "#DF7373",
            "PATH_COMMON": "#C56CF0",
            "PATH_SEPARATOR": "#767676",
            "MARK_BG": "#665220",
        },
    },
    {
        "id": "high-contrast",
        "label": "High contrast",
        "desc": (
            "Negro real y bordes marcados. Para monitores muy oscuros o para leer la tabla de lejos."
        ),
        "colors": {
            "WINDOW": "#0D0D0D",
            "SURFACE": "#151515",
            "SURFACE_RAISED": "#1F1F1F",
            "SURFACE_HEADER": "#191919",
            "SURFACE_HOVER": "#2B2B2B",
            "SURFACE_SELECTED": "#282828",
            "ROW_LINE": "#202020",
            "FIELD_BG": "#101010",
            "TEXT": "#B8B8B8",
            "TEXT_STRONG": "#FFFFFF",
            "TEXT_DIM": "#787878",
            "TEXT_HEADER": "#A0A0A0",
            "TEXT_ON_ACCENT": "#FFFFFF",
            "BORDER": "#303030",
            "BORDER_STRONG": "#484848",
            "BORDER_HOVER": "#5E5E5E",
            "ACCENT": "#6A5AE0",
            "ACCENT_HOVER": "#9370FF",
            "CHECKBOX_OFF": "#1E1C2A",
            "CHECKBOX_OFF_HOVER": "#2E2B3E",
            "CHECKBOX_ON": "#6A5AE0",
            "CHECKBOX_ON_HOVER": "#7F6EF5",
            "CHECKBOX_BORDER": "#151515",
            "CHECKBOX_ON_DISABLED": "#413876",
            "CHECKBOX_ON_DISABLED_BORDER": "#564C95",
            "CHECKBOX_ON_DISABLED_TICK": "#DAD4FA",
            "OK_BG": "#173D0F",
            "WARNING_BG": "#3F2E08",
            "ERROR_BG": "#420F0F",
            "SURFACE_SUNKEN": "#080808",
            "ACCENT_DISABLED": "#302A5D",
            "ACCENT_TRACK": "#4E43A1",
            "DOT_OK": "#6ED66E",
            "DOT_WARNING": "#EFC45E",
            "DOT_ERROR": "#F07070",
            "PATH_COMMON": "#D07BF7",
            "PATH_SEPARATOR": "#6E6E72",
            "MARK_BG": "#4C3B0A",
        },
    },
)

# El juego de tokens que TIENE que traer cada tema, escrito una vez. Se declara
# explicito y no se saca de THEMES[0]: sacarlo del primero es referenciar un
# tema por indice, que es exactamente lo que este modulo dice no hacer.
THEME_TOKENS = frozenset(THEMES[0]["colors"])


# El tema BASE es el que reciben las tools que no piden ninguno, o sea las que
# hacen `from ... import Style, Color`. Es "pack" y tiene que seguir siendolo:
# son once ventanas ya migradas que nadie pidio cambiar, y cambiarlas desde
# aca seria decidir por ellas sin que ninguna se entere.
#
# Una tool que quiere otro aspecto lo pide: `UI = theme("lga")`. El Media
# Manager usa "lga", que son los colores exactos de las apps Qt/C++ de LGA.
BASE_THEME = "pack"


def theme_ids():
    """Los id de los temas, en el orden en que se muestran."""
    return tuple(t["id"] for t in THEMES)


def get_theme(theme_id):
    """El tema pedido, o el default si ese id no existe.

    No explota con un id desconocido: un .ini escrito por una version mas
    nueva del pack, o a mano, tiene que dejar la ventana usable.
    """
    for tema in THEMES:
        if tema["id"] == theme_id:
            return tema
    for tema in THEMES:
        if tema["id"] == BASE_THEME:
            return tema
    return THEMES[0]


# La tilde del checkbox viaja al lado de este modulo. QSS pide una ruta de
# archivo y en Windows hay que pasarla con "/": con "\\" Qt no la resuelve y el
# checkbox queda prendido pero sin tilde, que es peor que no estilarlo.
_ICON_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKMARK_PATH = os.path.join(_ICON_DIR, "LGA_UI_checkmark.svg").replace("\\", "/")
# Tilde apagada para el checkbox deshabilitado. Sin ella la tilde blanca
# sobrevive a intensidad plena y lo apagado termina gritando mas que lo activo.
CHECKMARK_OFF_PATH = os.path.join(_ICON_DIR, "LGA_UI_checkmark_off.svg").replace(
    "\\", "/"
)


# ---------------------------------------------------------------------------
#                                  Estilos
# ---------------------------------------------------------------------------
# Barra de scroll. Va suelta y no adentro de un estilo concreto porque la
# comparten la tabla, los campos de texto multilinea y cualquier area
# scrolleable: cuando estaba copiada en cada tool cada una le puso un ancho
# distinto (8 o 12 px) y el salto se notaba al comparar dos ventanas.


class Style(object):
    """QSS listo para usar. Se arma con la paleta de arriba, nunca con hex."""

    # Los atributos los escribe _build_styles(). Antes se armaban en el
    # cuerpo de la clase, o sea una sola vez al importar el modulo, y no
    # habia forma de tener dos temas a la vez.
    #
    # Esta clase es la del tema BASE. Los otros temas tienen la suya, que
    # se pide con theme(id).Style.
    pass


def _build_styles(Color, Style):
    """
    Arma todas las hojas de UN tema.

    Color y Style son parametros a proposito y no los objetos del modulo:
    asi cada tema tiene su juego propio y dos tools con temas distintos no
    se pisan. El cuerpo de abajo los usa por nombre, igual que antes.
    """

    _scrollbar = """
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
"""     % {
        "window": Color.WINDOW,
        "border": Color.BORDER_STRONG,
        "border_hover": Color.BORDER_HOVER,
        "sb": Metric.SCROLLBAR_WIDTH,
        "sb_radius": Metric.SCROLLBAR_WIDTH // 2,
    }
    Style.SCROLLBAR = _scrollbar

    # Fondo de la ventana. Va sin border-radius: una ventana con esquinas
    # redondeadas y sin frame deja los cuatro angulos del rectangulo pintados
    # por debajo, que se ve peor que la esquina cuadrada.
    Style.WINDOW = "QWidget { background-color: %s; color: %s; }" % (
        Color.WINDOW,
        Color.TEXT,
    )

    # Caja apoyada sobre la ventana (avisos, agrupaciones).
    Style.PANEL = "background-color: %s; border-radius: %dpx;" % (
        Color.SURFACE,
        Metric.RADIUS,
    )

    # --- botones -----------------------------------------------------------
    # El boton de accion. Es el unico violeta de la ventana: si hay dos, el
    # usuario no sabe cual ejecuta Enter.
    Style.BTN_PRIMARY = """
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
    Style.BTN_SECONDARY = """
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
    Style.BTN_SMALL = """
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
    Style.BTN_ICON = """
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
    Style.BTN_CLOSE = """
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
    Style.LINE_EDIT = """
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

    Style.COMBO = """
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

    # El indicador se dibuja a mano: el nativo de Qt es una tilde que cambia
    # con el tema del host, asi que el mismo checkbox se veia distinto en Nuke,
    # en Hiero y en las apps Qt. Nunca poner background al QCheckBox entero:
    # colorea tambien el texto y el padding.
    Style.CHECKBOX = """
QCheckBox {
    color: %(text)s;
    padding: 2px;
    background: transparent;
    border: none;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background-color: %(off)s;
    border: 1px solid %(border)s;
    border-radius: %(radius)dpx;
}
QCheckBox::indicator:unchecked:hover { background-color: %(off_hover)s; }
QCheckBox::indicator:checked {
    background-color: %(on)s;
    image: url(%(checkmark)s);
}
QCheckBox::indicator:checked:hover { background-color: %(on_hover)s; }
QCheckBox:disabled { color: %(text_dim)s; }
QCheckBox::indicator:disabled {
    background-color: %(surface)s;
    border-color: %(border_dis)s;
}
QCheckBox::indicator:checked:disabled {
    background-color: %(on_dis)s;
    border-color: %(on_dis_border)s;
    image: url(%(checkmark_off)s);
}
""" % {
        "text": Color.TEXT,
        "off": Color.CHECKBOX_OFF,
        "off_hover": Color.CHECKBOX_OFF_HOVER,
        "on": Color.CHECKBOX_ON,
        "on_hover": Color.CHECKBOX_ON_HOVER,
        # "border" estaba dos veces en este dict y ganaba la segunda, asi que
        # CHECKBOX_BORDER estaba muerto y el borde real salia de BORDER_STRONG.
        "border": Color.CHECKBOX_BORDER,
        "border_dis": Color.BORDER_STRONG,
        "on_dis": Color.CHECKBOX_ON_DISABLED,
        "on_dis_border": Color.CHECKBOX_ON_DISABLED_BORDER,
        "surface": Color.SURFACE,
        "checkmark": CHECKMARK_PATH,
        "checkmark_off": CHECKMARK_OFF_PATH,
        "text_dim": Color.TEXT_DIM,
        "radius": Metric.RADIUS_SMALL,
    }

    # --- tooltip -----------------------------------------------------------
    # Mismos valores que LGA_tooltip_helper. Existe aca duplicado porque ese
    # helper vive SOLO en el ToolPack: los paneles de los otros dos packs lo
    # importan en un try y se quedan sin nada si el usuario no tiene instalado
    # el ToolPack, que es justo la dependencia cruzada que este modulo evita.
    # Con esto, el pack que no tenga el helper igual pinta sus tooltips.
    # Los dos hex van a mano a proposito: son los mismos de
    # LGA_tooltip_helper, y si aca salieran del tema, un pack con el helper
    # instalado y otro sin el pintarian tooltips distintos.
    Style.TOOLTIP = """
QToolTip {
    background-color: #1E1E1E;
    color: #CCCCCC;
    border: none;
    border-radius: 6px;
    padding: 12px;
}
"""

    # Barra de progreso. El riel va en un violeta apagado y el relleno en el
    # violeta de la app: es la misma senal que el boton de accion, asi que se
    # lee como "esto es lo que pediste, avanzando".
    Style.PROGRESS = """
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

    # El fondo de ventana arrastra el checkbox: es la hoja que aplican
    # casi todas las ventanas, y sin esto quedaban con el del host.
    Style.WINDOW = Style.WINDOW + Style.CHECKBOX

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
    Style.FORM = """
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
%(checkbox)s
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
/* El spinbox se deja NATIVO a proposito. En cuanto el QSS le define caja o
   flechitas, Qt deja de dibujar los triangulos y encima la sub-control queda
   pisando el numero. Lo unico que hace falta es sacarle de encima la regla de
   QLineEdit de arriba, que le cae al campo interno y le suma un segundo borde
   y un segundo padding adentro de su propia caja. */
QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {
    border: none;
    padding: 0px;
    background: transparent;
}
%(scrollbar)s
""" % {
        "scrollbar": _scrollbar,
        "checkbox": Style.CHECKBOX,
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
    Style.TABLE = """
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
        "scrollbar": _scrollbar,
    }

    # Bloque de detalle tecnico (traceback, salida de un proceso). Va mas
    # oscuro que la ventana a proposito, para que se lea como un bloque de
    # datos pegado y no como una segunda parte del mensaje.
    Style.DETAIL = """
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

    return Style


# ---------------------------------------------------------------------------
#                            Elegir un tema
# ---------------------------------------------------------------------------
# Cada tema se arma una vez y queda cacheado. No hay "tema activo": el tema es
# de la tool que lo pide, no del modulo.
_themes = {}


def _mix(color_a, color_b, factor=0.5):
    """Mezcla dos hex. factor 0 devuelve el primero y 1 el segundo."""
    def canales(valor):
        valor = valor.lstrip("#")
        return [int(valor[i:i + 2], 16) for i in (0, 2, 4)]

    a, b = canales(color_a), canales(color_b)
    mezcla = [int(round(x + (y - x) * factor)) for x, y in zip(a, b)]
    return "#%02X%02X%02X" % tuple(mezcla)


def _derivados(colores):
    """
    Los tokens que no se escriben a mano en cada tema.

    El fondo de una celda de estado en la fila SELECCIONADA se mezcla contra
    el gris de la seleccion, no se aclara: aclarar sube el brillo pero no
    desatura, y la celda queda mas roja en vez de mas gris.
    """
    sel = colores["SURFACE_SELECTED"]
    return {
        "OK_BG_SELECTED": _mix(colores["OK_BG"], sel),
        "WARNING_BG_SELECTED": _mix(colores["WARNING_BG"], sel),
        "ERROR_BG_SELECTED": _mix(colores["ERROR_BG"], sel),
    }


class Theme(object):
    """
    Un tema: su paleta y sus hojas.

        UI = theme("lga")
        ventana.setStyleSheet(UI.Style.WINDOW)
        label.setStyleSheet("color: %s;" % UI.Color.TEXT)
    """

    def __init__(self, spec):
        self.id = spec["id"]
        self.label = spec["label"]
        self.desc = spec["desc"]

        colores = dict(spec["colors"])
        faltantes = sorted(THEME_TOKENS - set(colores))
        sobrantes = sorted(set(colores) - THEME_TOKENS)
        if faltantes or sobrantes:
            raise ValueError(
                "el tema '%s' no coincide con THEME_TOKENS. Faltan: %s. Sobran: %s"
                % (self.id, ", ".join(faltantes) or "-", ", ".join(sobrantes) or "-")
            )
        colores.update(_derivados(colores))

        if self.id == BASE_THEME:
            # El tema base ES la clase Color del modulo, no una copia: las
            # tools que hacen `from ... import Color` tienen que recibir
            # exactamente este objeto.
            for nombre, valor in colores.items():
                setattr(Color, nombre, valor)
            self.Color = Color
            self.Style = _build_styles(Color, Style)
        else:
            # Los demas son subclases: heredan los tokens que NO cambian con
            # el tema (OK, WARNING, INFO, ENTITY, PATH_FIELD, la paleta de
            # paths) y pisan los que si.
            self.Color = type("Color_%s" % self.id.replace("-", "_"),
                              (Color,), colores)
            self.Style = _build_styles(
                self.Color, type("Style_%s" % self.id.replace("-", "_"), (), {})
            )


def theme(theme_id=None):
    """
    El tema pedido, armado y cacheado.

    Con un id desconocido devuelve el base en vez de explotar: un .ini escrito
    por una version mas nueva del pack, o a mano, tiene que dejar la ventana
    usable igual.
    """
    if theme_id not in _themes:
        spec = get_theme(theme_id)
        _themes[spec["id"]] = Theme(spec)
        if theme_id != spec["id"]:
            _themes[theme_id] = _themes[spec["id"]]
    return _themes[theme_id]


# ---------------------------------------------------------------------------
#                                  Fuentes
# ---------------------------------------------------------------------------
# Las fuentes viajan adentro del pack en vez de usar la del sistema: en macOS
# la del sistema es SF Pro y en Windows Segoe UI, o sea que la misma ventana se
# ve distinta en cada maquina y cualquier ancho ajustado en una se corre en la
# otra.
#
# Son TTF y no woff2 a proposito: QFontDatabase.addApplicationFont carga TTF y
# OTF, y no soporta woff2.
_FONT_DIR = os.path.join(_ICON_DIR, "fonts")
_UI_FONT_FILES = ("Inter-400.ttf", "Inter-600.ttf", "Inter-700.ttf")
# Mono SOLO para el campo de ruta EDITABLE de un formulario: ahi las rutas son
# relativas y con Inter los "../" no se distinguen, el punto y la barra se
# pegan. En una tabla de rutas absolutas Inter se lee mejor.
_MONO_FONT_FILES = ("JetBrainsMono-400.ttf", "JetBrainsMono-500.ttf")

_families = None


def _register(archivos):
    """Registra una familia y devuelve su nombre real, o "" si no cargo."""
    try:
        from LGA_QtAdapter_ToolPack import QtGui
    except Exception:
        return ""

    nombres = []
    for archivo in archivos:
        ruta = os.path.join(_FONT_DIR, archivo)
        if not os.path.exists(ruta):
            continue
        try:
            ident = QtGui.QFontDatabase.addApplicationFont(ruta)
        except Exception:
            continue
        if ident == -1:
            continue
        try:
            nombres += list(QtGui.QFontDatabase.applicationFontFamilies(ident))
        except Exception:
            pass
    # Se devuelve el nombre que informa Qt y no la string "Inter": si el
    # archivo no cargo hay que caer a la fuente del host, no pedir una familia
    # que no existe -eso deja la ventana con la fuente por default de Qt.
    return nombres[0] if nombres else ""


def load_fonts():
    """
    Registra las fuentes del pack UNA sola vez por sesion de Nuke.

    Devuelve (familia_ui, familia_mono). Cualquiera de las dos puede venir
    vacia: sin fuente propia se usa la del host, que es feo pero funciona.
    """
    global _families
    if _families is not None:
        return _families
    familias = (_register(_UI_FONT_FILES), _register(_MONO_FONT_FILES))
    # Se cachea SOLO si cargo algo. addApplicationFont devuelve -1 mientras no
    # exista QApplication, asi que cachear el fracaso dejaba al pack sin sus
    # fuentes para el resto de la sesion de Nuke aunque la GUI ya estuviera
    # levantada.
    if familias[0] or familias[1]:
        _families = familias
    return familias


def font_family():
    """La familia de interfaz, o "" si no se pudo cargar."""
    return load_fonts()[0]


def mono_family():
    """La familia mono, o "" si no se pudo cargar."""
    return load_fonts()[1]


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


# El modulo se arma apenas se importa con el tema BASE: sin esto,
# Style.LO_QUE_SEA no existe y cualquier tool que lo pida al construir su
# ventana explota.
#
# Que el base sea "pack" es lo que hace que este cambio sea invisible para las
# tools que ya estaban: siguen haciendo `from ... import Style, Color` y
# reciben lo mismo de siempre, sin tocarles una linea. La que quiera otro tema
# lo pide con theme("lga") y no le cambia el aspecto a ninguna otra.
theme(BASE_THEME)

# Suelto, por compatibilidad: hay una tool que hace
# `from ... import SCROLLBAR`. Como es un string, ese import liga por VALOR,
# asi que solo puede traer el del tema base.
SCROLLBAR = Style.SCROLLBAR
