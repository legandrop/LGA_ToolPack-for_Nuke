> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_RnW_ColorSpace_Favs

Herramienta para aplicar rápidamente espacios de color favoritos a nodos Read/Write seleccionados en Nuke.

## Flujo
- Lee `LGA_RnW_ColorSpace_Favs.ini` (se copia a `%APPDATA%/LGA/ToolPack/ColorSpace_Favs.ini` la primera vez).
- Muestra una tabla con los favoritos listados en la sección `[ColorSpaces]`.
- Al hacer clic en un favorito aplica el valor al knob `colorspace` de todos los Reads/Writes seleccionados y cierra la ventana.

## Compatibilidad OCIO
- La versión **v1.45** detecta el config actual (`root.OCIO_config`).  
- Cuando se ejecuta sobre un proyecto **OCIO 2.x / ACES 1.3+**, los favoritos que aún usan `Output - Rec.709` se remapean automáticamente a `Camera Rec.709`, que es el equivalente válido en esos configs.  
- En proyectos OCIO 1.2 la herramienta aplica los nombres originales sin cambios.
- Si necesitas otros remapeos, basta con añadirlos en el código siguiendo el mismo patrón.
- Botón **Save Current**: copia el `colorspace` del Read/Write seleccionado y lo agrega al archivo INI si no existía, usando el mismo estilo de botón que usábamos en Write Presets.

## Configuración
El archivo `.ini` sólo requiere las claves de cada colorspace; no se guardan valores extra:

```
[ColorSpaces]
Output - Rec.709
ACES - ACEScct
Camera Rec.709
```

Puedes editar el archivo en `%APPDATA%/LGA/ToolPack/ColorSpace_Favs.ini` o en la copia local (`LGA_RnW_ColorSpace_Favs.ini`) si quieres distribuir presets por defecto.
