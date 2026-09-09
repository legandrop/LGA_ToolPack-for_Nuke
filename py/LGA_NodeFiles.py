"""
____________________________________________________________________

  LGA_NodeFiles v1.00 | Lega

  Inventario unico de los knobs que guardan rutas de archivo en un
  script de Nuke. Contesta una sola pregunta -que knobs de que nodos
  apuntan a disco, y que es cada uno- para que las tools del pack no
  tengan cada una su propia lista de clases.

  El barrido NO enumera clases: toma todo nodo que tenga algun
  File_Knob. Enumerar clases es lo que dejaba afuera a CopyCat y a
  Inference, y se iba a volver a olvidar del siguiente nodo que saque
  Foundry. Lo unico que se enumera son los ROLES, que son cuatro casos
  y no una lista que haya que mantener completa.

  La mitad de politica (roles, carpetas, expresiones, relativos) no
  importa nuke y se prueba sin abrir el host; ver tests/.

  v1.00: Version inicial.
____________________________________________________________________
"""

import os
import re


# ---------------------------------------------------------------------------
#                                   Roles
# ---------------------------------------------------------------------------
# Que es cada ruta para el script, que es lo que decide que hace con ella la
# tool que consume el inventario:
#
#   input    el nodo LEE ese archivo. Sin el, el script no resuelve.
#   output   el nodo ESCRIBE ahi. El archivo puede no existir todavia.
#   workdir  carpeta de trabajo del nodo. No es un archivo y su contenido no
#            es material del comp: son subproductos del proceso.
#   tooling  recurso de pipeline, no media del shot: vive en una carpeta de
#            herramientas compartida y no viaja con el .nk. Se inventaria -un
#            collect tiene que llevarselo o el nodo no compila en la otra
#            punta- pero pasarlo a relativo casi nunca es lo que se quiere.
ROLE_INPUT = "input"
ROLE_OUTPUT = "output"
ROLE_WORKDIR = "workdir"
ROLE_TOOLING = "tooling"

# El rol de un knob cuando no esta en la tabla de abajo. La enorme mayoria de
# los File_Knob de Nuke son entradas, asi que ese es el default y la tabla
# lista unicamente las excepciones.
DEFAULT_ROLE = ROLE_INPUT

# (Clase, knob) -> rol. Solo las excepciones al default.
KNOB_ROLES = {
    # Los que escriben a disco
    ("Write", "file"): ROLE_OUTPUT,
    ("Write", "proxy"): ROLE_OUTPUT,
    ("DeepWrite", "file"): ROLE_OUTPUT,
    ("WriteGeo", "file"): ROLE_OUTPUT,
    ("ParticleCache", "file"): ROLE_OUTPUT,
    # Precomp tiene los dos: `file` es el .nk que lee, `output` es su render.
    ("Precomp", "output"): ROLE_OUTPUT,
    # CopyCat entrena adentro de dataDirectory: ahi van los checkpoints .cat y
    # los contact sheets .png de progreso. Es carpeta, y es del proceso, no del
    # comp. checkpointFile en cambio es una ENTRADA: el .cat desde el que el
    # nodo resume el entrenamiento.
    ("CopyCat", "dataDirectory"): ROLE_WORKDIR,
    ("CopyCat", "checkpointFile"): ROLE_INPUT,
    # El .cat que el Inference evalua para renderizar. Es la entrada que mas
    # importa de las tres y la que ninguna tool veia.
    ("Inference", "modelFile"): ROLE_INPUT,
    # El kernel de un BlinkScript es codigo de pipeline y suele vivir en una
    # carpeta de herramientas compartida, fuera del arbol del shot: pasarlo a
    # relativo da una ruta que solo sirve desde ESE shot.
    ("BlinkScript", "kernelSourceFile"): ROLE_TOOLING,
}

# Los knobs que apuntan a una CARPETA y no a un archivo. Todo lo que expanda
# secuencias, mida tamanos o copie frames tiene que preguntar esto antes.
FOLDER_KNOBS = frozenset(
    [
        ("CopyCat", "dataDirectory"),
    ]
)

# Nodos que se saltean enteros. Root queda afuera por no recorrerse nunca (el
# barrido arranca en root().nodes()), pero se nombra igual porque su
# project_directory ES un File_Knob y convertirlo a relativo rompe el script.
SKIP_CLASSES = frozenset(["Root"])

# Solo se baja adentro de los Group. Precomp y LiveGroup tambien contienen
# nodos, pero esos vienen de OTRO .nk: tocarlos aca no tiene efecto real, y el
# nodo contenedor ya aporta su propio knob.
RECURSE_CLASSES = frozenset(["Group"])


def role_for(node_class, knob_name):
    """Que es esta ruta para el script: input, output o workdir."""
    return KNOB_ROLES.get((node_class, knob_name), DEFAULT_ROLE)


def is_folder_knob(node_class, knob_name):
    """True si el knob apunta a una carpeta y no a un archivo."""
    return (node_class, knob_name) in FOLDER_KNOBS


# ---------------------------------------------------------------------------
#                            Helpers de rutas
# ---------------------------------------------------------------------------
# Unidad de Windows al principio del path (T:/ o T:\)
DRIVE_RE = re.compile(r"^[a-zA-Z]:[\\/]")


def is_expression_value(value):
    """
    True si el knob tiene una expresion TCL/Python en vez de una ruta literal.

    Los Writes creados con Write Presets caen aca y no se tocan nunca. Y esta
    bien que no se toquen: una expresion armada sobre nuke.script_directory()
    SIGUE sola al script cuando se lo mueve de carpeta, que es justo lo que se
    quiere de un relativo.
    """
    return "[" in value or "]" in value


def is_absolute_path(value):
    """
    True si la ruta es absoluta en cualquiera de las dos plataformas.

    No alcanza con os.path.isabs: el mismo script se abre en Mac y en Windows,
    asi que una ruta con unidad tiene que reconocerse corriendo en Mac.
    """
    if not value:
        return False
    if DRIVE_RE.match(value):
        return True
    if value.startswith("//") or value.startswith("\\\\"):
        return True
    return os.path.isabs(value)


def to_relative(path, anchor_dir):
    """
    Convierte una ruta absoluta en relativa al directorio ancla.

    Retorna (relative_path, up_levels). Si no existe ruta relativa posible
    (otra unidad o mount) retorna (None, 0).
    """
    try:
        relative = os.path.relpath(path, anchor_dir)
    except ValueError:
        return None, 0

    relative = relative.replace("\\", "/")

    up_levels = 0
    for part in relative.split("/"):
        if part == "..":
            up_levels += 1
        else:
            break

    return relative, up_levels


def resolve_against(path, anchor_dir):
    """
    Resuelve una ruta relativa contra el ancla. Las absolutas vuelven igual.

    El ancla de Nuke NO es la carpeta del .nk sino root.project_directory; el
    que llama decide cual pasa, pero tiene que pasar el que corresponda.
    """
    texto = (path or "").strip().replace("\\", "/")
    if not texto:
        return ""
    if is_absolute_path(texto):
        return os.path.normpath(texto).replace("\\", "/")
    if not anchor_dir:
        return texto
    unido = os.path.join(anchor_dir, texto)
    return os.path.normpath(unido).replace("\\", "/")


# ---------------------------------------------------------------------------
#                              Armado de entradas
# ---------------------------------------------------------------------------
def node_location(node):
    """Donde vive el nodo: "Root" o la ruta del Group que lo contiene."""
    try:
        full_name = node.fullName()
    except Exception:
        return "Root"
    if "." in full_name:
        return full_name.rsplit(".", 1)[0].replace(".", "/")
    return "Root"


def knob_raw_value(knob):
    """El texto crudo del knob, sin evaluar expresiones."""
    try:
        value = knob.getValue()
    except Exception:
        try:
            value = knob.value()
        except Exception:
            return ""
    return (value or "").strip()


_FILE_KNOB_CLASS = None


def _default_is_file_knob(knob):
    """
    El check real contra nuke. Los tests inyectan el suyo.

    La clase se cachea: esto corre una vez POR KNOB de todo el script, y con
    unos miles de knobs el import repetido se nota aunque sea solo una busqueda
    en el diccionario de modulos.
    """
    global _FILE_KNOB_CLASS
    if _FILE_KNOB_CLASS is None:
        import nuke

        _FILE_KNOB_CLASS = nuke.File_Knob
    return isinstance(knob, _FILE_KNOB_CLASS)


def reset_cache():
    """Suelta la clase cacheada. Lo usan los tests que stubbean nuke."""
    global _FILE_KNOB_CLASS
    _FILE_KNOB_CLASS = None


def file_knobs(node, is_file_knob=None):
    """Devuelve [(nombre, knob)] de todos los File_Knob del nodo, ordenados."""
    check = is_file_knob or _default_is_file_knob
    result = []
    try:
        knobs = node.knobs()
    except Exception:
        return result

    for knob_name, knob in knobs.items():
        try:
            if check(knob):
                result.append((knob_name, knob))
        except Exception:
            continue

    result.sort(key=lambda item: item[0])
    return result


def entries_from_nodes(nodes, is_file_knob=None):
    """
    Arma el inventario a partir de una lista de nodos ya juntada.

    Separada del barrido a proposito: recibe cualquier cosa que responda
    Class(), name(), fullName() y knobs(), asi que se prueba sin nuke.

    Cada entrada es un dict con:
        node        el objeto nodo, para escribirle despues
        node_name   nombre corto
        node_class  clase
        knob        nombre del knob
        raw         valor crudo, sin evaluar
        role        input / output / workdir
        is_folder   True si apunta a una carpeta
        is_expression  True si el valor es TCL/Python
        location    "Root" o el Group que lo contiene

    Las entradas vacias y las de expresion VIENEN INCLUIDAS, con su flag: el
    que consume decide si las cuenta, las muestra o las saltea. Filtrarlas
    aca dejaba a las tools sin poder decir por que algo no aparecia.
    """
    entries = []
    for node in nodes:
        try:
            node_class = node.Class()
        except Exception:
            continue
        if node_class in SKIP_CLASSES:
            continue
        try:
            node_name = node.name()
        except Exception:
            node_name = ""
        location = node_location(node)

        for knob_name, knob in file_knobs(node, is_file_knob):
            raw = knob_raw_value(knob)
            entries.append(
                {
                    "node": node,
                    "node_name": node_name,
                    "node_class": node_class,
                    "knob": knob_name,
                    "raw": raw.replace("\\", "/") if raw else "",
                    "role": role_for(node_class, knob_name),
                    "is_folder": is_folder_knob(node_class, knob_name),
                    "is_expression": is_expression_value(raw),
                    "location": location,
                }
            )
    return entries


# ---------------------------------------------------------------------------
#                                  Barrido
# ---------------------------------------------------------------------------
def walk_group(group, collected, visitados=None):
    """
    Recorre el grupo juntando nodos, y baja solo a los Group anidados.

    No se usa nuke.allNodes(recurseGroups=True) porque tambien baja a los
    Precomp y a los LiveGroup, cuyos nodos internos vienen de otro .nk.

    `visitados` corta los ciclos. La jerarquia de Nuke es un arbol y no puede
    tenerlos, pero sin la guarda un proveedor de nodos simulado -un test, un
    puente a otra herramienta- entra en recursion infinita y el RecursionError
    lo atrapa el except de abajo: el barrido se corta a la mitad y devuelve una
    lista incompleta SIN avisar, que es peor que reventar.
    """
    if visitados is None:
        visitados = set()
    # Se marca el grupo de entrada pero NO se corta por el: cuando se baja a un
    # Group ya se lo marco al agregarlo como hijo, y cortar aca dejaba sin
    # recorrer todo grupo anidado. El corte del ciclo lo hace el chequeo de los
    # hijos, mas abajo.
    visitados.add(id(group))

    try:
        children = group.nodes()
    except Exception:
        return

    for node in children:
        # El visto se marca al AGREGAR y no solo al bajar: cortando nada mas
        # la recursion, un nodo alcanzable por dos caminos entraba dos veces a
        # la lista y salia con dos filas.
        if id(node) in visitados:
            continue
        visitados.add(id(node))
        collected.append(node)
        try:
            node_class = node.Class()
        except Exception:
            continue
        if node_class in RECURSE_CLASSES:
            walk_group(node, collected, visitados)


def collect_nodes(prefer_selection=True):
    """
    Junta los nodos del script.

    Retorna (nodos, from_selection). Con seleccion y prefer_selection, trabaja
    solo sobre lo seleccionado -y baja a los Group seleccionados-; si no,
    recorre todo el script.
    """
    import nuke

    if prefer_selection:
        try:
            selected = list(nuke.selectedNodes())
        except Exception:
            selected = []
        if selected:
            collected = []
            for node in selected:
                collected.append(node)
                try:
                    if node.Class() in RECURSE_CLASSES:
                        walk_group(node, collected)
                except Exception:
                    continue
            return collected, True

    collected = []
    walk_group(nuke.root(), collected)
    return collected, False


def collect_entries(prefer_selection=True, roles=None):
    """
    El inventario completo del script.

    Retorna (entries, from_selection). Con `roles` se filtra por rol, por
    ejemplo roles=(ROLE_INPUT,) para quedarse solo con lo que el script LEE.

    Si hay seleccion pero NINGUNO de los nodos seleccionados aporta un knob de
    archivo -un Dot, un Backdrop, un Merge- se cae al script entero. Es el
    comportamiento que tenia la lista de clases y conviene conservarlo: quien
    dejo un Backdrop marcado no esta pidiendo que la tool no haga nada.
    """
    nodes, from_selection = collect_nodes(prefer_selection)
    entries = entries_from_nodes(nodes)

    if from_selection and not entries:
        nodes, from_selection = collect_nodes(prefer_selection=False)
        entries = entries_from_nodes(nodes)

    if roles:
        entries = [entry for entry in entries if entry["role"] in roles]
    return entries, from_selection


def usable_entries(entries):
    """Las entradas que apuntan a una ruta literal: sin vacias ni expresiones."""
    return [
        entry
        for entry in entries
        if entry["raw"] and not entry["is_expression"]
    ]
