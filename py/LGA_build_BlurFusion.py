"""
_____________________________________________________________________________

  LGA_build_BlurFusion v1.00 | Lega

  Crea un Group "Blur-Fusion" que estima el color del frente en los bordes
  semitransparentes (pelo, motion blur) a partir del PLATE y un matte, sin
  fondo conocido. Implementa con nodos nativos de Nuke el estimador de
  "Approximate Fast Foreground Colour Estimation" (Marco Forte y Francois
  Pitie, ICIP 2021), con sus dos pasadas: caja grande y caja chica.

  Una pasada, con caja de ancho r (filtro box del Blur):
      F^ = blur(Fsrc * a) / (blur(a) + eps)            frente medio cercano
      B^ = blur(Bsrc * (1 - a)) / (blur(1 - a) + eps)  fondo medio cercano
      F  = F^ + a * (I - a * F^ - (1 - a) * B^)        correccion por mezcla
  Pasada 1: Fsrc = Bsrc = I, r = large size (90).
  Pasada 2: Fsrc = F de la pasada 1, Bsrc = B^ de la pasada 1, r = small
  size (6). La salida es el F de la pasada 2.

  Donde mas se ve esta version, y hay que moverla junto con el header:
    - El knob "version" del Group, leido de este header por _tool_version().
    - El titulo de la seccion "Blur-Fusion" de README.md y README_ES.md, a mano.

  v1.00: Primera version.
_____________________________________________________________________________

"""

import os
import re

import nuke

TOOL_NAME = "Blur-Fusion"

# Tooltips de los knobs. Van por esta capa y no escritos en cada knob para que
# el paso a bilingue sea un cambio de datos (ver LGA_tooltip_helper).
TOOLTIPS = {
    "large_size": (
        "Ancho en pixeles de la caja de la primera pasada. Define de que zona "
        "se toma el color medio del frente y del fondo alrededor del borde. "
        "El paper usa 90."
    ),
    "small_size": (
        "Ancho en pixeles de la caja de la segunda pasada, que refina el "
        "color cerca del borde usando el resultado de la primera. El paper "
        "usa 6."
    ),
    "premultiply": (
        "Prendido: la salida sale premultiplicada por el matte, lista para un "
        "Merge over. Apagado: sale el color del frente sin premultiplicar, con "
        "el matte en el alpha."
    ),
    "clamp_negative": (
        "Lleva a cero los valores negativos que puede dejar la correccion. "
        "No recorta arriba de 1: en lineal los brillos pasan de 1."
    ),
    "epsilon": (
        "Valor chico que se suma a los divisores para no dividir por cero "
        "donde el blur del matte (o de su inverso) da cero."
    ),
}


def _tool_version():
    """Version de la tool, leida del header de este archivo."""
    try:
        with open(os.path.abspath(__file__), "r", encoding="utf-8") as archivo:
            cabecera = archivo.read(2000)
        coincidencia = re.search(r"LGA_build_BlurFusion v(\d+\.\d+)", cabecera)
        if coincidencia:
            return coincidencia.group(1)
    except (OSError, UnicodeError):
        pass
    return "?"


# -----------------------------------------------------------------------------
#  Knobs del Group
# -----------------------------------------------------------------------------


def _add_knobs(group):
    group.addKnob(nuke.Tab_Knob("blur_fusion_tab", TOOL_NAME))

    info = nuke.Text_Knob(
        "info",
        "",
        "Foreground colour for soft edges (Forte & Pitie, ICIP 2021).\n"
        "Source: plate rgb.  Matte: alpha (if empty, Source alpha is used).",
    )
    group.addKnob(info)

    large = nuke.Double_Knob("large_size", "large size")
    large.setRange(1, 400)
    large.setValue(90)
    large.setTooltip(TOOLTIPS["large_size"])
    group.addKnob(large)

    small = nuke.Double_Knob("small_size", "small size")
    small.setRange(1, 50)
    small.setValue(6)
    small.setTooltip(TOOLTIPS["small_size"])
    group.addKnob(small)

    premult = nuke.Boolean_Knob("premultiply", "premultiply")
    premult.setValue(True)
    premult.setFlag(nuke.STARTLINE)
    premult.setTooltip(TOOLTIPS["premultiply"])
    group.addKnob(premult)

    group.addKnob(nuke.Text_Knob("advanced_divider", "advanced"))

    clamp = nuke.Boolean_Knob("clamp_negative", "clamp negatives")
    clamp.setValue(True)
    clamp.setFlag(nuke.STARTLINE)
    clamp.setTooltip(TOOLTIPS["clamp_negative"])
    group.addKnob(clamp)

    epsilon = nuke.Double_Knob("epsilon", "epsilon")
    epsilon.setRange(0, 0.001)
    epsilon.setValue(1e-5)
    epsilon.setTooltip(TOOLTIPS["epsilon"])
    group.addKnob(epsilon)

    group.addKnob(nuke.Text_Knob("version_divider", ""))
    group.addKnob(
        nuke.Text_Knob("version", "", "%s v%s | Lega" % (TOOL_NAME, _tool_version()))
    )


# -----------------------------------------------------------------------------
#  Grafo interno
# -----------------------------------------------------------------------------


def _expression(source, rgb, alpha, xpos, ypos, name):
    """Expression con la misma formula en r, g y b (con {c} = r, g o b).
    Por defecto expr0..expr3 escriben en red, green, blue y alpha."""
    node = nuke.nodes.Expression(inputs=[source], name=name, xpos=xpos, ypos=ypos)
    node["expr0"].setValue(rgb.format(c="r"))
    node["expr1"].setValue(rgb.format(c="g"))
    node["expr2"].setValue(rgb.format(c="b"))
    node["expr3"].setValue(alpha)
    return node


def _merge_expression(b_input, a_input, rgb, alpha, xpos, ypos, name):
    """MergeExpression: input 0 es B y input 1 es A, como en Nuke. Mismo
    reparto de canales por defecto que Expression."""
    node = nuke.nodes.MergeExpression(
        inputs=[b_input, a_input], name=name, xpos=xpos, ypos=ypos
    )
    node["expr0"].setValue(rgb.format(c="r"))
    node["expr1"].setValue(rgb.format(c="g"))
    node["expr2"].setValue(rgb.format(c="b"))
    node["expr3"].setValue(alpha)
    return node


def _crop_to_format(source, xpos, ypos, name):
    """Recorta al formato con negro afuera: el blur de un numerador y de su
    denominador ven ceros fuera del cuadro, asi que el promedio sigue
    normalizado en los bordes de la imagen."""
    node = nuke.nodes.Crop(inputs=[source], name=name, xpos=xpos, ypos=ypos)
    node["box"].setExpression("0", 0)
    node["box"].setExpression("0", 1)
    node["box"].setExpression("width", 2)
    node["box"].setExpression("height", 3)
    node["reformat"].setValue(False)
    node["crop"].setValue(True)
    return node


def _box_blur(source, size_knob, xpos, ypos, name):
    node = nuke.nodes.Blur(inputs=[source], name=name, xpos=xpos, ypos=ypos)
    node["channels"].setValue("rgba")
    node["filter"].setValue("box")
    node["size"].setExpression("parent.%s" % size_knob)
    # Con quality por debajo del tamano, Blur calcula a menor resolucion y la
    # caja deja de ser exacta: se fuerza a resolucion completa.
    node["quality"].setExpression("max(15, size + 1)")
    return node


def _local_mean(source, weight, size_knob, xpos, ypos, tag):
    """blur(src * w) / (blur(w) + eps). Sale con el promedio en rgb y blur(w)
    en alpha. `weight` es la expresion del peso en funcion del alpha (a)."""
    pesado = _expression(
        source, "{c}*(%s)" % weight, weight, xpos, ypos, "weight_%s" % tag
    )
    recorte = _crop_to_format(pesado, xpos, ypos + 40, "crop_%s" % tag)
    borroso = _box_blur(recorte, size_knob, xpos, ypos + 80, "blur_%s" % tag)
    return _expression(
        borroso, "{c}/(a+parent.epsilon)", "a", xpos, ypos + 120, "mean_%s" % tag
    )


def _pass(f_source, b_source, image, size_knob, xpos, ypos, tag):
    """Una pasada del estimador. Todas las entradas llevan el matte en alpha.
    Devuelve (F, B^): F en rgb con el matte en alpha; B^ en rgb."""
    f_mean = _local_mean(f_source, "a", size_knob, xpos, ypos, "F%s" % tag)
    b_mean = _local_mean(b_source, "1-a", size_knob, xpos + 150, ypos, "B%s" % tag)
    # R = I - (1 - a) * B^
    resto = _merge_expression(
        image, b_mean, "B{c}-(1-Ba)*A{c}", "Ba", xpos + 150, ypos + 180, "rest_%s" % tag
    )
    # F = F^ + a * (I - a * F^ - (1 - a) * B^) = F^ + a * (R - a * F^)
    frente = _merge_expression(
        resto,
        f_mean,
        "A{c}+Ba*(B{c}-Ba*A{c})",
        "Ba",
        xpos,
        ypos + 240,
        "fg_%s" % tag,
    )
    limpio = _expression(
        frente,
        "parent.clamp_negative ? max({c}, 0) : {c}",
        "a",
        xpos,
        ypos + 280,
        "clamp_%s" % tag,
    )
    return limpio, b_mean


def _build_internals():
    """Arma los nodos internos. Se llama con el Group abierto (begin)."""
    source = nuke.nodes.Input(name="Source", xpos=0, ypos=-300)
    matte = nuke.nodes.Input(name="Matte", xpos=300, ypos=-300)

    # Con el input Matte conectado, el alpha sale de ahi; si no, del Source.
    elegir = nuke.nodes.Switch(inputs=[source, matte], name="matte_or_source", xpos=300, ypos=-240)
    elegir["which"].setExpression("[exists parent.input1]")

    con_alpha = nuke.nodes.Copy(inputs=[source, elegir], name="copy_alpha", xpos=0, ypos=-240)
    con_alpha["from0"].setValue("rgba.alpha")
    con_alpha["to0"].setValue("rgba.alpha")

    # I en rgb y a = clamp(alpha, 0, 1) en alpha.
    imagen = _expression(
        con_alpha, "{c}", "clamp(a, 0, 1)", 0, -200, "image_and_matte"
    )
    imagen = _crop_to_format(imagen, 0, -160, "crop_image")

    # Pasada 1: Fsrc = Bsrc = I, caja grande.
    f1, b1 = _pass(imagen, imagen, imagen, "large_size", 0, -80, "1")

    # Pasada 2: Fsrc = F1, Bsrc = B^1 con el matte en alpha, caja chica.
    b1_alpha = nuke.nodes.Copy(inputs=[b1, imagen], name="bg1_with_matte", xpos=300, ypos=260)
    b1_alpha["from0"].setValue("rgba.alpha")
    b1_alpha["to0"].setValue("rgba.alpha")
    f2, _ = _pass(f1, b1_alpha, imagen, "small_size", 0, 320, "2")

    premult = nuke.nodes.Premult(inputs=[f2], name="premult", xpos=0, ypos=660)
    premult["disable"].setExpression("!parent.premultiply")
    final = _crop_to_format(premult, 0, 700, "crop_output")
    nuke.nodes.Output(inputs=[final], xpos=0, ypos=760)


def build_group():
    """Crea el Group Blur-Fusion en el contexto actual y lo devuelve."""
    group = nuke.nodes.Group(name="BlurFusion1")
    _add_knobs(group)
    group.begin()
    try:
        _build_internals()
    finally:
        group.end()
    return group


# -----------------------------------------------------------------------------
#  Entrada del menu
# -----------------------------------------------------------------------------


def _selected_node_or_none():
    try:
        from LGA_ToolPack_Selection import selected_node

        return selected_node()
    except ValueError:
        return None


def main():
    """Crea el Group colgado del nodo seleccionado (input Source)."""
    elegido = _selected_node_or_none()
    for nodo in nuke.selectedNodes():
        nodo.setSelected(False)

    group = build_group()
    if elegido is not None:
        group.setInput(0, elegido)
        group.setXYpos(
            elegido.xpos(), elegido.ypos() + elegido.screenHeight() + 40
        )
    else:
        centro = nuke.center()
        group.setXYpos(int(centro[0]), int(centro[1]))
    group.setSelected(True)
    return group
