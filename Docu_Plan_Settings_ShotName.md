# Planificación y Documentación: Settings de Nomenclatura de Archivos (Shot Naming)

Este documento describe el funcionamiento del script `LGA_showInlFlow.py` y planifica la creación de un sistema de configuración centralizado para manejar las convenciones de nombres de archivo en los scripts de LGA_ToolPack.

## 1. Funcionamiento Actual de `LGA_showInlFlow.py`

**Objetivo:** Abrir la página de la tarea "Comp" en Flow (anteriormente ShotGrid) correspondiente al script de Nuke activo.

**Proceso:**

1.  **Obtener Nombre del Script:** Lee el nombre del archivo `.nk` actualmente abierto en Nuke (`nuke.root().name()`).
2.  **Extraer Información (Lógica Fija):**
    *   Asume que las partes del nombre están separadas por guiones bajos (`_`).
    *   Asume que el **Nombre del Proyecto** es la *primera parte* (índice 0) del nombre.
    *   Asume que el **Código del Shot** (Shot Code) se construye uniendo las *primeras cinco partes* (índices 0-4) del nombre con guiones bajos.
3.  **Conectar a Flow:** Utiliza las credenciales guardadas de forma segura (`ShowInFlow.dat`) para conectarse a la API de Flow.
4.  **Buscar en Flow:**
    *   Busca un `Project` en Flow cuyo campo `name` coincida con el Nombre del Proyecto extraído.
    *   Si lo encuentra, busca dentro de ese proyecto un `Shot` cuyo campo `code` coincida con el Código del Shot construido.
5.  **Buscar Tarea "Comp":**
    *   Si encuentra el Shot, busca entre sus `Task` asociadas una cuyo campo `content` sea exactamente `"Comp"`.
6.  **Abrir URL:** Si encuentra la tarea "Comp", construye su URL de detalle en Flow y la abre en el navegador web configurado.

**Limitaciones Actuales:**

*   **Dependencia Fuerte de la Nomenclatura:** La extracción del Proyecto y el Shot Code está *fijada* a una estructura específica (primer elemento para proyecto, primeros cinco para shot code, separados por `_`). No funciona si la convención de nombres es diferente.
*   **Nombre de Tarea Fijo:** Asume que la tarea relevante siempre se llama `"Comp"`. No funciona si la tarea tiene otro nombre (ej. "Compositing", "VFX").

## 2. Necesidad de un Sistema de Configuración Centralizado

Para que `LGA_showInlFlow.py` (y potencialmente otros scripts de LGA_ToolPack) funcionen en diferentes entornos con distintas convenciones de nombres, es necesario crear un panel de configuración donde el usuario pueda definir cómo se estructura su nomenclatura de archivos.

**Objetivos del Sistema de Settings:**

*   Permitir al usuario definir la estructura de sus nombres de archivo de Nuke.
*   Permitir al usuario especificar qué partes de esa estructura corresponden al `Project` y cómo se compone el `Shot Code` para buscar en Flow.
*   Permitir al usuario definir el nombre exacto de la tarea (`Task Content`) que `LGA_showInlFlow.py` debe buscar.
*   Centralizar esta configuración para que otros scripts puedan reutilizarla si es necesario.

## 3. Diseño de la Interfaz de Usuario (UI) para Settings

Se propone una ventana de configuración accesible desde Nuke (probablemente a través de un menú "LGA ToolPack Settings"). La interfaz se estructurará en tres secciones claras:

```text
+--------------------------------------------------------------------------+
| LGA_showInFlow Settings                                            [X] |
+--------------------------------------------------------------------------+
|                                                                          |
|  [-] 1. Filename Pattern Structure                                       |
|  |                                                                        |
|  | Define the structure of your Nuke script filenames using predefined    |
|  | tags separated by underscores (_). Do not include the version suffix |
|  | (_vXX) or the file extension (.nk).                                  |
|  | Available tags: Project, Sequence, Shot, Task, Version, Extra.       |
|  | Ensure 'Project' and 'Shot' tags are included. 'Extra' can represent |
|  | one or more optional parts. Define the full pattern structure, as    |
|  | other LGA tools might use all parts.                                 |
|  |                                                                        |
|  |  __________________________________________________________________   |
|  | | Ej: Project_Sequence_Shot_Extra_Task                             |  |
|  |  ------------------------------------------------------------------   |
|  |                                                                        |
|  | *Example Breakdown: If your file is 'MYPROJ_SQ010_SH020_comp_v01.nk',*|
|  | *your pattern might be: Project_Sequence_Shot_Task*                   |
|  |                                                                        |
|                                                                          |
|  [-] 2. Shot Code Composition                                            |
|  |                                                                        |
|  | Write the tags from your pattern (above), separated by underscores (_),|
|  | that combine to form the **exact Shot Code** used in Flow's 'Shot'   |
|  | entity 'code' field.                                                 |
|  |                                                                        |
|  |  __________________________________________________________________   |
|  | | Ej: Sequence_Shot                                                  |  |
|  |  ------------------------------------------------------------------   |
|  |                                                                        |
|  | *Examples:*                                                          |
|  | *- If Flow Code is 'SQ010_SH020' -> Write: Sequence_Shot*            |
|  | *- If Flow Code is 'MYPROJ_SH020' -> Write: Project_Shot*             |
|  | *- If Flow Code is just 'SH020' -> Write: Shot*                      |
|  |                                                                        |
|                                                                          |
|  [-] 3. Target Flow Task Name                                            |
|  |                                                                        |
|  | Enter the exact name (case-sensitive) of the Task to open in Flow.   |
|  | This must match the 'content' field of the 'Task' entity.            |
|  | (This is often 'Comp' for Nuke scripts).                             |
|  |                                                                        |
|  |  __________________________________________________________________   |
|  | | Comp                                                             |  |
|  |  ------------------------------------------------------------------   |
|  |                                                                        |
|                                                                          |
|                                           +---------------+  +----------+  |
|                                           | Save Settings |  |  Cancel  |  |
|                                           +---------------+  +----------+  |
|                                                                          |
+--------------------------------------------------------------------------+
```

## 4. Lógica de Implementación (Resumen)

1.  **Crear Módulo de Settings:** Un nuevo script Python (ej. `LGA_settings_manager.py`) que:
    *   Defina la clase de la UI con PySide2 basada en el diseño anterior.
    *   Implemente funciones para guardar y cargar la configuración (ej. en un archivo JSON o `.ini` en una ubicación estándar como `%APPDATA%/LGA/ToolPack/config.json`).
    *   Proporcione funciones para que otros scripts (como `LGA_showInlFlow.py`) puedan leer fácilmente los valores de configuración guardados.
2.  **Modificar `LGA_showInlFlow.py`:**
    *   Importar el módulo de settings.
    *   En lugar de la lógica fija de extracción, llamar a una función que:
        *   Lea el patrón de nombre de archivo desde la configuración.
        *   Lea la definición de composición del Shot Code desde la configuración.
        *   Lea el nombre de la Tarea objetivo desde la configuración.
        *   Analice (`parse`) el nombre del script de Nuke actual según el patrón.
        *   Extraiga el valor del `Project` según la etiqueta `Project` en el patrón.
        *   Construya el `Shot Code` uniendo los valores de las etiquetas especificadas en la configuración.
        *   Utilice el nombre de la Tarea configurado al buscar en Flow.
3.  **Integración en Nuke:** Añadir una entrada de menú en Nuke para lanzar la ventana de configuración definida en `LGA_settings_manager.py`.
