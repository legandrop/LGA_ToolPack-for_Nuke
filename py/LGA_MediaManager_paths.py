"""
_______________________________________

  LGA_MediaManager_paths v2.37 | Lega
  Como se interpretan las rutas relativas al .nk

  El shot folder y las locations se escriben como rutas RELATIVAS a la
  carpeta del .nk, con comodines. Este modulo es el unico lugar donde
  esa notacion se interpreta: lo usan la ventana de ajustes -para la
  columna "Resolves to" y para el scan efectivo- y el FileScanner
  -para saber donde buscar y donde termina el shot-.

  Dos mitades, y la division importa:

    parse_path / includes / shot_segments   NO tocan disco. Son
        instantaneas y se pueden llamar en cada tecla.
    resolve                                 TOCA DISCO. Va en un
        worker o con debounce y editingFinished, nunca en textChanged:
        contra un servidor, resolver un comodin en cada tecla cuelga
        la ventana.

  No importa Qt a proposito: asi se puede probar sin PySide.

  v2.27: Modulo nuevo. Sale del prototipo del rediseno, donde esta
         escrito en JS.
_______________________________________

"""

import os
import re


# Un patron con comodines en varios niveles puede abrir muchisimas ramas. El
# tope existe para que una ruta como "*/*/*" contra un servidor no deje la
# ventana colgada enumerando: se corta, y quien llama muestra que hay mas.
MAX_MATCHES = 512


# Los cuatro resultados posibles de interpretar el texto de una ruta. Se
# distinguen porque la UI dice una cosa distinta en cada caso.
EMPTY = "empty"  # el campo esta vacio
INVALID = "invalid"  # sube mas alto que la raiz
ABSOLUTE = "absolute"  # no se resuelve contra el .nk
RELATIVE = "relative"  # lo normal


class ParsedPath(object):
    """
    El texto de una ruta ya interpretado, sin haber tocado disco.

    `segments` son los segmentos del resultado, ya con los ".." aplicados.
    `root` es lo que va adelante al rearmar la ruta: "" en relativa (porque
    los segmentos del .nk ya lo traen), "/" o "C:/" o "//server/" en absoluta.
    """

    __slots__ = ("kind", "segments", "root")

    def __init__(self, kind, segments=None, root=""):
        self.kind = kind
        self.segments = segments or []
        self.root = root

    @property
    def usable(self):
        """Si se puede intentar resolverla contra disco."""
        return self.kind in (RELATIVE, ABSOLUTE)

    def as_path(self):
        """La ruta rearmada, sin resolver los comodines."""
        if not self.usable:
            return ""
        return self.root + "/".join(self.segments)

    def __repr__(self):
        return "ParsedPath(%s, %r, root=%r)" % (self.kind, self.segments, self.root)


class Resolution(object):
    """
    A que carpetas REALES llega una ruta.

    `folders` son rutas absolutas existentes. Puede tener 0, 1 o N: un comodin
    no promete unicidad y la UI tiene que poder decirlo.
    """

    __slots__ = ("kind", "folders", "truncated")

    def __init__(self, kind, folders=None, truncated=False):
        self.kind = kind
        self.folders = folders or []
        self.truncated = truncated

    def __repr__(self):
        return "Resolution(%s, %r%s)" % (
            self.kind, self.folders, ", truncated" if self.truncated else ""
        )


def _slashes(texto):
    """Barras normales, sin repetir, conservando el prefijo UNC."""
    texto = (texto or "").replace("\\", "/")
    unc = texto.startswith("//")
    texto = re.sub(r"/{2,}", "/", texto)
    return ("/" + texto) if unc else texto


def _is_absolute(texto):
    """
    Si la ruta NO es relativa al .nk.

    Mismo criterio que LGA_MediaManager_config.is_absolute, y por el mismo
    motivo: el .ini se comparte entre las dos maquinas, asi que una ruta de
    Windows tiene que reconocerse tambien corriendo en Mac. Se repite en vez
    de importarse para que este modulo no dependa del otro; si alguna vez
    divergen, manda config.
    """
    if not texto:
        return False
    return (
        texto.startswith("/")
        or texto.startswith("\\\\")
        or bool(re.match(r"^[A-Za-z]:", texto))
        or texto[0] in "~$%"
    )


def _expand(texto):
    """`~` y las variables de entorno, que en un pipeline de Nuke son comunes."""
    return os.path.expandvars(os.path.expanduser(texto))


def _split_root(texto):
    """
    Separa el prefijo que NO es un segmento navegable.

    Devuelve (root, resto). El root queda con la barra final puesta, asi que
    root + "/".join(segs) rearma la ruta.
    """
    if texto.startswith("//"):
        # UNC: //server/share es la raiz, no dos carpetas. Bajar de ahi con
        # ".." no lleva a ningun lado.
        partes = [p for p in texto[2:].split("/") if p]
        raiz = "//" + "/".join(partes[:2])
        return raiz + "/", partes[2:]
    match = re.match(r"^([A-Za-z]:)/?", texto)
    if match:
        return match.group(1) + "/", [p for p in texto[len(match.group(0)):].split("/") if p]
    if texto.startswith("/"):
        return "/", [p for p in texto[1:].split("/") if p]
    return "", [p for p in texto.split("/") if p]


def parse_path(path, nk_dir=""):
    """
    Interpreta el texto de una ruta contra la carpeta del .nk. No toca disco.

    Un ".." de mas NO se ignora: la ruta queda invalida y hay que decirlo.
    Callandolo, "../../../../.." resolvia a la raiz, la columna la daba por
    buena, y peor: al no quedarle segmentos, esa location incluia a TODAS las
    demas y les apagaba el Scan.
    """
    texto = _slashes(path).strip()
    if not texto:
        return ParsedPath(EMPTY)

    if _is_absolute(texto):
        raiz, segs = _split_root(_slashes(_expand(texto)))
        resultado = []
        for parte in segs:
            if parte in ("", "."):
                continue
            if parte == "..":
                if not resultado:
                    return ParsedPath(INVALID)
                resultado.pop()
                continue
            resultado.append(parte)
        return ParsedPath(ABSOLUTE, resultado, raiz)

    raiz, base = _split_root(_slashes(nk_dir).strip())
    segs = list(base)
    for parte in texto.split("/"):
        if parte in ("", "."):
            continue
        if parte == "..":
            if not segs:
                return ParsedPath(INVALID)
            segs.pop()
            continue
        segs.append(parte)
    return ParsedPath(RELATIVE, segs, raiz)


def _pattern_re(patron, ignorecase=True):
    """Un segmento con `*` como expresion regular anclada."""
    partes = [re.escape(p) for p in patron.split("*")]
    return re.compile("^" + ".*".join(partes) + "$", re.I if ignorecase else 0)


def _match_segment(patron, nombres):
    """
    Los nombres de `nombres` que coinciden con el patron.

    Sin distinguir mayusculas en las dos ramas: los filesystems de macOS y
    Windows no distinguen, y con la rama literal distinguiendo, "_INPUT" no
    encontraba "_input" pero "_INP*T" si, que es incoherente.
    """
    if "*" not in patron:
        objetivo = patron.lower()
        return [n for n in nombres if n.lower() == objetivo]
    rx = _pattern_re(patron)
    return [n for n in nombres if rx.match(n)]


def _subdirs(ruta):
    """Los nombres de las subcarpetas de `ruta`. [] si no se puede leer."""
    try:
        with os.scandir(ruta) as entradas:
            return [e.name for e in entradas if e.is_dir()]
    except (OSError, ValueError):
        # Un permiso denegado o una unidad desconectada no son un error de la
        # ruta que escribio el usuario: son cero coincidencias por ahi.
        return []


def resolve(path, nk_dir=""):
    """
    A que carpetas reales llega una ruta. TOCA DISCO: va fuera del hilo principal.

    Baja nivel por nivel en vez de usar glob.glob porque glob distingue
    mayusculas en macOS y en Linux, y aca no se quiere distinguir.
    """
    parsed = parse_path(path, nk_dir)
    if not parsed.usable:
        return Resolution(parsed.kind)

    # Sin raiz, el nk_dir tambien era relativo: se resuelve contra el
    # directorio actual, que es lo unico que se puede hacer.
    actuales = [parsed.root or "."]
    truncado = False

    for segmento in parsed.segments:
        siguientes = []
        lleno = False
        for base in actuales:
            for nombre in _match_segment(segmento, _subdirs(base)):
                siguientes.append(base.rstrip("/") + "/" + nombre)
                if len(siguientes) >= MAX_MATCHES:
                    lleno = True
                    break
            if lleno:
                break
        truncado = truncado or lleno
        actuales = siguientes
        if not actuales:
            return Resolution(parsed.kind, [], truncado)

    return Resolution(parsed.kind, actuales, truncado)


def seg_matches(pattern, target):
    """
    Si el segmento `pattern` abarca al segmento `target`.

    El `*` del objetivo se neutraliza antes de comparar: si no, el comodin de
    una location haria juego con el comodin de la otra y dos rutas distintas
    se darian por la misma.
    """
    if pattern == "*":
        return True
    if pattern.lower() == target.lower():
        return True
    return bool(_pattern_re(pattern).match(target.replace("*", "x")))


def _joined(parsed):
    """Los segmentos como una sola string comparable, sin distinguir mayusculas."""
    return "/".join(parsed.segments).lower()


def includes(a, b, nk_dir=""):
    """
    Si la location `a` incluye a la `b`. NO toca disco.

    `a` incluye a `b` cuando esta mas arriba y cada uno de sus segmentos
    abarca al de `b`: como el escaneo es recursivo, con el prefijo alcanza.
    Una ruta no se incluye a si misma.
    """
    ra, rb = parse_path(a, nk_dir), parse_path(b, nk_dir)
    if not ra.usable or not rb.usable:
        return False
    # Se comparan los segmentos YA resueltos, asi que una location absoluta y
    # una relativa que caen en el mismo lado si se comparan: lo que las tiene
    # que separar es la unidad o el servidor, no como esten escritas.
    if ra.root.lower() != rb.root.lower():
        return False
    if len(ra.segments) > len(rb.segments):
        return False
    # A la misma profundidad todavia puede incluirla -"comp/*" abarca a
    # "comp/roto"- pero no si son la MISMA ruta: nadie se incluye a si mismo.
    if _joined(ra) == _joined(rb):
        return False
    return all(seg_matches(s, rb.segments[i]) for i, s in enumerate(ra.segments))


def scanning_parent(locations, index, nk_dir=""):
    """
    La location con Scan prendido que ya incluye a la del indice `index`.

    Mira el scan EXPLICITO de las otras filas y no el efectivo: con el
    efectivo, dos rutas que se incluyen mutuamente se apagarian la una a la
    otra en loop y ninguna de las dos terminaria escaneandose.
    """
    objetivo = locations[index]
    for i, otra in enumerate(locations):
        if i == index or not otra.get("scan"):
            continue
        if includes(otra.get("path", ""), objetivo.get("path", ""), nk_dir):
            return otra
    return None


def shot_segments(shot, nk_dir=""):
    """
    Los segmentos de la carpeta del shot, o [] si no hay ancla.

    De aca sale el ancla del coloreo de paths: los segmentos que coinciden con
    el shot van en PATH_COMMON y el resto cicla la paleta. Sin shot folder no
    hay ancla y ciclan todos desde el principio.
    """
    if not shot or not shot.get("enabled"):
        return []
    parsed = parse_path(shot.get("path", ""), nk_dir)
    if not parsed.usable:
        return []
    return root_segments(parsed.root) + parsed.segments


def root_segments(root):
    """
    Lo que la raiz aporta al path DIBUJADO, como segmentos.

    parse_path deja la unidad o el servidor en `root` y fuera de `segments`,
    pero el path que se muestra en la tabla los trae partidos como un
    segmento mas: "C:/a" se dibuja ["C:", "a"]. Sin devolverlos, la
    comparacion contra la carpeta del shot queda corrida un lugar y el
    coloreo alterna colores sin sentido.
    """
    texto = (root or "").strip()
    if texto.startswith("//"):
        # //server/share es la raiz: los dos van como segmentos dibujados.
        return [p for p in texto[2:].split("/") if p]
    if re.match(r"^[A-Za-z]:", texto):
        return [texto[:2]]
    return []


# ---------------------------------------------------------------------------
#                       Coloreo del path de la tabla
# ---------------------------------------------------------------------------
# Vive aca y no en el modulo de estilo porque lo que decide el color es la
# comparacion contra la carpeta del shot, que es logica de rutas. El modulo de
# estilo pone los colores; este decide a que segmento va cada uno.

def _escape(texto):
    return (texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def path_runs(path, shot_segs=(), common="", palette=(), filename="", separator=""):
    """
    El path partido en tramos (texto, color), listo para pintar.

    Las reglas son las del rediseno:
      - el segmento que coincide con el de la carpeta del shot va en `common`,
        que es lo que hace que de un vistazo se vea donde deja de ser este
        shot y empieza el resto de la ruta;
      - el resto cicla la paleta POR POSICION del segmento, no por posicion
        relativa al shot: asi los segmentos de despues del shot conservan su
        color prendas o apagues el shot folder, y lo unico que cambia es el
        prefijo;
      - el ultimo segmento es el nombre del archivo y va aparte: es lo que se
        lee primero y competia con los colores de las carpetas;
      - las barras van del color del texto fuerte, no grises.
    """
    texto = (path or "").replace("\\", "/")
    partes = texto.split("/")
    # El primer segmento vacio de un path unix se descarta: en "/projects/x"
    # el segmento 0 es "projects", no "". Sin esto toda la comparacion contra
    # el shot queda corrida un lugar.
    arranque = ""
    # El len > 1 importa: sin el, un path vacio se leia como la raiz "/" y la
    # celda mostraba una barra suelta en vez de nada.
    while len(partes) > 1 and partes[0] == "":
        partes = partes[1:]
        arranque += "/"

    runs = []
    if arranque:
        runs.append((arranque, separator))
    ultimo = len(partes) - 1
    for i, parte in enumerate(partes):
        if i == ultimo:
            color = filename
        elif i < len(shot_segs) and parte.lower() == shot_segs[i].lower():
            color = common
        elif palette:
            color = palette[i % len(palette)]
        else:
            color = filename
        runs.append((parte, color))
        if i != ultimo:
            runs.append(("/", separator))
    return runs


def path_html(path, shot_segs=(), common="", palette=(), filename="",
              separator="", query="", mark_bg=""):
    """
    El path como HTML coloreado, con lo buscado resaltado.

    Los tramos que coinciden con la busqueda se calculan sobre el path ENTERO
    y despues se cortan contra los tramos de color: lo que uno escribe casi
    siempre cruza una barra -"mar/img_93"- y midiendo segmento por segmento no
    se resaltaba nada justo en ese caso.
    """
    runs = path_runs(path, shot_segs, common, palette, filename, separator)

    # Los rangos que coinciden, en posiciones del texto completo.
    plano = "".join(t for t, _c in runs)
    marcas = []
    buscado = (query or "").strip().lower()
    if buscado:
        bajo = plano.lower()
        desde = bajo.find(buscado)
        while desde != -1:
            marcas.append((desde, desde + len(buscado)))
            desde = bajo.find(buscado, desde + len(buscado))

    partes = []
    pos = 0
    for texto, color in runs:
        fin = pos + len(texto)
        cortes = [pos, fin]
        for a, b in marcas:
            for corte in (a, b):
                if pos < corte < fin:
                    cortes.append(corte)
        cortes = sorted(set(cortes))
        for a, b in zip(cortes, cortes[1:]):
            trozo = _escape(plano[a:b])
            resaltado = any(m0 <= a and b <= m1 for m0, m1 in marcas)
            if resaltado and mark_bg:
                # Sin padding a proposito: el resaltado puede caer partido en
                # varios tramos y cada uno sumaria su propio aire, separando
                # visualmente "mar" de "/img".
                partes.append(
                    '<span style="color:%s;background-color:%s;">%s</span>'
                    % (color, mark_bg, trozo)
                )
            else:
                partes.append('<span style="color:%s;">%s</span>' % (color, trozo))
        pos = fin
    return "".join(partes)
