"""
_______________________________________________________________________

  LGA_MediaManager_collect v2.52 | Lega

  El PLAN de un Collect: que archivo va a que carpeta del destino, con
  que ruta relativa queda cada knob, y que choca con que.

  No importa Nuke ni Qt a proposito, igual que LGA_MediaManager_paths:
  el plan entero se puede probar sin abrir el host y sin tocar disco.
  Quien lo consume -el FileScanner- pone el inventario, la copia en un
  worker, y el Save As.

  El orden importa y es al reves del que parece: NO se pasa a relativo
  y despues se hace Save As. Una ruta relativa se calcula contra un
  ancla, asi que convertir primero deja los "../.." apuntando contra la
  carpeta VIEJA y al mover el script no resuelven. Primero se decide el
  destino de cada archivo, y la ruta relativa se calcula contra la raiz
  del collect, que es donde va a quedar el .nk.

  v2.52: El destino deja de ser una invencion -una subcarpeta por
         nombre de location, con el .nk en la raiz- y pasa a reproducir
         la estructura REAL que definen los Settings. Es lo unico que
         hace que el script colectado resuelva adentro del collect: el
         shot folder y las locations se escriben relativas al .nk, asi
         que si el .nk no queda en su misma posicion, resuelven al shot
         VIEJO. Medido: un rescan despues de un collect volvia a
         escanear las carpetas del shot original.
         Suma analizar_estructura, raiz_de_collect, destino_del_script,
         relativa_entre y clasificar_en_estructura. Se crea ademas el
         esqueleto completo del shot: sin eso, una location sin
         archivos no existe en el destino y desde el script colectado
         resuelve a cero carpetas.
         relativo_seguro reemplaza a os.path.relpath, que con una
         carpeta que no cuelga de la base devuelve una ruta con ".."
         -se escapa del destino- y entre dos unidades lanza ValueError,
         que con una location absoluta es configuracion valida.
         revisar_destino pasa a comparar la ruta final del SCRIPT, que
         es la condicion exacta que destruye algo, y resuelve los alias
         del sistema de archivos: una letra mapeada al shot metia el
         collect adentro de si mismo sin ni siquiera el aviso.
  v2.51: Suma revisar_destino, la politica de que carpeta sirve como
         destino. Estaba escrita adentro del metodo de Qt y prohibia el
         shot ENTERO, o sea tambien un Comp/collect recien creado que
         no tiene ningun riesgo: Collect copia, no mueve. Ahora se
         bloquea solo la carpeta del .nk -el scriptSaveAs final la
         pisaria- y adentro de una scan location se avisa nomas.
  v2.48: Modulo nuevo. Cuatro cosas que salieron de auditarlo y que
         conviene no volver a romper: el token del frame se sustituye
         POR POSICION -con str.replace, dos grupos del mismo largo
         dejaban el del frame literal en el regex y la secuencia no
         matcheaba ni un archivo-; el desempate de homonimos termina en
         un hash del origen y no en un range acotado que, agotado,
         devolvia el mismo destino sin registrarlo y perdia archivos en
         silencio; una sub-ruta vacia -un knob que apunta a la raiz de
         una location- toma el ultimo segmento del origen; y deshacer()
         revierte la reescritura de knobs cuando el Save As falla.
_______________________________________________________________________

"""

import hashlib
import os
import re

# LGA_NodeFiles importa nuke de forma perezosa, adentro de las funciones que lo
# necesitan, asi que traerlo aca no ata este modulo al host.
import LGA_NodeFiles as node_files


# ---------------------------------------------------------------------------
#                                  Buckets
# ---------------------------------------------------------------------------
# Donde cae cada archivo adentro de la carpeta de collect. Los cuatro primeros
# salen de las scan locations configuradas y llevan su nombre en minuscula.
BUCKET_SHOT = "shot"
BUCKET_OUTSIDE = "outside"

# Que se hace con cada entrada del inventario.
ACTION_COPY = "copy"  # se copia el archivo y se reapunta el knob
ACTION_MKDIR = "mkdir"  # se crea la carpeta vacia y se reapunta el knob
ACTION_REPOINT = "repoint"  # no se copia nada; solo se reapunta el knob
ACTION_SKIP = "skip"  # no se toca (expresiones TCL, rutas vacias)

# Por que se salteo una entrada
SKIP_EXPRESSION = "expression"
SKIP_EMPTY = "empty"

# Hasta cuantos segmentos de la ruta de origen se espejan en outside/ para
# desempatar dos archivos que se llaman igual. Mas que esto y en Windows se
# empieza a rozar el limite de 260 caracteres de ruta.
MAX_SEGMENTOS_DESEMPATE = 4


def normalizar(ruta):
    """Barras hacia adelante y minusculas, para comparar rutas."""
    return (ruta or "").replace("\\", "/").rstrip("/").lower()


def con_barras(ruta):
    """Barras hacia adelante, sin tocar mayusculas."""
    return (ruta or "").replace("\\", "/")


def es_secuencia(ruta):
    """True si la ruta tiene un token de frame."""
    return bool(re.search(r"%0\d+d", ruta or "")) or "#" in (ruta or "")


def a_almohadillas(ruta):
    """Convierte "%04d" en "####". El resto queda igual."""
    return re.sub(r"%0(\d+)d", lambda m: "#" * int(m.group(1)), ruta or "")


def dentro_de(ruta, carpeta):
    """True si `ruta` esta adentro de `carpeta` (o es la carpeta misma)."""
    a = normalizar(ruta)
    b = normalizar(carpeta)
    if not a or not b:
        return False
    return a == b or a.startswith(b + "/")


def relativo_a(ruta, carpeta):
    """El tramo de `ruta` que cuelga de `carpeta`, con barras hacia adelante."""
    a = con_barras(ruta)
    largo = len(normalizar(carpeta))
    resto = a[largo:].lstrip("/")
    return resto


def nombre_de_bucket(nombre_location):
    """"Prerenders" -> "prerenders"; "Mi Carpeta" -> "mi_carpeta"."""
    limpio = re.sub(r"[^A-Za-z0-9]+", "_", (nombre_location or "").strip())
    return limpio.strip("_").lower() or "location"


# ---------------------------------------------------------------------------
#                        La estructura del shot a reproducir
# ---------------------------------------------------------------------------
def relativo_seguro(ruta, base):
    """
    La ruta relativa de `ruta` dentro de `base`, o None si no cuelga de ahi.

    NO usa os.path.relpath. relpath contesta siempre algo: con una carpeta que
    no cuelga de la base devuelve una ruta con ".." -que adentro del destino se
    escapa de la carpeta que el usuario eligio- y entre dos unidades distintas
    lanza ValueError, que en Windows es una configuracion valida y comun (una
    location apuntando a una biblioteca compartida en otro servidor).
    """
    if not dentro_de(ruta, base):
        return None
    return relativo_a(con_barras(ruta), base)


class Estructura(object):
    """
    Como se reproduce el shot adentro del destino.

    Collect deja de inventar carpetas por nombre de location y reproduce la
    estructura REAL que definen los Settings: si el shot tiene el .nk en
    "Comp/1_projects" y las locations en "_input" y "Comp/2_prerenders", el
    destino queda igual. Esa es la unica forma de que abrir el .nk colectado y
    correr el Media Manager resuelva adentro del collect: el shot folder y las
    locations se escriben RELATIVAS al .nk, asi que si el .nk no queda en la
    misma posicion relativa, resuelven al shot viejo.

    `reproducible` es False cuando no hay estructura que copiar -shot apagado,
    shot que no resuelve, o un .nk que no cuelga del shot-. Ahi se cae al
    esquema viejo de buckets por nombre, que no es tan bueno pero es predecible.
    """

    __slots__ = (
        "reproducible",
        "shot_dir",
        "nombre_shot",
        "rel_nk",
        "internas",
        "rel_externos",
        "nombre_externos",
        "motivo",
    )

    def __init__(self, reproducible, shot_dir="", nombre_shot="", rel_nk="",
                 internas=None, rel_externos="", nombre_externos="", motivo=""):
        self.reproducible = reproducible
        self.shot_dir = con_barras(shot_dir).rstrip("/")
        self.nombre_shot = nombre_shot
        self.rel_nk = rel_nk
        self.nombre_externos = nombre_externos
        # [(nombre, carpeta_absoluta, ruta_relativa_al_shot)] de las locations
        # que SI cuelgan del shot, ordenadas de mas especifica a menos.
        self.internas = internas or []
        # Donde caen los archivos que viven fuera del shot, relativo al shot.
        self.rel_externos = rel_externos
        # Por que no es reproducible, para poder decirlo.
        self.motivo = motivo


# Carpeta para lo de afuera cuando no hay ninguna location que pueda recibirlo.
CARPETA_EXTERNOS = "_outside"


def _location_para_externos(internas):
    """
    Que location recibe lo que vive fuera del shot.

    Primero la que se llame "input", que es la decision del usuario. Si no hay
    ninguna con ese nombre, la primera de la lista. Si no hay ninguna location
    adentro del shot, una carpeta propia en la raiz.

    El criterio depende de un NOMBRE que el usuario puede cambiar, asi que la
    location elegida se muestra en el cartel de confirmacion: que el destino de
    un archivo dependa de como se llama una fila de los ajustes es aceptable
    solo si el usuario lo ve antes de aceptar, no despues en el log.
    """
    for nombre, _carpeta, rel in internas:
        if nombre_de_bucket(nombre) == "input":
            return rel, nombre
    if internas:
        return internas[0][2], internas[0][0]
    return CARPETA_EXTERNOS, ""


def analizar_estructura(shot_dir, nk_dir, locations):
    """
    Que se puede reproducir del shot. Devuelve una Estructura.

    No toca disco: trabaja sobre rutas ya resueltas por quien llama.
    """
    if not shot_dir:
        return Estructura(False, motivo="the shot folder is turned off")

    nombre_shot = os.path.basename(con_barras(shot_dir).rstrip("/"))
    if not nombre_shot:
        # La raiz de una unidad o de un UNC no tiene nombre. Sin nombre no hay
        # carpeta de shot que crear, y todo caeria suelto en la carpeta elegida.
        return Estructura(False, motivo="the shot folder has no name")

    rel_nk = relativo_seguro(nk_dir, shot_dir)
    if rel_nk is None:
        # El shot puede configurarse con una ruta absoluta a cualquier lado, y
        # ahi el .nk no cuelga de el.
        return Estructura(False, motivo="the script is not inside the shot folder")

    internas = []
    for nombre, carpeta in locations or ():
        if not carpeta:
            continue
        rel = relativo_seguro(carpeta, shot_dir)
        if rel is None:
            # Una location afuera del shot no tiene lugar en la estructura: lo
            # que viva ahi se trata como material externo.
            continue
        internas.append((nombre, con_barras(carpeta), rel))

    # La location que recibe lo de afuera se elige ANTES de ordenar, o sea en
    # el orden de la tabla de ajustes. Eligiendola despues salia la mas
    # ESPECIFICA, que no es un criterio que el usuario pueda predecir: con
    # locations "Plates" y "Assets", lo de afuera caia en Assets solo porque su
    # ruta es mas larga.
    rel_externos, nombre_externos = _location_para_externos(internas)

    # Recien ahora, de mas especifica a menos: para el matching, una location
    # adentro de otra tiene que ganar.
    internas.sort(key=lambda t: len(normalizar(t[1])), reverse=True)
    return Estructura(
        True,
        shot_dir=shot_dir,
        nombre_shot=nombre_shot,
        rel_nk=rel_nk,
        internas=internas,
        rel_externos=rel_externos,
        nombre_externos=nombre_externos,
    )


def raiz_de_collect(elegida, nombre_shot):
    """
    La raiz del shot nuevo a partir de la carpeta que eligio el usuario.

    El usuario elige la carpeta CONTENEDORA y aca se le cuelga la del shot. Si
    la que eligio ya se llama como el shot, se usa tal cual: asi elegir la
    carpeta que ya preparo no le anida una igual adentro.
    """
    elegida = con_barras(elegida).rstrip("/")
    if not nombre_shot:
        return elegida
    if os.path.basename(elegida).lower() == nombre_shot.lower():
        return elegida
    return _juntar(elegida, nombre_shot)


def destino_del_script(raiz, estructura, nombre_nk):
    """Donde queda el .nk colectado."""
    if estructura.reproducible:
        return _juntar(raiz, estructura.rel_nk, nombre_nk)
    return _juntar(raiz, nombre_nk)


def relativa_entre(rel_desde, rel_hasta):
    """
    La ruta de `rel_hasta` vista desde `rel_desde`. Las dos cuelgan de la raiz.

    Es lo que se escribe en el knob, y NO es lo mismo que la ruta relativa a la
    raiz del collect: el .nk no queda en la raiz sino en su posicion del shot
    -"Comp/1_projects"-, asi que un archivo en "_input/plate.mov" se escribe
    "../../_input/plate.mov".

    Se cancela el prefijo comun para que la ruta quede como la escribiria una
    persona: desde "Comp/1_projects" hasta "Comp/2_prerenders/x.exr" da
    "../2_prerenders/x.exr" y no "../../Comp/2_prerenders/x.exr". Las dos
    resuelven al mismo lado, pero la corta es la que ya tiene el script
    original y la que el usuario espera leer.

    No usa os.path.relpath a proposito: en Windows devuelve barras invertidas
    y aca la salida va a un knob de Nuke, que las quiere hacia adelante.
    """
    desde = [p for p in con_barras(rel_desde).strip("/").split("/") if p]
    hasta = [p for p in con_barras(rel_hasta).strip("/").split("/") if p]

    comun = 0
    for a, b in zip(desde, hasta):
        if a.lower() != b.lower():
            break
        comun += 1

    subidas = [".."] * (len(desde) - comun)
    return "/".join(subidas + hasta[comun:]) or "."


# ---------------------------------------------------------------------------
#                          A que bucket va cada ruta
# ---------------------------------------------------------------------------
def clasificar_en_estructura(ruta, estructura):
    """
    Donde cae una ruta absoluta dentro del shot reproducido.

    Devuelve la sub-ruta relativa a la raiz del collect. Tres casos:

      1. Adentro de una scan location que cuelga del shot -> la MISMA ruta que
         tiene hoy relativa al shot. No un bucket con el nombre de la location:
         la ruta real, para que las locations del script colectado resuelvan.
      2. Adentro del shot pero fuera de toda location -> su ruta relativa al
         shot, igual.
      3. Afuera del shot -> adentro de la location de externos, conservando la
         carpeta que lo contenia para no perder de donde salio.

    El desempate de homonimos NO se hace aca: lo hace armar_plan para TODOS los
    casos por igual, con _sin_colision. Meter una formula fija de un solo
    segmento aca -como decia el borrador de esta propuesta- reintroduce el
    modo de fallo que el desempate existe para evitar: dos archivos distintos
    al mismo destino, uno pisa al otro, y el resumen dice que salio todo bien.
    """
    ruta = con_barras(ruta)

    # 1. Adentro de una location del shot: su ruta real, relativa al shot.
    for _nombre, carpeta, rel in estructura.internas:
        if dentro_de(ruta, carpeta):
            return _juntar(rel, relativo_a(ruta, carpeta))

    # 2. Adentro del shot, fuera de toda location: su ruta relativa al shot.
    rel_al_shot = relativo_seguro(ruta, estructura.shot_dir)
    if rel_al_shot is not None:
        return rel_al_shot

    # 3. Afuera del shot: a la location de externos, con la carpeta que lo
    # contenia para no perder de donde salio.
    carpeta_padre = os.path.basename(os.path.dirname(ruta.rstrip("/")))
    nombre = os.path.basename(ruta.rstrip("/"))
    return _juntar(estructura.rel_externos, carpeta_padre, nombre)


def clasificar(ruta, locations, shot_dir):
    """
    Decide bucket y sub-ruta de una ruta absoluta.

    `locations` es [(nombre, ruta_absoluta_resuelta)] de las scan locations.
    Devuelve (bucket, subruta), donde subruta es lo que cuelga adentro del
    bucket. Tres casos, en este orden:

      1. Adentro de una scan location  -> bucket con el nombre de la location,
         conservando la estructura que tenga adentro. Se elige la location MAS
         ESPECIFICA: prerenders vive adentro del shot, y si se resolviera al
         reves todo caeria en el shot.
      2. Adentro del shot pero fuera de toda location -> bucket "shot",
         espejando la ruta relativa al shot.
      3. Afuera del shot -> bucket "outside", con la carpeta que lo contiene
         para no perder de donde salio.
    """
    ruta = con_barras(ruta)

    candidatas = [
        (nombre, carpeta)
        for nombre, carpeta in (locations or [])
        if carpeta and dentro_de(ruta, carpeta)
    ]
    if candidatas:
        # La mas especifica es la de ruta mas larga.
        candidatas.sort(key=lambda par: len(normalizar(par[1])), reverse=True)
        nombre, carpeta = candidatas[0]
        return nombre_de_bucket(nombre), relativo_a(ruta, carpeta)

    if shot_dir and dentro_de(ruta, shot_dir):
        return BUCKET_SHOT, relativo_a(ruta, shot_dir)

    # Afuera: la carpeta contenedora alcanza para no perder el contexto y no
    # hace crecer la ruta como espejar el arbol entero.
    carpeta_padre = os.path.basename(os.path.dirname(ruta.rstrip("/")))
    nombre = os.path.basename(ruta.rstrip("/"))
    if carpeta_padre:
        return BUCKET_OUTSIDE, "%s/%s" % (carpeta_padre, nombre)
    return BUCKET_OUTSIDE, nombre


def segmentos_de_origen(ruta, cantidad):
    """Los ultimos `cantidad` segmentos de la ruta, para desempatar en outside."""
    partes = [p for p in con_barras(ruta).split("/") if p and not p.endswith(":")]
    if cantidad >= len(partes):
        return "/".join(partes)
    return "/".join(partes[-cantidad:])


# ---------------------------------------------------------------------------
#                                  El plan
# ---------------------------------------------------------------------------
def _juntar(*tramos):
    """
    Pega tramos de ruta con una sola barra, respetando el prefijo UNC.

    No se puede colapsar las barras con un re.sub global: un destino en
    "//servidor/share" perderia la doble barra del principio y dejaria de
    resolver.
    """
    partes = [con_barras(t).strip("/") for t in tramos]
    prefijo = ""
    primero = con_barras(tramos[0]) if tramos else ""
    if primero.startswith("//"):
        prefijo = "//"
    return prefijo + "/".join(p for p in partes if p)


# Que puede pasar con el destino elegido.
DESTINO_OK = "ok"
DESTINO_PISA_SCRIPT = "pisa_script"  # bloquea: el Save As pisaria el original
DESTINO_EN_EL_SHOT = "en_el_shot"  # solo avisa


def _mismo_archivo(a, b):
    """
    Si dos rutas son el MISMO lugar en disco.

    Compara el texto normalizado y, cuando las dos existen, tambien le
    pregunta al sistema: dos letras de unidad mapeadas al mismo servidor, o un
    symlink, son el mismo archivo con dos nombres distintos, y la comparacion
    de texto no lo ve. Si la de destino todavia no existe -el caso normal- solo
    queda el texto, y se declara: no es una garantia total.
    """
    if normalizar(a) == normalizar(b):
        return True
    try:
        if os.path.exists(a) and os.path.exists(b):
            return os.path.samefile(a, b)
    except OSError:
        pass
    return False


def _dentro_de_real(ruta, carpeta):
    """
    Como dentro_de, pero resolviendo antes los alias del sistema de archivos.

    La comparacion de texto sola no ve que una letra de unidad mapeada -un
    `subst K: <shot>`, una unidad de red, un symlink- es el mismo lugar con
    otro nombre: elegir "K:/" como destino se lleva el shot adentro de si
    mismo y no salta ni el aviso, porque "k:/..." no empieza con "n:/...".
    realpath lo desarma en Windows y en macOS.
    """
    if dentro_de(ruta, carpeta):
        return True
    try:
        return dentro_de(os.path.realpath(ruta), os.path.realpath(carpeta))
    except OSError:
        return False


def revisar_destino(raiz, destino_nk, nk_actual, shot_dir):
    """
    Si el destino elegido sirve. Devuelve (veredicto, dato).

    Collect COPIA, no mueve, asi que casi cualquier carpeta sirve, incluida una
    adentro del shot. Hubo un guard que prohibia el shot ENTERO y estaba mal
    calibrado: rechazaba un "Comp/collect" recien creado sin ningun riesgo.

    Ahora que el destino reproduce la estructura del shot, elegir la carpeta
    donde vive el .nk tampoco es peligroso: el script colectado aterriza dos
    niveles mas abajo, adentro de la carpeta con el nombre del shot.

    Lo unico que DESTRUYE algo es que el .nk colectado caiga exactamente sobre
    el original, que pasa al elegir la raiz del shot actual -se llama como el
    shot, asi que no se anida, y la estructura se reproduce encima-. Se compara
    la ruta final del script, que es la condicion exacta, y no la carpeta.

    Reproducir el shot ADENTRO del shot vivo no rompe nada pero deja una copia
    entera del plano colgando de el, que el proximo escaneo va a listar. Se
    avisa y se deja seguir.
    """
    if destino_nk and nk_actual and _mismo_archivo(destino_nk, nk_actual):
        return DESTINO_PISA_SCRIPT, None
    if shot_dir and _dentro_de_real(raiz, shot_dir):
        return DESTINO_EN_EL_SHOT, shot_dir
    return DESTINO_OK, None


def accion_para(entrada, incluir_workdir):
    """
    Que se hace con esta entrada del inventario.

    - Una expresion TCL no se toca NUNCA. Y esta bien que no se toque: una
      expresion armada sobre nuke.script_directory() sigue sola al script
      cuando se lo mueve, que es exactamente lo que un collect necesita.
    - La salida de un Write se reapunta pero no se copia: el render todavia
      puede no existir, y si existe no es material que el comp necesite.
    - La carpeta de trabajo de un CopyCat se recrea vacia. Adentro viven los
      contact sheets .png del entrenamiento y los checkpoints alternativos:
      historia del proceso, no material del comp. El checkpoint que el nodo
      USA es otra entrada, con rol input, y ese si se copia.
    - Un recurso de pipeline (rol tooling: el kernel de un BlinkScript) SI se
      copia, aunque Paths to Relative lo deje destildado. Son dos preguntas
      distintas: ahi se decide si conviene relativizarlo, y aca si el collect
      puede prescindir de el. No puede: sin el kernel el nodo no compila.
    """
    if not entrada.get("path"):
        return ACTION_SKIP, SKIP_EMPTY
    if entrada.get("is_expression"):
        return ACTION_SKIP, SKIP_EXPRESSION
    if entrada.get("is_folder"):
        return (ACTION_COPY if incluir_workdir else ACTION_MKDIR), ""
    if entrada.get("role") == node_files.ROLE_OUTPUT:
        return ACTION_REPOINT, ""
    return ACTION_COPY, ""


def armar_plan(entradas, destino, locations, shot_dir, incluir_workdir=False,
               estructura=None):
    """
    El plan completo del collect.

    `entradas` son dicts del inventario con al menos: node_name, node_class,
    knob, role, is_folder, is_expression y path (absoluta, ya resuelta).
    `destino` es la RAIZ del shot nuevo, o sea donde se reproduce la estructura.

    Con `estructura` reproducible, cada archivo va a la ruta REAL que tiene hoy
    relativa al shot, y el resultado es un shot de verdad: abrir el .nk
    colectado y correr el Media Manager resuelve adentro del collect. Sin ella
    se cae al esquema viejo de buckets por nombre de location.

    Devuelve (plan, salteadas):
      plan       una entrada por knob, con bucket, destino absoluto, ruta
                 relativa a escribir en el knob, y accion
      salteadas  [(entrada, motivo)] de lo que no se toca

    Las colisiones -dos origenes distintos que caen en el mismo destino- se
    resuelven aca adentro, IGUAL para todos los casos: alargando la sub-ruta
    con mas segmentos del origen y, si no alcanza, con un hash. Dos archivos
    que se llaman igual y se pisan en silencio es el peor modo de fallar de un
    collect: el script queda apuntando a un archivo que no es el suyo y nadie
    se entera.
    """
    destino = con_barras(destino).rstrip("/")
    plan = []
    salteadas = []
    ocupados = {}
    reproducible = estructura is not None and estructura.reproducible

    for entrada in entradas or []:
        accion, motivo = accion_para(entrada, incluir_workdir)
        if accion == ACTION_SKIP:
            salteadas.append((entrada, motivo))
            continue

        ruta = con_barras(entrada["path"])
        if reproducible:
            # Sin bucket: la sub-ruta YA es la ruta relativa a la raiz. El
            # desempate se hace igual, con un bucket unico, asi que dos
            # archivos distintos nunca comparten destino.
            bucket = ""
            subruta = clasificar_en_estructura(ruta, estructura)
        else:
            bucket, subruta = clasificar(ruta, locations, shot_dir)
        # La barra final del origen no viaja en la sub-ruta: se decide una sola
        # vez mas abajo, y si no se saca aca queda duplicada ("CopyCat//").
        subruta = (subruta or "").strip("/")
        # La sub-ruta queda vacia cuando el knob apunta EXACTAMENTE a la raiz
        # de una location. Sin nombre, el destino seria la carpeta del bucket y
        # el knob quedaria escrito como "input" a secas. Se usa el ultimo
        # segmento del origen, que es el nombre que tenia.
        if not subruta:
            subruta = os.path.basename(ruta.rstrip("/"))
        subruta = _sin_colision(bucket, subruta, ruta, ocupados)

        destino_abs = _juntar(destino, bucket, subruta)
        # La ruta del knob es relativa a la carpeta del .nk, que con estructura
        # reproducible NO es la raiz del collect sino su posicion del shot.
        rel_nk = estructura.rel_nk if reproducible else ""
        relativa = relativa_entre(rel_nk, _juntar("", bucket, subruta))
        # Un knob de carpeta se guarda con la barra final que tenia.
        if entrada.get("is_folder") and ruta.endswith("/"):
            relativa += "/"
            destino_abs += "/"

        item = dict(entrada)
        item.update(
            {
                "bucket": bucket,
                "subruta": subruta,
                "destino": destino_abs,
                "relativa": relativa,
                "accion": accion,
                "is_sequence": es_secuencia(ruta),
            }
        )
        plan.append(item)

    return plan, salteadas


def _sin_colision(bucket, subruta, origen, ocupados):
    """
    Devuelve una sub-ruta que todavia no este tomada dentro del bucket.

    Primero alarga la sub-ruta con mas segmentos del origen -que ademas dice
    de donde salio-; si aun asi choca, numera la carpeta contenedora.
    """
    clave = (bucket, normalizar(subruta))
    if ocupados.get(clave) in (None, normalizar(origen)):
        ocupados[clave] = normalizar(origen)
        return subruta

    for cantidad in range(3, MAX_SEGMENTOS_DESEMPATE + 1):
        candidata = segmentos_de_origen(origen, cantidad)
        clave = (bucket, normalizar(candidata))
        if ocupados.get(clave) in (None, normalizar(origen)):
            ocupados[clave] = normalizar(origen)
            return candidata

    # Ultimo recurso: un hash corto del origen, que es UNICO por definicion.
    # Antes se numeraba la carpeta con un range acotado y, agotado, se devolvia
    # la sub-ruta original SIN registrarla: dos origenes distintos terminaban
    # en el mismo destino, uno solo se copiaba, y el otro no aparecia ni entre
    # los errores ni entre los que no tenian archivo. O sea, un archivo que se
    # perdia y un resumen que decia que salio todo bien.
    base = segmentos_de_origen(origen, MAX_SEGMENTOS_DESEMPATE)
    carpeta, _, nombre = base.rpartition("/")
    marca = hashlib.sha1(normalizar(origen).encode("utf-8")).hexdigest()[:8]
    candidata = "%s_%s/%s" % (carpeta, marca, nombre) if carpeta else "%s_%s" % (marca, nombre)
    ocupados[(bucket, normalizar(candidata))] = normalizar(origen)
    return candidata


# ---------------------------------------------------------------------------
#                        De la ruta del knob a los archivos
# ---------------------------------------------------------------------------
# Estas DOS tocan disco. Van en un worker, nunca en el hilo principal: listar
# una secuencia larga contra un servidor congela la ventana.
#
# No se reusa expand_sequence() de LGA_MediaManager_utils porque esa parte del
# texto de la TABLA -"nombre.####.exr[1001-1129]"- y necesita el rango escrito.
# Aca se parte del valor del KNOB, que trae "%04d" y ningun rango: los frames
# hay que ir a buscarlos al disco.


def _regex_de_secuencia(nombre):
    """
    Un regex que casa los frames de un nombre con "%0Nd" o "####".

    El token del frame es el ULTIMO, no el primero: un nombre puede traer una
    version escrita "sh010_v###_####.exr". Y se sustituye POR POSICION, no con
    str.replace: con dos grupos del MISMO largo -"sh010_v####_####.exr"-
    replace ataca el de la izquierda y deja el del frame como literal en el
    regex, con lo cual la secuencia entera no matcheaba ni un archivo y el
    collect la daba por inexistente en disco.
    """
    marcas = list(re.finditer(r"%0(\d+)d", nombre))
    if marcas:
        ultima = marcas[-1]
        digitos = int(ultima.group(1))
    else:
        marcas = list(re.finditer(r"#+", nombre))
        if not marcas:
            return None
        ultima = marcas[-1]
        digitos = len(ultima.group(0))

    izquierda = re.escape(nombre[: ultima.start()])
    derecha = re.escape(nombre[ultima.end():])
    # Padding flexible: Nuke escribe "%04d" pero en disco puede haber frames de
    # cinco digitos una vez pasado el 99999.
    patron = izquierda + (r"(-?\d{%d,})" % digitos) + derecha
    return re.compile("^" + patron + "$", re.IGNORECASE)


def archivos_de_secuencia(ruta, listar=None):
    """
    Los archivos que existen en disco para una ruta con token de frame.

    `listar` es os.listdir; se puede inyectar para probar sin disco.
    """
    listar = listar or os.listdir
    ruta = con_barras(ruta)
    carpeta, _, nombre = ruta.rpartition("/")
    expresion = _regex_de_secuencia(nombre)
    if expresion is None or not carpeta:
        return []
    try:
        candidatos = listar(carpeta)
    except OSError:
        return []
    return sorted(
        "%s/%s" % (carpeta, archivo)
        for archivo in candidatos
        if expresion.match(archivo)
    )


def archivos_de(item, listar=None, caminar=None):
    """
    Los archivos REALES que hay que copiar para un item del plan.

    Devuelve [(origen, destino)]. Vacio si no hay nada que copiar, que es el
    caso de las acciones mkdir y repoint.
    """
    if item.get("accion") != ACTION_COPY:
        return []

    origen = con_barras(item["path"])
    destino = con_barras(item["destino"])

    if item.get("is_folder"):
        caminar = caminar or os.walk
        pares = []
        base = origen.rstrip("/")
        for raiz, _carpetas, archivos in caminar(base):
            raiz_rel = relativo_a(con_barras(raiz), base)
            for archivo in archivos:
                pares.append(
                    (
                        _juntar(con_barras(raiz), archivo),
                        _juntar(destino.rstrip("/"), raiz_rel, archivo),
                    )
                )
        return pares

    if item.get("is_sequence"):
        carpeta_destino = destino.rpartition("/")[0]
        return [
            (archivo, _juntar(carpeta_destino, archivo.rpartition("/")[2]))
            for archivo in archivos_de_secuencia(origen, listar=listar)
        ]

    return [(origen, destino)]


# ---------------------------------------------------------------------------
#                              Lo que se informa
# ---------------------------------------------------------------------------
def buckets_del_plan(plan):
    """{bucket: cantidad de knobs} para el resumen. Sin buckets vacios."""
    cuentas = {}
    for item in plan or []:
        cuentas[item["bucket"]] = cuentas.get(item["bucket"], 0) + 1
    return cuentas


def carpetas_a_crear(plan, raiz="", estructura=None):
    """
    Las carpetas del destino que hay que crear, ordenadas y sin repetir.

    Con estructura reproducible se crea ademas el ESQUELETO del shot: la
    carpeta del .nk y TODAS las scan locations, tengan contenido o no. Medido
    de punta a punta: sin eso, una location vacia -Assets y Publish en el shot
    de prueba- simplemente no existe en el destino, y desde el script colectado
    resuelve a cero carpetas. El collect dejaba de ser un shot valido apenas
    alguna location no tuviera archivos, que es el caso normal.

    Son carpetas vacias, si: pero son las carpetas PROPIAS del shot, no buckets
    inventados. Un shot al que le faltan sus carpetas no es un shot.
    """
    carpetas = set()
    for item in plan or []:
        if item["accion"] == ACTION_MKDIR:
            carpetas.add(item["destino"].rstrip("/"))
        else:
            carpetas.add(os.path.dirname(item["destino"].rstrip("/")))

    if raiz and estructura is not None and estructura.reproducible:
        carpetas.add(_juntar(raiz, estructura.rel_nk))
        for _nombre, _abs, rel in estructura.internas:
            carpetas.add(_juntar(raiz, rel))

    return sorted(c for c in carpetas if c)


def a_copiar(plan):
    """Los items cuyo archivo hay que copiar de verdad."""
    return [item for item in plan or [] if item["accion"] == ACTION_COPY]


def a_reapuntar(plan):
    """
    Los items cuyo knob hay que reescribir: todos menos los salteados.

    Incluye los de accion repoint -los Write, que no se copian pero si tienen
    que apuntar adentro del collect- y los de mkdir.
    """
    return [
        item
        for item in plan or []
        if item["accion"] in (ACTION_COPY, ACTION_MKDIR, ACTION_REPOINT)
    ]


# ---------------------------------------------------------------------------
#                         La capa que si toca Nuke
# ---------------------------------------------------------------------------
# Todo lo de abajo importa nuke de forma perezosa y corre en el HILO PRINCIPAL.
# Qt no entra: los carteles y el progreso los pone el FileScanner.

PROJECT_DIRECTORY_EXPRESSION = "[python {nuke.script_directory()}]"


def inventario(anchor_dir):
    """
    El inventario del script con las rutas ya resueltas a absolutas.

    `anchor_dir` es contra que se resuelven las relativas: el
    root.project_directory evaluado si tiene valor, y si no la carpeta del .nk.
    Nuke resuelve los relativos contra ese knob y no contra la ubicacion del
    script, asi que pasarle la carpeta del .nk cuando el knob apunta a otro
    lado da rutas que no existen.

    Corre en el hilo principal. Devuelve datos, nunca objetos nodo.
    """
    import LGA_NodeFiles as nfiles

    entradas, _ = nfiles.collect_entries(prefer_selection=False)
    salida = []
    for entrada in entradas:
        valor = entrada["raw"]
        if valor and not entrada["is_expression"]:
            valor = nfiles.resolve_against(valor, anchor_dir)
        salida.append(
            {
                "node": entrada["node"],
                "node_name": entrada["node_name"],
                "node_class": entrada["node_class"],
                "knob": entrada["knob"],
                "role": entrada["role"],
                "is_folder": entrada["is_folder"],
                "is_expression": entrada["is_expression"],
                "path": valor,
            }
        )
    return salida


def anchor_del_script():
    """
    Contra que resuelve Nuke las rutas relativas de ESTE script.

    Devuelve (anchor_dir, project_directory_vacio). Si el knob esta vacio,
    Nuke resuelve contra el working directory del proceso y los relativos no
    funcionan: el collect lo va a dejar apuntando al script, pero quien llama
    tiene que saber que estaba vacio para avisarlo.
    """
    import nuke

    ruta = nuke.root().name()
    carpeta_nk = os.path.dirname(ruta) if ruta else ""

    crudo = ""
    evaluado = ""
    try:
        knob = nuke.root()["project_directory"]
        crudo = (knob.getValue() or "").strip()
        if crudo:
            evaluado = (knob.evaluate() or "").strip()
    except Exception:
        pass

    evaluado = con_barras(evaluado).rstrip("/")
    if evaluado and os.path.isabs(evaluado):
        return evaluado, False
    return con_barras(carpeta_nk).rstrip("/"), not crudo


def crear_carpetas(carpetas):
    """
    Crea las carpetas del destino. Devuelve la lista de errores.

    Las de los archivos las crea sola la copia; esta funcion existe por las de
    accion mkdir -el dataDirectory de un CopyCat-, que no tienen ningun archivo
    que las traiga y quedarian sin crear.
    """
    errores = []
    for carpeta in carpetas or []:
        try:
            if carpeta and not os.path.isdir(carpeta):
                os.makedirs(carpeta, exist_ok=True)
        except OSError as problema:
            errores.append("%s: %s" % (carpeta, problema))
    return errores


def aplicar_rutas(plan, fijar_project_directory=True):
    """
    Escribe en cada knob su ruta relativa a la raiz del collect.

    Todo en UN bloque de undo, para que un Collect a medias se pueda deshacer
    de una. Devuelve (aplicadas, errores).

    El project_directory se deja en la expresion del script porque es lo que
    hace que los relativos resuelvan desde donde quede el .nk. Sin eso, las
    rutas que acabamos de escribir no encuentran nada.

    Corre en el hilo principal.
    """
    import nuke

    aplicadas = 0
    errores = []

    nuke.Undo().begin("Collect")
    try:
        if fijar_project_directory:
            try:
                nuke.root()["project_directory"].setValue(
                    PROJECT_DIRECTORY_EXPRESSION
                )
            except Exception as problema:
                errores.append("project_directory: %s" % problema)

        for item in a_reapuntar(plan):
            nodo = item.get("node")
            try:
                if nodo is None or nodo.knob(item["knob"]) is None:
                    errores.append(
                        "%s.%s: el knob ya no existe"
                        % (item["node_name"], item["knob"])
                    )
                    continue
                nodo[item["knob"]].setValue(item["relativa"])
                aplicadas += 1
            except Exception as problema:
                errores.append(
                    "%s.%s: %s" % (item["node_name"], item["knob"], problema)
                )
    finally:
        nuke.Undo().end()

    return aplicadas, errores


def deshacer():
    """
    Deshace el ultimo bloque de undo, que es el de aplicar_rutas.

    Existe por el fallo de Save As: si el guardado no sale, el script ABIERTO
    ya tiene todos sus knobs en relativo contra una carpeta donde nunca se
    guardo, asi que el project_directory evalua a la carpeta VIEJA y cada
    ruta relativa apunta a un lugar que no existe. O sea, el script del
    usuario queda offline entero por un fallo que no fue suyo. Es el mismo
    principio que la cancelacion: a medio camino, se vuelve.
    """
    import nuke

    try:
        nuke.Undo().undo()
        return True
    except Exception:
        return False


def guardar_como(ruta):
    """
    Guarda el script en la ruta dada. Devuelve (ruta, error).

    Recibe la ruta COMPLETA y no destino+nombre: desde que el collect
    reproduce la estructura del shot, el .nk no va en la raiz sino en su
    posicion -"Comp/1_projects"-, y esa cuenta ya la hizo destino_del_script.

    Va DESPUES de reescribir los knobs: si se guardara antes, el .nk del
    destino quedaria con las rutas viejas.
    """
    import nuke

    ruta = con_barras(ruta)
    try:
        nuke.scriptSaveAs(ruta, overwrite=1)
        return ruta, ""
    except Exception as problema:
        return "", str(problema)
