"""
____________________________________________________________________

  LGA_Write_Presets_Range v2.85 | Lega

  Rango opcional del TimeClip conectado al EditRef para Writes MOV/MXF.

  v2.83: Busca conexiones indirectas y ofrece copiar el rango de salida y activar use_limit,
         incluyendo el desplazamiento start at del TimeClip.
____________________________________________________________________
"""

import html
import logging
import os
import re

import nuke
from LGA_Write_Presets_Dialogs import ask_question, show_warning

DEBUG = False


def _logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    try:
        folder = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(folder, exist_ok=True)
        handler = logging.FileHandler(
            os.path.join(folder, "DebugPy_LGA_Write_Presets_Range.log"),
            mode="w", encoding="utf-8")
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    if DEBUG:
        logger.addHandler(logging.StreamHandler())
    return logger


def find_editref_clips(nodes):
    """Solo sigue entradas reales dentro del grafo actual, sin entrar en gizmos."""
    reads = set()
    for node in nodes:
        if node.Class() != "Read":
            continue
        filename = node["file"].value().replace("\\", "/").rsplit("/", 1)[-1]
        if "editref" in re.sub(r"[\s_.-]+", "", filename).lower():
            reads.add(node.fullName())
    matches = []
    for node in nodes:
        if node.Class() != "TimeClip":
            continue
        pending = [node]
        visited = set()
        while pending:
            upstream = pending.pop()
            name = upstream.fullName()
            if name in visited:
                continue
            visited.add(name)
            if name in reads:
                matches.append((node, name))
                break
            pending.extend(upstream.input(i) for i in range(upstream.inputs())
                           if upstream.input(i) is not None)
    return matches


def offer_editref_range(created_nodes):
    """No modifica Writes existentes ni cambia rangos sin respuesta afirmativa."""
    log = _logger()
    writes = []
    pending = list(created_nodes)
    while pending:
        node = pending.pop()
        if node.Class() == "Group":
            pending.extend(node.nodes())
        elif node.Class() == "Write" and str(node["file_type"].value()).lower() in ("mov", "mxf"):
            writes.append(node)
    log.info("Writes MOV/MXF nuevos: %s", [w.fullName() for w in writes])
    if not writes:
        return False
    matches = find_editref_clips(nuke.allNodes())
    log.info("TimeClips de EditRef: %s", [(n.fullName(), r) for n, r in matches])
    if not matches:
        return False
    ranges = {(int(n.firstFrame()), int(n.lastFrame())) for n, _ in matches}
    if len(ranges) != 1 or any(first > last for first, last in ranges):
        log.warning("Rangos ambiguos o invalidos: %s", ranges)
        show_warning(None, "Write Presets", "The EditRef TimeClips have conflicting or invalid ranges.<br>The new Writes keep their preset ranges.")
        return False
    first, last = next(iter(ranges))
    sources = "<br>".join("%s → %s" % (html.escape(r), html.escape(n.fullName()))
                             for n, r in matches)
    names = ", ".join(html.escape(w.fullName()) for w in writes)
    accepted = ask_question(
        None, "Write Presets — Limit render range",
        "EditRef connected to TimeClip:<br>%s<br><br>"
        "Limit <b>%s</b> to frames <b>%s–%s</b>?<br>"
        "This enables the Write frame limit and sets its first and last frames."
        % (sources, names, first, last),
        yes_text="Limit range", no_text="Keep range")
    log.info("Rango %s–%s; aceptado: %s", first, last, accepted)
    if accepted:
        for write in writes:
            write["first"].setValue(first)
            write["last"].setValue(last)
            write["use_limit"].setValue(True)
    return accepted
