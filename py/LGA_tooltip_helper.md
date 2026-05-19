> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_tooltip_helper — Tooltips estilizados para Qt

Helper que genera y aplica **tooltips ricos con HTML** a widgets Qt (QLabel, QPushButton, etc.).

Diseñado para usarse en paneles Hiero/Nuke donde Qt controla el look via stylesheet.

---

## Instalación rápida

```python
import sys, importlib

_mod = "LGA_NKS_Shared.LGA_tooltip_helper"
if _mod in sys.modules:
    del sys.modules[_mod]
tooltip_mod = importlib.import_module(_mod)

# Aplicar CSS global de QToolTip (una sola vez en la ventana)
tooltip_mod.apply_tooltip_stylesheet(QtWidgets.QApplication.instance())

# Luego usar en cualquier widget:
tooltip_mod.set_clip_tooltip(label, "TEST_013_020_comp_v02", 480, fps=24, color="#3381e0")
```

---

## API

### `apply_tooltip_stylesheet(target=None, bg="#1e1e1e", text="#d8d8d8", border="1px solid #444444", radius="5px", padding="0px", force=False)`

Inyecta el CSS de `QToolTip` en la `QApplication` o widget raíz.

**Llamar UNA SOLA VEZ** al iniciar la ventana. Si ya hay un stylesheet, el CSS se **añade** al existente sin sobreescribir.

```python
apply_tooltip_stylesheet(QtWidgets.QApplication.instance())
# o bien:
apply_tooltip_stylesheet(my_dialog)
```

El CSS aplicado establece fondo oscuro, borde sutil y bordes redondeados para todos los `QToolTip` de la app.

Para tooltips sin borde, o para sobrescribir una regla `QToolTip` ya instalada en una sesion larga, pasar parametros explicitos:

```python
apply_tooltip_stylesheet(
    QtWidgets.QApplication.instance(),
    bg="#1e1e1e",
    border="none",
    radius="0px",
    padding="0px",
    force=True,
)
```

| ParÃ¡metro | Tipo | DescripciÃ³n |
|-----------|------|-------------|
| `bg` | `str` | Color de fondo del widget `QToolTip` |
| `text` | `str` | Color de texto por defecto |
| `border` | `str` | CSS completo del borde; usar `"none"` para quitarlo |
| `radius` | `str` | Radio del borde del tooltip |
| `padding` | `str` | Padding exterior del widget `QToolTip` |
| `force` | `bool` | Si es `True`, agrega la regla aunque ya exista `QToolTip`, permitiendo sobrescribir estilos previos |

---

### `set_clip_tooltip(widget, name, frames, fps=24, color="#42616d", extra_rows=None)`

Tooltip estándar para chips de clips de timeline.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `widget` | `QWidget` | Widget al que asignar el tooltip |
| `name` | `str` | Nombre completo del clip |
| `frames` | `int` | Duración en frames |
| `fps` | `float` | FPS del proyecto (default `24`) |
| `color` | `str` | Color de acento del track (hex), usado para el título del tooltip |
| `extra_rows` | `list` | Lista de `(label, value)` para filas adicionales opcionales |

**Ejemplo simple:**
```python
set_clip_tooltip(label, "TEST_013_020_comp_v02", 480)
```

**Ejemplo con color y filas extra:**
```python
set_clip_tooltip(
    label,
    "TEST_013_020_comp_v02",
    frames=480,
    fps=24,
    color="#3381e0",           # comp color
    extra_rows=[
        ("Track",  "_comp_"),
        ("TC IN",  "01:00:22:20"),
        ("TC OUT", "01:00:42:19"),
    ]
)
```

El tooltip mostrará:
```
TEST_013_020_comp_v02
480f    20.00 s
Track   _comp_
TC IN   01:00:22:20
TC OUT  01:00:42:19
```

---

### `set_rich_tooltip(widget, html)`

Tooltip con **HTML arbitrario**. Útil cuando se necesita control total.

```python
html = "<b style='color:#ff0;'>¡Atención!</b><br>Este clip tiene media faltante."
set_rich_tooltip(label, html)
```

El HTML se renderiza dentro de la caja `QToolTip` ya estilizada.

---

### `make_tooltip_html(title, body_rows=None, accent_color="#42616d", width="220px")`

Genera el HTML de un tooltip genérico (no específico de clips).

```python
html = make_tooltip_html(
    title="Renombrar",
    body_rows=[
        ("Shot",    "TEST_013_020"),
        ("Versión", "v02"),
        ("Estado",  "Listo"),
    ],
    accent_color="#aa9e54",
    width="240px",
)
set_rich_tooltip(btn, html)
```

---

## Personalización

Los colores globales están definidos como constantes al inicio del módulo:

| Constante | Default | Descripción |
|-----------|---------|-------------|
| `_TOOLTIP_BG` | `#1e1e1e` | Fondo del tooltip |
| `_TOOLTIP_BORDER` | `#444444` | Borde exterior |
| `_TOOLTIP_TEXT` | `#d8d8d8` | Texto general |
| `_TOOLTIP_DIM` | `#888888` | Texto secundario / labels |
| `_TOOLTIP_RADIUS` | `5px` | Radio de bordes |
| `_TOOLTIP_PADDING` | `8px 12px` | Padding interno |

Para cambiar el look globalmente, editar estas constantes antes de llamar a `apply_tooltip_stylesheet`.

---

## Notas técnicas

- Qt renderiza el HTML de `setToolTip()` dentro del `QToolTip` widget. El fondo y borde de ese widget se controlan via `QToolTip { ... }` en el stylesheet de la QApplication, **no** via CSS interno del HTML.
- El HTML interno sirve para tipografía, colores de texto y layout (tablas).
- `apply_tooltip_stylesheet` detecta si ya hay `QToolTip` en el stylesheet existente y no lo duplica.
- El helper usa PySide2 con fallback a PySide6. Si ninguno está disponible, las funciones son no-ops silenciosos.

---

## Referencias técnicas

| Archivo | Función / Clase |
|---------|----------------|
| `LGA_NKS_Shared/LGA_tooltip_helper.py` | `apply_tooltip_stylesheet`, `set_clip_tooltip`, `set_rich_tooltip`, `make_tooltip_html`, `_clip_tooltip_html`, `_mix`, `_frames_to_seconds` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `ImportShotDialog._make_chip_label` (consume `set_clip_tooltip`), `_build_page_import` (consume `apply_tooltip_ss`) |
| `LGA_NKS_Shared/README_StyleUtils.md` | Referencia de sistema de colores y estilos de paneles |
| `docs/LGA_NKS_Panel_Style_Guide.md` | Guía general de estilos para paneles Hiero |
