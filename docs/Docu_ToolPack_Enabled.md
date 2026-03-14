> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Sistema de Configuración de Herramientas LGA ToolPack

## 🎯 ¿Qué es este sistema?

El **Sistema de Configuración de Herramientas** es una funcionalidad avanzada del LGA ToolPack que permite a los usuarios personalizar completamente qué herramientas se cargan y muestran en el menú de Nuke. Esto proporciona un control total sobre el entorno de trabajo, optimizando la carga y evitando clutter en el menú.

## 📁 Archivos del Sistema

### Archivos de Configuración
- **`_LGA_ToolPack_Enabled.ini`** (en carpeta del paquete): Configuración por defecto
- **`_LGA_ToolPack_Enabled.ini`** (en `~/.nuke/`): Configuración personal del usuario

### Archivos del Sistema
- **`menu.py`**: Menú principal con el sistema integrado
- **`Docu_ToolPack_Enabled.md`**: Esta documentación

## ⚙️ Cómo Funciona

### 1. Carga de Configuración
```python
# El sistema busca archivos .ini en este orden:
1. ~/.nuke/_LGA_ToolPack_Enabled.ini (usuario) - PRIORIDAD
2. LGA_ToolPack/_LGA_ToolPack_Enabled.ini (paquete) - DEFAULTS
```

### 2. Evaluación de Herramientas
- **True**: La herramienta se carga y muestra en el menú
- **False**: La herramienta NO se carga ni muestra
- **No existe**: Se asume **True** (compatibilidad hacia atrás)

### 3. Carga Perezosa (Lazy Loading)
- Los módulos de las herramientas se importan **solo** cuando están habilitadas
- Mejora significativamente el tiempo de inicio de Nuke
- Reduce el uso de memoria

## 📝 Formato del Archivo .ini

```ini
[Tools]
; LGA ToolPack – Tool Switches
; Set to False to hide a tool from the menu AND avoid importing its script.
; Leave True to keep it visible and load on demand.
; Example: Media_Manager = False

Media_Manager = True
Media_Path_Replacer = True
CopyCat_Cleaner = True
Read_From_Write = True
; ... todas las demás herramientas
```

## 🛠️ Lista Completa de Herramientas Configurables

### READ n WRITE TOOLS
- **Media_Manager**: Gestor de medios multimedia
- **Media_Path_Replacer**: Reemplazador de rutas de medios
- **CopyCat_Cleaner**: Limpiador de CopyCat
- **Read_From_Write**: Leer desde Write
- **Write_Presets**: Preajustes de Write
- **Write_Focus**: Enfoque de Write
- **Write_Add_Send_Mail**: Opción de envío de mail en Write
- **Show_in_Explorer**: Mostrar en Explorador
- **Show_in_Flow**: Mostrar en Flow
- **Color_Space_Favs**: Favoritos de espacio de color

### FRAME RANGE TOOLS
- **FR_Read_to_Project**: Leer → Proyecto
- **FR_Read_to_Project_Res**: Leer → Proyecto (+Res)

### ROTATE TRANSFORM SHORTCUTS
- **Rotate_Commands**: Todos los comandos de rotación (4 comandos)

### COPY n PASTE TOOLS
- **Paste_To_Selected**: Pegar a seleccionado
- **Copy_with_inputs**: Copiar con entradas
- **Paste_with_inputs**: Pegar con entradas
- **Duplicate_with_inputs**: Duplicar con entradas

### NODE BUILDS & KNOBS
- **Build_Iteration**: Construir iteración
- **Build_Roto_BlurMask**: Construir roto + blur en máscara de entrada
- **Build_Merge_SwitchOps**: Construir merge (máscara) | Cambiar operaciones
- **Build_Grade**: Construir grade
- **Build_Grade_Highlights**: Construir grade de highlights
- **Disable_A_B**: Deshabilitar A-B
- **Channels_Cycle**: Ciclo de canales
- **Channel_HotBox**: HotBox de canales

### VA TOOLS
- **Viewer_Rec709**: Visor Rec709
- **Snapshot_Tools**: Herramientas de snapshot (Take + Show Hold)
- **Reset_Workspace**: Reiniciar workspace
- **Restart_NukeX**: Reiniciar NukeX

### HERRAMIENTAS ESPECIALES
- **Settings**: Configuraciones del ToolPack
- **Documentation**: Siempre disponible (no configurable)

## 🚀 Cómo Configurar

### Paso 1: Localizar el Archivo
1. Abre tu carpeta personal de Nuke: `~/.nuke/`
2. Si no existe, crea el archivo: `_LGA_ToolPack_Enabled.ini`

### Paso 2: Copiar la Configuración Base
Copia el contenido del archivo de defaults desde la carpeta del paquete:
```
LGA_ToolPack/_LGA_ToolPack_Enabled.ini
```

### Paso 3: Personalizar
Edita las líneas cambiando `True` por `False` para deshabilitar herramientas:

```ini
[Tools]
; Deshabilitar herramientas que no uso
Media_Manager = False
Color_Space_Favs = False
Rotate_Commands = False
Snapshot_Tools = False

; Mantener las que sí uso
CopyCat_Cleaner = True
Read_From_Write = True
Viewer_Rec709 = True
```

### Paso 4: Aplicar Cambios
1. Guarda el archivo
2. Reinicia Nuke
3. Las herramientas deshabilitadas no aparecerán en el menú

> **Nota**: La herramienta **Documentation** siempre está disponible en el menú y no se puede deshabilitar.

## 💡 Ventajas del Sistema

### Para Usuarios Individuales
- **Personalización**: Solo ver las herramientas que necesitas
- **Performance**: Inicio más rápido de Nuke
- **Limpieza**: Menú menos cluttered
- **Flexibilidad**: Cambiar configuración sin reinstalar

### Para Estudios/Equipos
- **Consistencia**: Configuraciones estándar por rol
- **Mantenimiento**: Fácil actualizar sin afectar usuarios
- **Escalabilidad**: Nuevas herramientas se agregan automáticamente

### Para Desarrolladores
- **Modularidad**: Código más organizado
- **Debugging**: Fácil identificar problemas de carga
- **Mantenibilidad**: Cambios centralizados
- **Compatibilidad**: Sistema backward-compatible

## 🔧 Casos de Uso Comunes

### Artista de Rotoscopia
```ini
[Tools]
; Solo herramientas de roto
Build_Roto_BlurMask = True
Rotate_Commands = True
; Deshabilitar otras herramientas
Media_Manager = False
Color_Space_Favs = False
; ... etc
```

### Artista Minimalista
```ini
[Tools]
; Configuración básica
CopyCat_Cleaner = True
Read_From_Write = True
Viewer_Rec709 = True
; Deshabilitar comandos complejos
Rotate_Commands = False
Snapshot_Tools = False
Select_Nodes = False
Easy_Navigate = False
```

### Artista de Revisión
```ini
[Tools]
; Solo herramientas de revisión y comparación
Viewer_Rec709 = True
Snapshot_Tools = True
Color_Space_Favs = True
; Deshabilitar herramientas de edición compleja
Build_Iteration = False
Build_Roto_BlurMask = False
Select_Nodes = False
```

### Artista de Compositing
```ini
[Tools]
; Herramientas de composición
Build_Merge_SwitchOps = True
Build_Grade = True
Build_Grade_Highlights = True
; Deshabilitar otras
; ... etc
```

### Pipeline TD
```ini
[Tools]
; Todas las herramientas disponibles
Media_Manager = True
Media_Path_Replacer = True
CopyCat_Cleaner = True
; ... todas en True
```

## ⚠️ Notas Importantes

### Compatibilidad
- Si no existe el archivo .ini, **todas las herramientas se habilitan por defecto**
- Valores no reconocidos se tratan como `True`
- El sistema es completamente backward-compatible

### Troubleshooting
- **Herramienta no aparece**: Verificar que esté en `True` en el .ini
- **Error al cargar**: Revisar sintaxis del archivo .ini
- **Cambios no aplican**: Reiniciar Nuke completamente

### Archivos de Configuración
- **Usuario**: `~/.nuke/_LGA_ToolPack_Enabled.ini` - **Pisa** la configuración del paquete
- **Paquete**: `LGA_ToolPack/_LGA_ToolPack_Enabled.ini` - Valores por defecto

## 🎨 Ejemplos Avanzados

### Configuración por Entorno de Producción
```ini
[Tools]
; Para producciones VFX complejas
Build_Iteration = True
Build_Roto_BlurMask = True
Channels_Cycle = True
Channel_HotBox = True

; Deshabilitar herramientas básicas
FR_Read_to_Project = False
FR_Read_to_Project_Res = False
```

### Configuración Minimalista
```ini
[Tools]
; Solo lo esencial
CopyCat_Cleaner = True
Read_From_Write = True
Write_Presets = True

; Todo lo demás deshabilitado
Media_Manager = False
Color_Space_Favs = False
; ... etc = False
```

## 🔄 Actualizaciones y Nuevas Herramientas

Cuando se actualiza el LGA ToolPack:

1. **Nuevas herramientas**: Se agregan automáticamente con `True` por defecto
2. **Configuración existente**: Se mantiene sin cambios
3. **Compatibilidad**: Nunca se pierden configuraciones personalizadas

## 📞 Soporte

Si tienes problemas con el sistema de configuración:

1. Verifica la sintaxis del archivo .ini
2. Asegúrate de que Nuke se reinició completamente
3. Revisa la consola de Nuke por mensajes de warning
4. Consulta esta documentación

---

**Versión**: LGA ToolPack v2.43
**Última actualización**: $(date)
**Autor**: Sistema de configuración automática
