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

## Próximo criterio acordado

Por ahora todo queda dentro de [DocToMD](/Users/leg4/.nuke/LGA_ToolPack/DocToMD).

Cuando el contenido y el formato estén aprobados, recién ahí se decidirá cómo copiar o adaptar el resultado final a la raíz de [LGA_ToolPack](/Users/leg4/.nuke/LGA_ToolPack).
