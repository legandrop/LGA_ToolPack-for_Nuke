"""
_____________________________________________________________________________________________________

  LGA_ToolPack_settings v0.46 | Lega
  Configuracion de la herramienta LGA_ToolPack
_____________________________________________________________________________________________________
"""

import sys
import os
import configparser
import typing  # Importar typing
from typing import Optional, Tuple

from qt_compat import QtWidgets, QtCore, QtGui, QGuiApplication

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QGroupBox = QtWidgets.QGroupBox
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QFormLayout = QtWidgets.QFormLayout
QPushButton = QtWidgets.QPushButton
QTextEdit = QtWidgets.QTextEdit  # Importar QTextEdit
QMessageBox = QtWidgets.QMessageBox  # Importar QMessageBox
QCheckBox = QtWidgets.QCheckBox
QFileDialog = QtWidgets.QFileDialog
QFrame = QtWidgets.QFrame  # Divisores
Qt = QtCore.Qt

# Variable global para controlar el debug
DEBUG = False

# Espaciado vertical para divisores horizontales (en pixeles)
LINE_SPACING = 10


# Funcion debug_print
def debug_print(*message):
    if DEBUG:
        print(*message)


# Importar funciones y constantes desde LGA_Write_Focus
# Asumiendo que ambos scripts estan en el mismo directorio o en el sys.path
try:
    from LGA_Write_Focus import (
        get_config_path as wf_get_config_path,  # Renombrar para claridad
        ensure_config_exists as wf_ensure_config_exists,
        get_node_names_from_config as wf_get_node_names_from_config,
        DEFAULT_NODE_NAME as WF_DEFAULT_NODE_NAME,  # Renombrar constante
        DEFAULT_SECONDARY_NODE_NAME as WF_DEFAULT_SECONDARY_NODE_NAME,
        CONFIG_SECTION as WF_CONFIG_SECTION,  # Renombrar constante
        CONFIG_NODE_NAME_KEY as WF_CONFIG_NODE_NAME_KEY,  # Renombrar constante
        CONFIG_SECONDARY_NODE_NAME_KEY as WF_CONFIG_SECONDARY_NODE_NAME_KEY,
    )
except ImportError as e_wf:
    print(f"Error al importar LGA_Write_Focus.py: {e_wf}. Funcionalidad limitada.")

    # Definir funciones dummy y valores por defecto
    def wf_ensure_config_exists():
        pass

    def wf_get_node_names_from_config() -> typing.Tuple[str, str]:
        return ("Write_Pub", "Write_EXR Publish DWAA")

    def wf_get_config_path() -> typing.Optional[str]:
        return None

    WF_DEFAULT_NODE_NAME = "Write_Pub"
    WF_DEFAULT_SECONDARY_NODE_NAME = "Write_EXR Publish DWAA"
    WF_CONFIG_SECTION = "Settings"
    WF_CONFIG_NODE_NAME_KEY = "node_name"
    WF_CONFIG_SECONDARY_NODE_NAME_KEY = "secondary_node_name"

# --- Importaciones de LGA_showInlFlow ---
try:
    from LGA_showInlFlow import (
        get_config_path as sif_get_config_path,
        ensure_config_exists as sif_ensure_config_exists,
        get_credentials_from_config as sif_get_credentials_from_config,
        save_credentials_to_config as sif_save_credentials_to_config,
    )
except ImportError as e_sif:
    print(f"Error al importar LGA_showInlFlow.py: {e_sif}. Funcionalidad limitada.")

    # Definir funciones dummy y valores por defecto
    def sif_ensure_config_exists():
        pass

    def sif_get_credentials_from_config() -> (
        typing.Tuple[typing.Optional[str], typing.Optional[str], typing.Optional[str]]
    ):
        return None, None, None

    def sif_get_config_path() -> typing.Optional[str]:
        return None

    # Funcion save dummy
    def sif_save_credentials_to_config(url, login, password) -> bool:
        debug_print(
            "Error: LGA_showInlFlow.py no encontrado, no se pueden guardar credenciales."
        )
        return False


# --- Importaciones de LGA_RnW_ColorSpace_Favs --- Nuevo
try:
    from LGA_RnW_ColorSpace_Favs import (
        get_colorspace_ini_path,
        read_colorspaces_from_ini,
        save_colorspaces_to_ini,
        COLORSPACE_SECTION,  # Importar tambien la constante de seccion
    )
except ImportError as e_csf:
    print(
        f"Error al importar LGA_RnW_ColorSpace_Favs.py: {e_csf}. Funcionalidad limitada."
    )

    # Definir funciones dummy
    def get_colorspace_ini_path(create_if_missing: bool = True) -> typing.Optional[str]:
        return None

    def read_colorspaces_from_ini(ini_path: typing.Optional[str]) -> typing.List[str]:
        return []

    def save_colorspaces_to_ini(
        ini_path: typing.Optional[str], colorspaces_list: typing.List[str]
    ) -> bool:
        return False

    COLORSPACE_SECTION = "ColorSpaces"

# --- Importaciones de LGA_Write_RenderComplete --- NUEVO
try:
    from LGA_Write_RenderComplete import (
        get_config_path as rc_get_config_path,
        ensure_config_exists as rc_ensure_config_exists,
        get_mail_settings_from_config as rc_get_mail_settings_from_config,
        save_mail_settings_to_config as rc_save_mail_settings_to_config,
        CONFIG_FROM_KEY as RC_CONFIG_FROM_KEY,
        CONFIG_PASS_KEY as RC_CONFIG_PASS_KEY,
        CONFIG_TO_KEY as RC_CONFIG_TO_KEY,
        get_wav_path_from_config,
        save_wav_path_to_config,
        get_sound_enabled_from_config,
        save_sound_enabled_to_config,
        get_render_time_enabled_from_config,
        save_render_time_enabled_to_config,
    )
except ImportError as e_rc:
    print(
        f"Error al importar LGA_Write_RenderComplete.py: {e_rc}. Funcionalidad limitada."
    )

    def rc_ensure_config_exists() -> None:
        pass

    def rc_get_mail_settings_from_config() -> (
        Tuple[Optional[str], Optional[str], Optional[str]]
    ):
        return None, None, None

    def rc_save_mail_settings_to_config(from_email, from_password, to_email) -> bool:
        debug_print(
            "Error: LGA_Write_RenderComplete.py no encontrado, no se pueden guardar settings de mail."
        )
        return False

    def rc_get_config_path() -> Optional[str]:
        return None

    RC_CONFIG_FROM_KEY = "from_email"
    RC_CONFIG_PASS_KEY = "from_password"
    RC_CONFIG_TO_KEY = "to_email"


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LGA ToolPack Settings")
        self.setMinimumWidth(500)  # Más ancho para la ventana
        self.initUI()
        # Centrar la ventana en la pantalla (horizontal y vertical) DESPUES de show()
        self.show()
        qr = self.frameGeometry()
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            qr.moveCenter(geo.center())
            self.move(qr.topLeft())
        self.hide()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # --- Write Focus Section ---
        write_focus_layout = QVBoxLayout()
        write_focus_title = QLabel("Write Focus")
        write_focus_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        write_focus_layout.addWidget(write_focus_title)
        write_focus_form_layout = QFormLayout()
        self.write_focus_input = QLineEdit()
        self.write_focus_secondary_input = QLineEdit()
        try:
            wf_ensure_config_exists()
            node_name, secondary_node_name = wf_get_node_names_from_config()
            self.write_focus_input.setText(node_name or WF_DEFAULT_NODE_NAME)
            self.write_focus_secondary_input.setText(
                secondary_node_name or WF_DEFAULT_SECONDARY_NODE_NAME
            )
        except Exception as e:
            debug_print(f"Error al cargar config de Write Focus: {e}")
            self.write_focus_input.setText(WF_DEFAULT_NODE_NAME)
            self.write_focus_secondary_input.setText(WF_DEFAULT_SECONDARY_NODE_NAME)
        write_focus_form_layout.addRow(
            "Name of the Write Node to Focus:", self.write_focus_input
        )
        write_focus_form_layout.addRow(
            "Secondary Write Node Name:", self.write_focus_secondary_input
        )
        write_focus_layout.addLayout(write_focus_form_layout)
        self.save_write_focus_button = QPushButton("Save")
        self.save_write_focus_button.clicked.connect(self.save_write_focus_settings)
        write_focus_layout.addWidget(self.save_write_focus_button, 0, Qt.AlignRight)
        main_layout.addLayout(write_focus_layout)

        # Espaciado antes del divisor
        main_layout.addSpacing(LINE_SPACING)
        # Divisor
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line1)
        # Espaciado después del divisor
        main_layout.addSpacing(LINE_SPACING)

        # --- Render Complete Mail Settings Section ---
        render_mail_layout = QVBoxLayout()
        render_mail_title = QLabel("Render Complete")
        render_mail_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        render_mail_layout.addWidget(render_mail_title)
        render_mail_form_layout = QFormLayout()
        self.render_mail_from_input = QLineEdit()
        self.render_mail_pass_input = QLineEdit()
        self.render_mail_pass_input.setEchoMode(QLineEdit.Password)
        self.render_mail_to_input = QLineEdit()
        self.render_mail_from_input.setPlaceholderText("e.g., tuMail@outlook.com")
        self.render_mail_pass_input.setPlaceholderText("")
        self.render_mail_to_input.setPlaceholderText("e.g., tuMail@gmail.com")
        try:
            rc_ensure_config_exists()
            from_email, from_password, to_email = rc_get_mail_settings_from_config()
            self.render_mail_from_input.setText(from_email or "")
            self.render_mail_pass_input.setText(from_password or "")
            self.render_mail_to_input.setText(to_email or "")
        except Exception as e:
            debug_print(f"Error al cargar config de Render Complete Mail: {e}")
        self.cb_enable_render_time = QCheckBox("Enable render time calculation")
        self.cb_enable_sound = QCheckBox("Enable sound notification")
        try:
            self.cb_enable_render_time.setChecked(get_render_time_enabled_from_config())
        except Exception as e:
            debug_print(f"Error al leer setting de render time: {e}")
            self.cb_enable_render_time.setChecked(True)
        try:
            self.cb_enable_sound.setChecked(get_sound_enabled_from_config())
        except Exception as e:
            debug_print(f"Error al leer setting de sonido: {e}")
            self.cb_enable_sound.setChecked(True)
        render_mail_layout.addWidget(self.cb_enable_render_time)

        # Layout horizontal para sonido: checkbox + input + browse
        sound_layout = QHBoxLayout()
        sound_layout.addWidget(self.cb_enable_sound)
        self.wav_path_input = QLineEdit()
        self.wav_path_input.setPlaceholderText("Select .wav file...")
        try:
            wav_path = get_wav_path_from_config()
            self.wav_path_input.setText(wav_path)
        except Exception as e:
            debug_print(f"Error al cargar ruta wav: {e}")
            self.wav_path_input.setText("")
        self.wav_browse_btn = QPushButton("Browse")
        self.wav_browse_btn.clicked.connect(self.browse_wav_file)
        sound_layout.addWidget(self.wav_path_input)
        sound_layout.addWidget(self.wav_browse_btn)
        render_mail_layout.addLayout(sound_layout)
        # Espaciado antes del texto informativo
        render_mail_layout.addSpacing(10)
        # Texto informativo para la sección de mail
        mail_info_label = QLabel("Send mail when render is complete info:")
        mail_info_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        render_mail_layout.addWidget(mail_info_label)
        render_mail_form_layout.addRow("From (Outlook):", self.render_mail_from_input)
        render_mail_form_layout.addRow("Password:", self.render_mail_pass_input)
        render_mail_form_layout.addRow("To (Recipient):", self.render_mail_to_input)
        render_mail_layout.addLayout(render_mail_form_layout)
        self.save_render_mail_button = QPushButton("Save")
        self.save_render_mail_button.clicked.connect(self.save_render_mail_settings)
        render_mail_layout.addWidget(self.save_render_mail_button, 0, Qt.AlignRight)
        main_layout.addLayout(render_mail_layout)

        main_layout.addSpacing(LINE_SPACING)
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line2)
        main_layout.addSpacing(LINE_SPACING)

        # --- Show in Flow Section ---
        show_flow_layout = QVBoxLayout()
        show_flow_title = QLabel("Show in Flow")
        show_flow_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        show_flow_layout.addWidget(show_flow_title)
        show_flow_form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("e.g., https://studio.shotgrid.autodesk.com")
        self.username_input.setPlaceholderText("e.g., artist@studio.com")
        self.password_input.setPlaceholderText("")
        show_flow_form_layout.addRow(
            "ShotGrid URL:",
            self.site_input,
        )
        show_flow_form_layout.addRow("ShotGrid Login:", self.username_input)
        show_flow_form_layout.addRow("ShotGrid Password:", self.password_input)
        try:
            sif_ensure_config_exists()
            sif_url, sif_login, sif_password = sif_get_credentials_from_config()
            self.site_input.setText(sif_url or "")
            self.username_input.setText(sif_login or "")
            self.password_input.setText(sif_password or "")
        except Exception as e:
            debug_print(f"Error al cargar credenciales de Show in Flow: {e}")
        show_flow_layout.addLayout(show_flow_form_layout)

        # Boton Save para configuracion de Show/Flow
        self.save_show_flow_button = QPushButton("Save")
        self.save_show_flow_button.clicked.connect(self.save_show_flow_settings)
        show_flow_layout.addWidget(self.save_show_flow_button, 0, Qt.AlignRight)

        main_layout.addLayout(show_flow_layout)

        main_layout.addSpacing(LINE_SPACING)
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line3)
        main_layout.addSpacing(LINE_SPACING)

        # --- Color Space Favs Section ---
        color_space_layout = QVBoxLayout()
        color_space_title = QLabel("Color Space Favorites")
        color_space_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        color_space_layout.addWidget(color_space_title)
        color_space_layout.addWidget(
            QLabel("Enter favorite OCIO color spaces (one per line):")
        )
        self.color_space_edit = QTextEdit()
        self.color_space_edit.setPlaceholderText(
            "e.g.,\nOutput - sRGB\nUtility - Raw\nACES - ACEScg"
        )
        self.color_space_edit.setMinimumHeight(80)
        color_space_layout.addWidget(self.color_space_edit)
        try:
            self.colorspace_ini_path = get_colorspace_ini_path(create_if_missing=True)
            if self.colorspace_ini_path:
                fav_list = read_colorspaces_from_ini(self.colorspace_ini_path)
                self.color_space_edit.setText("\n".join(fav_list))
            else:
                debug_print(
                    "Advertencia: No se pudo obtener la ruta del INI de ColorSpaces."
                )
        except Exception as e:
            debug_print(f"Error al cargar Color Space Favs: {e}")
            QMessageBox.warning(
                self, "Error", f"Could not load Color Space Favorites:\n{e}"
            )
        self.save_color_space_button = QPushButton("Save")
        self.save_color_space_button.clicked.connect(self.save_color_space_settings)
        color_space_layout.addWidget(self.save_color_space_button, 0, Qt.AlignRight)
        main_layout.addLayout(color_space_layout)

        main_layout.addSpacing(LINE_SPACING)
        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line4)
        main_layout.addSpacing(LINE_SPACING)

        # --- Write Presets Section (Placeholder) ---
        write_presets_layout = QVBoxLayout()
        write_presets_title = QLabel("Write Presets")
        write_presets_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        write_presets_layout.addWidget(write_presets_title)
        self.open_write_presets_btn = QPushButton("Open Editor")
        self.open_write_presets_btn.clicked.connect(
            self.show_write_presets_not_implemented
        )
        write_presets_layout.addWidget(self.open_write_presets_btn, 0, Qt.AlignHCenter)
        main_layout.addLayout(write_presets_layout)
        main_layout.addStretch()

    def save_write_focus_settings(self):
        """Guarda los nombres de los nodos de Write Focus en su archivo .ini."""
        config_file_path = wf_get_config_path()
        if not config_file_path:
            debug_print("Error: No se pudo obtener la ruta para guardar Write Focus.")
            QMessageBox.critical(
                self,
                "Error",
                "Could not determine the configuration file path for Write Focus.",
            )
            return

        new_node_name = self.write_focus_input.text().strip()
        new_secondary_node_name = self.write_focus_secondary_input.text().strip()
        if not new_node_name:
            QMessageBox.warning(
                self, "Input Error", "Write Focus node name cannot be empty."
            )
            try:
                node_name, _ = wf_get_node_names_from_config()
                self.write_focus_input.setText(node_name or WF_DEFAULT_NODE_NAME)
            except Exception:
                self.write_focus_input.setText(WF_DEFAULT_NODE_NAME)
            return
        if not new_secondary_node_name:
            QMessageBox.warning(
                self, "Input Error", "Secondary Write node name cannot be empty."
            )
            try:
                _, secondary_node_name = wf_get_node_names_from_config()
                self.write_focus_secondary_input.setText(
                    secondary_node_name or WF_DEFAULT_SECONDARY_NODE_NAME
                )
            except Exception:
                self.write_focus_secondary_input.setText(WF_DEFAULT_SECONDARY_NODE_NAME)
            return
        config = configparser.ConfigParser()
        try:
            if os.path.exists(config_file_path):
                config.read(config_file_path)
            if not config.has_section(WF_CONFIG_SECTION):
                config.add_section(WF_CONFIG_SECTION)
            config.set(WF_CONFIG_SECTION, WF_CONFIG_NODE_NAME_KEY, new_node_name)
            config.set(
                WF_CONFIG_SECTION,
                WF_CONFIG_SECONDARY_NODE_NAME_KEY,
                new_secondary_node_name,
            )
            with open(config_file_path, "w") as configfile:
                config.write(configfile)
            debug_print(
                f"Configuracion de Write Focus guardada: {new_node_name}, {new_secondary_node_name}"
            )
            QMessageBox.information(self, "Success", "Write Focus settings saved.")
        except Exception as e:
            debug_print(f"Error al guardar la configuracion de Write Focus: {e}")
            QMessageBox.critical(
                self, "Save Error", f"Could not save Write Focus settings:\n{e}"
            )

    def save_show_flow_settings(self):
        """Guarda las credenciales de Show in Flow en su archivo .ini."""
        config_file_path = sif_get_config_path()
        if not config_file_path:
            debug_print("Error: No se pudo obtener la ruta para guardar Show in Flow.")
            QMessageBox.critical(
                self,
                "Error",
                "Could not determine the configuration file path for Show in Flow.",
            )
            return

        new_url = self.site_input.text().strip()
        new_login = self.username_input.text().strip()
        new_password = self.password_input.text()  # No hacer strip a la password

        if not new_url or not new_login or not new_password:
            QMessageBox.warning(
                self,
                "Input Error",
                "Show in Flow URL, Login, and Password cannot be empty.",
            )
            # No revertimos aqui, dejamos que el usuario corrija
            return

        # Llamar a la nueva funcion de guardado que maneja la codificacion
        try:
            success = sif_save_credentials_to_config(new_url, new_login, new_password)
            if success:
                # El mensaje de exito ya se imprime en la funcion save
                QMessageBox.information(self, "Success", "Show in Flow settings saved.")
            else:
                # El error especifico ya deberia haberse impreso
                QMessageBox.critical(
                    self,
                    "Save Error",
                    "Could not save Show in Flow settings. Check console for details.",
                )
        except Exception as e:
            debug_print(f"Error al llamar a save_credentials_to_config: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Unexpected error saving Show in Flow settings:\n{e}",
            )

    def save_color_space_settings(self):  # Nuevo metodo
        """Guarda la lista de Color Space Favorites en su archivo .ini."""
        # Re-obtener la ruta por si acaso, pero no forzar creacion/copia aqui
        ini_path = getattr(
            self,
            "colorspace_ini_path",
            get_colorspace_ini_path(create_if_missing=False),
        )

        if not ini_path:
            debug_print(
                "Error: No se pudo obtener la ruta para guardar Color Space Favs."
            )
            QMessageBox.critical(
                self,
                "Error",
                "Could not determine the configuration file path for Color Space Favorites.",
            )
            return

        # Obtener texto del QTextEdit
        text = self.color_space_edit.toPlainText()
        # Dividir en lineas, quitar espacios y filtrar vacias/solo espacios
        favorites_list = [line.strip() for line in text.split("\n") if line.strip()]

        # Usar la funcion importada para guardar
        try:
            success = save_colorspaces_to_ini(ini_path, favorites_list)
            if success:
                debug_print("Configuracion de Color Space Favorites guardada.")
                QMessageBox.information(self, "Success", "Color Space Favorites saved.")
            else:
                # El error especifico ya deberia haberse impreso en la funcion save_colorspaces_to_ini
                QMessageBox.critical(
                    self,
                    "Save Error",
                    "Could not save Color Space Favorites. Check console for details.",
                )

        except Exception as e:
            # Captura por si save_colorspaces_to_ini lanza una excepcion inesperada
            debug_print(f"Error inesperado al llamar a save_colorspaces_to_ini: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Unexpected error saving Color Space Favorites:\n{e}",
            )

    def save_render_mail_settings(self):
        """Guarda los datos de mail de Render Complete en su archivo .ini."""
        config_file_path = rc_get_config_path()
        if not config_file_path:
            debug_print(
                "Error: No se pudo obtener la ruta para guardar Render Complete Mail."
            )
            QMessageBox.critical(
                self,
                "Error",
                "Could not determine the configuration file path for Render Complete Mail.",
            )
            return
        from_email = self.render_mail_from_input.text().strip()
        from_password = self.render_mail_pass_input.text()
        to_email = self.render_mail_to_input.text().strip()
        wav_path = self.wav_path_input.text().strip()
        sound_enabled = self.cb_enable_sound.isChecked()
        render_time_enabled = self.cb_enable_render_time.isChecked()
        if not from_email or not from_password or not to_email:
            QMessageBox.warning(
                self,
                "Input Error",
                "All mail fields must be filled (From, Password, To).",
            )
            # No revertimos, dejamos que el usuario corrija
            return
        try:
            # La funcion rc_save_mail_settings_to_config ahora maneja la codificacion interna
            success = rc_save_mail_settings_to_config(
                from_email, from_password, to_email
            )
            # Guardar el path del wav
            wav_success = save_wav_path_to_config(wav_path)
            # Guardar el setting de sonido
            sound_success = save_sound_enabled_to_config(sound_enabled)
            # Guardar el setting de render time
            render_time_success = save_render_time_enabled_to_config(
                render_time_enabled
            )
            if success and wav_success and sound_success and render_time_success:
                # El mensaje de exito ya se imprime en la funcion save
                QMessageBox.information(
                    self, "Success", "Render Complete Mail settings saved."
                )
            else:
                # El error especifico ya deberia haberse impreso
                QMessageBox.critical(
                    self,
                    "Save Error",
                    "Could not save Render Complete Mail settings. Check console for details.",
                )
        except Exception as e:
            debug_print(f"Error al llamar a save_mail_settings_to_config: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Unexpected error saving Render Complete Mail settings:\n{e}",
            )

    def browse_wav_file(self):
        """Abre un diálogo para seleccionar un archivo .wav y lo pone en el QLineEdit."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select WAV file", "", "WAV Files (*.wav)"
        )
        if file_path:
            self.wav_path_input.setText(file_path)
            # Guardar inmediatamente el nuevo path seleccionado
            save_wav_path_to_config(file_path)

    def show_write_presets_not_implemented(self):
        """Muestra un mensaje indicando que la función aún no está implementada."""
        QMessageBox.information(
            self,
            "Not Implemented",
            "The Write Presets editor is not yet implemented.\nComing soon!",
        )

    def keyPressEvent(self, event):
        """Cerrar la ventana si se presiona ESC."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # --- Metodo para abrir la ventana de configuracion de nomenclatura --- NUEVO

    # --- Fin Metodo ---


# --- Instancia global para la ventana de Settings ---
settings_window_instance = None


def main():
    """Funcion principal para abrir la ventana de Settings y mantenerla viva."""
    global settings_window_instance
    app = QApplication.instance() or QApplication(sys.argv)
    if settings_window_instance is None or not settings_window_instance.isVisible():
        settings_window_instance = SettingsWindow()
        settings_window_instance.show()
    else:
        settings_window_instance.raise_()
        settings_window_instance.activateWindow()


# --- Main Execution ---
if __name__ == "__main__":
    # Necesario para ejecucion standalone fuera de Nuke
    main()
