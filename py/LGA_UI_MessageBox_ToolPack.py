"""
____________________________________________________________________

  LGA_UI_MessageBox_ToolPack v1.00 | Lega

  Carteles estandar del pack: info, warning, error y pregunta,
  estilados con LGA_UI_Style_ToolPack. Reemplazan a los QMessageBox
  estaticos de Qt, que salen con el tema del host y no con el del pack.

  Las firmas son ESPEJO de las estaticas de Qt a proposito, para que
  migrar un callsite sea cambiar el nombre y nada mas:

      QMessageBox.information(parent, title, text) -> show_info(parent, title, text)
      QMessageBox.warning(parent, title, text)     -> show_warning(parent, title, text)
      QMessageBox.critical(parent, title, text)    -> show_error(parent, title, text)

  Para preguntas:

      if ask_question(parent, "Delete", "Remove 3 clips?"):
          ...

  ask_question devuelve bool. El boton afirmativo va ultimo, a la
  derecha y en violeta (BTN_PRIMARY), como en el resto del pack; si
  ninguna opcion es la recomendada, pasar recommended=False y ningun
  boton queda marcado.

  Para un cartel que no entra en estos moldes (tres botones, checkbox,
  detalle expandible) esta styled_message_box(), que devuelve el
  QMessageBox ya estilado para terminar de armarlo en el callsite.

  Sin icono de sistema: los carteles del pack no usan los iconos del
  host, la jerarquia la dan el titulo de la ventana y el texto.

  v1.00: Version inicial, portado del helper de HieroTools con
         las fuentes del pack aplicadas (apply_ui_font).
____________________________________________________________________
"""

from LGA_QtAdapter_ToolPack import QtWidgets
from LGA_UI_Style_ToolPack import Style, apply_ui_font


def styled_message_box(parent=None, title="", text=""):
    """QMessageBox con el estilo del pack, para armar carteles a medida.

    Style.FORM trae la regla de QMessageBox QPushButton, asi que los
    botones que se agreguen despues salen con el secundario del pack.
    """
    box = QtWidgets.QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QtWidgets.QMessageBox.NoIcon)
    box.setStyleSheet(Style.FORM)
    apply_ui_font(box)
    return box


def _show(parent, title, text):
    box = styled_message_box(parent, title, text)
    box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    apply_ui_font(box)  # de nuevo: el boton Ok recien existe ahora
    box.exec_()


def show_info(parent, title, text):
    """Espejo de QMessageBox.information(parent, title, text)."""
    _show(parent, title, text)


def show_warning(parent, title, text):
    """Espejo de QMessageBox.warning(parent, title, text)."""
    _show(parent, title, text)


def show_error(parent, title, text):
    """Espejo de QMessageBox.critical(parent, title, text)."""
    _show(parent, title, text)


def ask_question(parent, title, text, yes_text="Yes", no_text="No", recommended=True):
    """Pregunta de dos botones. Devuelve True si se eligio el afirmativo.

    No usa QMessageBox: en Windows su QDialogButtonBox pone el AcceptRole a
    la IZQUIERDA, y la regla del pack pide el boton de accion ultimo, a la
    derecha. Se arma un QDialog con layout manual, igual que los
    FlowStatusWindow ya migrados.

    El afirmativo es el unico violeta y responde a Enter. Con
    recommended=False ninguno queda marcado ni responde a Enter: es el caso
    en que ninguna de las dos opciones es la recomendada y el cartel no
    debe empujar ninguna. Escape rechaza siempre.
    """
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet(Style.FORM)

    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setContentsMargins(18, 16, 18, 14)
    layout.setSpacing(12)

    label = QtWidgets.QLabel(text)
    label.setWordWrap(True)
    layout.addWidget(label)

    row = QtWidgets.QHBoxLayout()
    row.addStretch()
    no_button = QtWidgets.QPushButton(no_text)
    yes_button = QtWidgets.QPushButton(yes_text)
    no_button.setStyleSheet(Style.BTN_SECONDARY)
    if recommended:
        yes_button.setStyleSheet(Style.BTN_PRIMARY)
        yes_button.setDefault(True)
    else:
        yes_button.setStyleSheet(Style.BTN_SECONDARY)
        yes_button.setAutoDefault(False)
        no_button.setAutoDefault(False)
    row.addWidget(no_button)
    row.addWidget(yes_button)
    layout.addLayout(row)

    no_button.clicked.connect(dialog.reject)
    yes_button.clicked.connect(dialog.accept)

    apply_ui_font(dialog)  # al final: recorre hijos, que recien ahora existen
    return dialog.exec_() == QtWidgets.QDialog.Accepted
