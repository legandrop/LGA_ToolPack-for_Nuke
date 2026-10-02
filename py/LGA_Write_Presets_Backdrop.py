"""
____________________________________________________________________

  LGA_Write_Presets_Backdrop v2.81 | Lega

  Los backdrops que crea o pega Write Presets: que sean LGA_backdrop y
  que queden por encima de lo que ya hay en el Node Graph.

  to_lga_backdrop(node) -> node
      Le agrega a un BackdropNode comun los knobs de LGA_backdrop, en el
      mismo nodo: la misma pestana "backdrop" que arma LGA_BD_knobs de
      LGA_ToolPack-Layout (copia de su estructura). NO depende de que Layout
      este instalado: igual que un script con LGA_backdrops que se le pasa a
      alguien sin Layout, los knobs viajan como parte del nodo y quedan
      inertes hasta que haya un Layout que registre sus callbacks. Si Layout
      esta, se agregan con sus callbacks en pausa. Un LGA_backdrop queda
      como esta.

  raise_backdrops(backdrops)
      Z order de los backdrops recien creados o pegados, del mas grande al
      mas chico: uno mas que el mas alto de los backdrops que ya estaban y
      se le superponen, para que quede arriba. Si encierra entero a un
      backdrop que ya estaba, va uno menos que ese, para no taparlo
      (mismo criterio que autoBackdrop de Layout). Tambien sincroniza el
      slider zorder del LGA_backdrop.

  v2.80: Modulo nuevo.
____________________________________________________________________
"""

import nuke

# Knob que solo tiene un LGA_backdrop.
LGA_MARKER_KNOB = "lga_autofit_control"

# Margen del autofit con que nace un LGA_backdrop (default de Layout).
MARGIN_DEFAULT = 50

_logger = None


def set_logger(funcion):
    global _logger
    _logger = funcion


def debug_print(*message):
    if _logger:
        _logger(*message)


def is_lga_backdrop(node):
    return LGA_MARKER_KNOB in node.knobs()


def _suppress_layout_callbacks():
    """La pausa de callbacks de Layout si esta instalado; si no, nada."""
    try:
        import LGA_BD_callbacks

        return LGA_BD_callbacks.suppress_callbacks()
    except Exception:
        import contextlib

        return contextlib.nullcontext()


def _alignment_from_label(label):
    if label.startswith('<div align="center">'):
        return "center"
    if label.startswith('<div align="right">'):
        return "right"
    return "left"


def _text(name, text="", startline=True):
    knob = nuke.Text_Knob(name, "", text)
    if startline:
        knob.setFlag(nuke.STARTLINE)
    else:
        knob.clearFlag(nuke.STARTLINE)
    return knob


def _link(node, name, label, target, startline=False):
    """Link_Knob relativo al knob nativo: setLink va despues del addKnob."""
    knob = nuke.Link_Knob(name, label)
    if not startline:
        knob.clearFlag(nuke.STARTLINE)
    node.addKnob(knob)
    knob.setLink(target)


def _custom(name, widget):
    knob = nuke.PyCustom_Knob(name, "", "nuke.%s(nuke.thisNode())" % widget)
    knob.clearFlag(nuke.STARTLINE)
    return knob


def _slider(name, label, low, high, value, tooltip=None, startline=False):
    knob = nuke.Double_Knob(name, label)
    knob.setRange(low, high)
    knob.setValue(value)
    knob.setFlag(nuke.NO_ANIMATION)
    if tooltip:
        knob.setTooltip(tooltip)
    if startline:
        knob.setFlag(nuke.STARTLINE)
    else:
        knob.clearFlag(nuke.STARTLINE)
    return knob


def _margin_default():
    """El margen guardado en los defaults de Layout, o el de fabrica."""
    try:
        import LGA_BD_config

        return float(LGA_BD_config.get_backdrop_defaults()["margin"])
    except Exception:
        return MARGIN_DEFAULT


def _add_lga_knobs(node):
    """La pestana de LGA_backdrop, en el orden de LGA_BD_knobs.add_all_knobs."""
    label = node["label"].value()
    z = int(node["z_order"].value())

    node.addKnob(nuke.Tab_Knob("backdrop"))
    _link(node, "label_link", "Label", "label", startline=True)
    node.addKnob(
        _slider("lga_note_font_size", "Font Size", 10, 100, node["note_font_size"].value(), startline=True)
    )
    margen = nuke.Enumeration_Knob("lga_margin", "", ["left", "center", "right"])
    margen.setValue(_alignment_from_label(label))
    margen.clearFlag(nuke.STARTLINE)
    node.addKnob(margen)
    node.addKnob(_text("font_label", "       Font "))
    _link(node, "note_font_link", "", "note_font")

    node.addKnob(_text("divider_2"))
    node.addKnob(_text("resize_label", "    Resize  ", startline=False))
    node.addKnob(_text("margin_label", "Margin ", startline=False))
    node.addKnob(_slider("margin_slider", "", 10, 200, _margin_default(), "Margin slider for auto fit"))
    node.addKnob(_custom("lga_autofit_control", "LGA_AutoFitControlWidget"))

    node.addKnob(_text("divider_style"))
    node.addKnob(_text("appearance_label", "      Style "))
    if "appearance" in node.knobs():
        _link(node, "appearance_link", "", "appearance")
    if "border_width" in node.knobs():
        _link(node, "border_width_link", "", "border_width")
    node.addKnob(_custom("lga_save_defaults", "LGA_SaveDefaultsWidget"))

    node.addKnob(_text("divider_3"))
    node.addKnob(_text("z_order_label", "   Z Order  ", startline=False))
    node.addKnob(_text("zorder_back", "Back ", startline=False))
    node.addKnob(_slider("zorder", "", -10, 10, z))
    node.addKnob(_text("zorder_front", " Front", startline=False))
    node.addKnob(_text("zorder_space", " ", startline=False))

    node.addKnob(_text("divider_4"))
    node.addKnob(_custom("lga_color_palette", "LGA_ColorSwatchWidget"))


def to_lga_backdrop(node):
    """El backdrop con los knobs de LGA_backdrop (el mismo nodo)."""
    if node is None or node.Class() != "BackdropNode" or is_lga_backdrop(node):
        return node
    try:
        with _suppress_layout_callbacks():
            _add_lga_knobs(node)
        debug_print("  Backdrop convertido a LGA_backdrop:", node.name())
    except Exception as exc:
        debug_print("  [ERROR] No se pudieron agregar los knobs a %s: %r" % (node.name(), exc))
    return node


def _rect(node):
    x, y = node.xpos(), node.ypos()
    return x, y, x + node["bdwidth"].value(), y + node["bdheight"].value()


def _overlaps(a, b):
    ax0, ay0, ax1, ay1 = _rect(a)
    bx0, by0, bx1, by1 = _rect(b)
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def _inside(inner, outer):
    ix0, iy0, ix1, iy1 = _rect(inner)
    ox0, oy0, ox1, oy1 = _rect(outer)
    return ox0 <= ix0 and oy0 <= iy0 and ox1 >= ix1 and oy1 >= iy1


def _set_z(node, z):
    node["z_order"].setValue(z)
    if "zorder" in node.knobs():
        node["zorder"].setValue(z)


def raise_backdrops(backdrops):
    """Z order de los backdrops nuevos respecto de los que ya estaban."""
    nuevos = [b for b in backdrops if b is not None and b.Class() == "BackdropNode"]
    if not nuevos:
        return
    nuevos_nombres = set(b.fullName() for b in nuevos)
    resueltos = [b for b in nuke.allNodes("BackdropNode") if b.fullName() not in nuevos_nombres]

    # Del mas grande al mas chico: uno anidado se resuelve despues que el que
    # lo contiene y le queda arriba.
    nuevos.sort(key=lambda b: b["bdwidth"].value() * b["bdheight"].value(), reverse=True)
    for bd in nuevos:
        debajo = [o for o in resueltos if _overlaps(bd, o) and not _inside(o, bd)]
        adentro = [o for o in resueltos if _inside(o, bd)]
        z = max([o["z_order"].value() for o in debajo] + [-1]) + 1
        if adentro:
            z = min(z, min(o["z_order"].value() for o in adentro) - 1)
        _set_z(bd, z)
        resueltos.append(bd)
        debug_print("  Z order de %s: %s" % (bd.name(), z))
