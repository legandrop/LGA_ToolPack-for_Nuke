# Google Doc a Markdown (LGA ToolPack)

## Objetivo

Dejar documentado el flujo actualizado para convertir el Google Doc de `LGA_ToolPack` a un `README.md` preliminar dentro de `DocToMD`, manteniendo todo el proceso contenido en esta carpeta.

## Estado actual

En esta carpeta ya existen:

- [LGA_ToolPack.docx](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/LGA_ToolPack.docx): export del Google Doc.
- [README.md](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/README.md): primera conversión preliminar a Markdown.
- [convert_docx_to_md.py](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/convert_docx_to_md.py): script usado para generar esa primera versión.
- [media_original](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/media_original): imágenes extraídas del `.docx`.
- [media_converted](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/media_converted): copia de trabajo para las imágenes referenciadas por el `.md`.

## Primer paso

1. Abrir el Google Doc.
2. Exportarlo como `Microsoft Word (.docx)`.
3. Guardarlo en:

`/Users/leg4/.nuke/LGA_ToolPack/DocToMD/LGA_ToolPack.docx`

Ese es el punto de partida del flujo actual.

## Flujo usado esta vez

1. Se partió del archivo [LGA_ToolPack.docx](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/LGA_ToolPack.docx).
2. Se inspeccionó el contenido interno del `.docx` directamente, sin depender de la conversión HTML de macOS.
3. Se extrajeron las imágenes embebidas del documento y se copiaron a dos carpetas:
   - [media_original](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/media_original)
   - [media_converted](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/media_converted)
4. Se recorrió el XML del documento para reconstruir:
   - título
   - versión
   - bloques de instalación
   - secciones
   - herramientas
   - imágenes en su orden aproximado dentro del documento
5. Se generó un Markdown preliminar en [README.md](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/README.md).
6. Se limpiaron los temporales usados durante la exploración para que `DocToMD` quedara sólo con los archivos relevantes.

## Por qué se hizo así

La exportación HTML con `textutil` en macOS conservó bastante bien el texto, pero no preservó las imágenes embebidas dentro del HTML resultante. Por eso el flujo real terminó yendo directo al contenido interno del `.docx`.

Ese enfoque permitió:

- preservar mejor el orden entre texto e imágenes
- extraer toda la media original
- generar una primera versión rápida del `README.md`
- dejar un script repetible para volver a correr la conversión base

## Comando para regenerar la versión actual

```bash
python3 /Users/leg4/.nuke/LGA_ToolPack/DocToMD/convert_docx_to_md.py
```

Esto vuelve a:

- recrear `media_original`
- recrear `media_converted`
- regenerar [README.md](/Users/leg4/.nuke/LGA_ToolPack/DocToMD/README.md)

## Alcance de esta primera conversión

La versión actual del Markdown:

- ya respeta razonablemente la estructura general del documento
- ya incluye títulos, secciones, bloque de instalación, links e imágenes principales
- todavía no aplica una etapa final de limpieza editorial/visual fina
- todavía no está preparada para copiarse directamente a la raíz de `LGA_ToolPack`

## Reglas de estructuración acordadas

Estas reglas ya pasan a formar parte del criterio del `README.md` de `LGA_ToolPack`:

- El encabezado principal debe usar el mismo patrón visual que `LGA_ToolPack-Layout`: bloque HTML con imagen a la izquierda, título a la derecha y `br clear="left"`.
- La sección `Instalación` debe copiar el formato base del README de layout, adaptando solamente el nombre del pack y la línea de `pluginAddPath`.
- Los títulos de sección deben conservar el color del Google Doc.
- Cada tool debe ir como encabezado grande con un icono chico a la izquierda, usando la imagen embebida que traiga el `.docx`.
- Los iconos chicos de tool se están respetando con el tamaño aproximado detectado en el documento: `7x12`.
- Cuando el atajo aparece integrado en el título del Google Doc, debe mantenerse dentro del heading en cursiva.
- Entre tools debe agregarse espacio explícito con `<br><br>`, como en el README de layout, para separar visualmente cada bloque.

## Colores de sección detectados en el docx

- `READ n WRITE`: `#a9ab13`
- `FRAME RANGE`: `#135eab`
- `ROTATE TRANSFORM`: `#914dcb`
- `COPY n PASTE`: `#4dcb9d`
- `NODE BUILDS`: `#cb944d`
- `KNOBS`: `#cb944d`
- `VA`: `#cb4d82`

## Próximo criterio acordado

Por ahora todo queda dentro de [DocToMD](/Users/leg4/.nuke/LGA_ToolPack/DocToMD).

Cuando el contenido y el formato estén aprobados, recién ahí se decidirá cómo copiar o adaptar el resultado final a la raíz de [LGA_ToolPack](/Users/leg4/.nuke/LGA_ToolPack).
