"""
LGA_tooltip_helper.py
─────────────────────
Helper para aplicar tooltips estilizados a widgets Qt en paneles de Hiero/Nuke.

Los tooltips de Qt soportan HTML rich text. Para que el fondo y borde se
apliquen correctamente, el QToolTip stylesheet debe establecerse en la QApplication.
Este helper ofrece:

  set_clip_tooltip(widget, name, frames, fps=24, color="#42616d")
      Tooltip estándar para chips de clips de timeline.

  set_rich_tooltip(widget, html)
      Tooltip con HTML arbitrario (máximo control).

  apply_tooltip_stylesheet(app_or_widget)
      Aplica el QToolTip CSS global a la QApplication o al widget raíz.
      Debe llamarse UNA SOLA VEZ al iniciar la ventana.

Uso típico
──────────
  from LGA_tooltip_helper import set_clip_tooltip, apply_tooltip_stylesheet
  apply_tooltip_stylesheet(QtWidgets.QApplication.instance())
  set_clip_tooltip(label, "TEST_013_020_comp_v02", 480, fps=24, color="#3381e0")
"""

# ── imports ───────────────────────────────────────────────────────────────────

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore
    except ImportError:
        QtWidgets = None
        QtCore    = None


# ── constants ─────────────────────────────────────────────────────────────────

_TOOLTIP_BG      = "#1e1e1e"
_TOOLTIP_BORDER  = "#444444"
_TOOLTIP_TEXT    = "#d8d8d8"
_TOOLTIP_DIM     = "#888888"
_TOOLTIP_RADIUS  = "5px"
_TOOLTIP_PADDING = "8px 12px"

# CSS global inyectado en QApplication — controla la caja exterior del tooltip
def _make_qtooltip_css(
    bg: str = _TOOLTIP_BG,
    text: str = _TOOLTIP_TEXT,
    border: str = "1px solid " + _TOOLTIP_BORDER,
    radius: str = _TOOLTIP_RADIUS,
    padding: str = "0px",
) -> str:
    return """
QToolTip {{
    background-color: {bg};
    color:            {text};
    border:           {border};
    border-radius:    {radius};
    padding:          {padding};
    font-size:        12px;
}}
""".format(
        bg=bg,
        text=text,
        border=border,
        radius=radius,
        padding=padding,
    )


_QTTOOLTIP_CSS = _make_qtooltip_css()


# ── internal helpers ──────────────────────────────────────────────────────────

def _mix(hex_a: str, hex_b: str, t: float) -> str:
    """Interpola linealmente entre hex_a (t=1) y hex_b (t=0)."""
    def parse(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    ra, ga, ba = parse(hex_a)
    rb, gb, bb = parse(hex_b)
    r = int(ra * t + rb * (1 - t))
    g = int(ga * t + gb * (1 - t))
    b = int(ba * t + bb * (1 - t))
    return "#%02x%02x%02x" % (r, g, b)


def _frames_to_seconds(frames: int, fps: float = 24.0) -> str:
    """Convierte frames a string de segundos con dos decimales."""
    if fps <= 0:
        return "—"
    secs = frames / fps
    return "%.2f s" % secs


def _clip_tooltip_html(
    name: str,
    frames: int,
    fps: float = 24.0,
    accent_color: str = "#42616d",
    extra_rows: list = None,
) -> str:
    """
    Genera el HTML para el tooltip de un clip de timeline.

    Args:
        name:         Nombre completo del clip.
        frames:       Duración en frames.
        fps:          Frames por segundo (para convertir a segundos).
        accent_color: Color de acento derivado del track (hex).
        extra_rows:   Lista de tuplas (label, value) para filas adicionales.
                      Ejemplo: [("TC IN", "01:00:00:00"), ("Track", "aPlate")]
    """
    accent_bright = _mix(accent_color, "#ffffff", 0.70)
    secs_str      = _frames_to_seconds(frames, fps)

    rows_html = ""
    if extra_rows:
        for lbl, val in extra_rows:
            rows_html += (
                "<tr>"
                "<td style='color:{dim}; padding-right:10px; white-space:nowrap;'>{lbl}</td>"
                "<td style='color:{text}; white-space:nowrap;'>{val}</td>"
                "</tr>"
            ).format(dim=_TOOLTIP_DIM, text=_TOOLTIP_TEXT, lbl=lbl, val=val)

    html = (
        "<div style='"
        "background:{bg};"
        "border:1px solid {border};"
        "border-radius:{radius};"
        "padding:{pad};"
        "min-width:200px;"
        "'>"
        # Nombre del clip
        "<p style='"
        "margin:0 0 6px 0;"
        "color:{accent};"
        "font-weight:bold;"
        "font-size:13px;"
        "word-break:break-all;"
        "'>{name}</p>"
        # Línea de duración
        "<p style='margin:0 0 4px 0; font-size:12px;'>"
        "<span style='color:{text};'>{frames}f</span>"
        "&nbsp;&nbsp;"
        "<span style='color:{dim};'>{secs}</span>"
        "</p>"
        # Filas extra
        "{rows}"
        "</div>"
    ).format(
        bg=_TOOLTIP_BG,
        border=_TOOLTIP_BORDER,
        radius=_TOOLTIP_RADIUS,
        pad=_TOOLTIP_PADDING,
        accent=accent_bright,
        name=name,
        frames=frames,
        text=_TOOLTIP_TEXT,
        dim=_TOOLTIP_DIM,
        secs=secs_str,
        rows=(
            ("<table style='margin-top:6px; border-collapse:collapse;'>"
             + rows_html
             + "</table>")
            if rows_html else ""
        ),
    )
    return html


# ── public API ────────────────────────────────────────────────────────────────

def apply_tooltip_stylesheet(
    target=None,
    bg: str = _TOOLTIP_BG,
    text: str = _TOOLTIP_TEXT,
    border: str = "1px solid " + _TOOLTIP_BORDER,
    radius: str = _TOOLTIP_RADIUS,
    padding: str = "0px",
    force: bool = False,
):
    """
    Aplica el CSS de QToolTip globalmente.

    Args:
        target: QApplication o QWidget raíz. Si es None intenta obtener
                QApplication.instance().

    Llama a esto UNA SOLA VEZ al construir la ventana principal.
    Si ya hay un stylesheet aplicado, el CSS de QToolTip se añade al existente.
    """
    if QtWidgets is None:
        return
    if target is None:
        target = QtWidgets.QApplication.instance()
    if target is None:
        return

    current = target.styleSheet() if hasattr(target, "styleSheet") else ""
    if "QToolTip" not in current or force:
        css = _make_qtooltip_css(bg, text, border, radius, padding)
        target.setStyleSheet(current + "\n" + css)


def set_clip_tooltip(
    widget,
    name: str,
    frames: int,
    fps: float = 24.0,
    color: str = "#42616d",
    extra_rows: list = None,
):
    """
    Asigna un tooltip estilizado de clip de timeline a un widget Qt.

    Args:
        widget:     QWidget (p.ej. QLabel chip).
        name:       Nombre completo del clip.
        frames:     Duración en frames.
        fps:        FPS del proyecto (default 24).
        color:      Color de acento del track (hex).
        extra_rows: [(label, value), ...] filas opcionales adicionales.

    Ejemplo:
        set_clip_tooltip(lbl, "TEST_013_020_comp_v02", 480, fps=24,
                         color="#3381e0",
                         extra_rows=[("Track", "_comp_"), ("TC IN", "01:00:22:20")])
    """
    if widget is None:
        return
    html = _clip_tooltip_html(name, frames, fps, color, extra_rows)
    widget.setToolTip(html)


def set_rich_tooltip(widget, html: str):
    """
    Asigna un tooltip con HTML arbitrario a un widget Qt.
    Útil cuando se necesita control total sobre el contenido.

    Args:
        widget: QWidget.
        html:   HTML completo del tooltip.
    """
    if widget is None:
        return
    widget.setToolTip(html)


def make_tooltip_html(
    title: str,
    body_rows: list = None,
    accent_color: str = "#42616d",
    width: str = "220px",
) -> str:
    """
    Genera HTML de tooltip genérico (no específico de clips).

    Args:
        title:        Título en la parte superior (bold, accent color).
        body_rows:    Lista de (label, value) o strings para el cuerpo.
        accent_color: Color de acento (hex).
        width:        Ancho mínimo del div.

    Returns:
        str — HTML listo para setToolTip().
    """
    accent_bright = _mix(accent_color, "#ffffff", 0.70)
    rows_html = ""
    if body_rows:
        for item in body_rows:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                lbl, val = item
                rows_html += (
                    "<tr>"
                    "<td style='color:{dim}; padding-right:10px; white-space:nowrap;'>{lbl}</td>"
                    "<td style='color:{text}; white-space:nowrap;'>{val}</td>"
                    "</tr>"
                ).format(dim=_TOOLTIP_DIM, text=_TOOLTIP_TEXT, lbl=lbl, val=val)
            else:
                rows_html += (
                    "<tr><td colspan='2' style='color:{text}; padding-top:4px;'>{row}</td></tr>"
                ).format(text=_TOOLTIP_TEXT, row=str(item))

    table = (
        "<table style='margin-top:8px; border-collapse:collapse;'>"
        + rows_html
        + "</table>"
    ) if rows_html else ""

    return (
        "<div style='"
        "background:{bg}; border:1px solid {border}; border-radius:{radius};"
        "padding:{pad}; min-width:{width};"
        "'>"
        "<p style='margin:0 0 2px 0; font-weight:bold; font-size:13px;"
        "color:{accent};'>{title}</p>"
        "{table}"
        "</div>"
    ).format(
        bg=_TOOLTIP_BG, border=_TOOLTIP_BORDER, radius=_TOOLTIP_RADIUS,
        pad=_TOOLTIP_PADDING, width=width, accent=accent_bright,
        title=title, table=table,
    )
