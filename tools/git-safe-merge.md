# git-safe-merge

Herramienta para hacer merge de la branch actual hacia otra branch de destino de forma más segura, con chequeos previos y confirmación manual.

## Archivos

- [git-safe-merge.bat](/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.bat): lanzador para Windows.
- [git-safe-merge.ps1](/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.ps1): implementación principal en PowerShell.
- [git-safe-merge.sh](/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.sh): implementación para macOS/Linux usando shell.

## Qué hace

Antes de mergear:

- verifica que estés dentro de un repo git
- exige working tree limpio
- aborta si hay merge o rebase en progreso
- detecta la branch actual
- hace `fetch origin`
- verifica que tu branch actual no esté behind respecto de remoto
- verifica que la branch destino local no esté behind respecto de remoto
- simula el merge para detectar conflictos
- muestra resumen de commits y `diff --stat`
- pide confirmación manual

Si confirmás:

- cambia a la branch destino
- mergea la branch actual
- hace push a remoto
- vuelve a la branch original

## Uso en mac

Desde terminal:

```bash
/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.sh
```

Eso mergea la branch actual hacia `main`.

Para usar otra branch destino:

```bash
/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.sh develop
```

## Uso en Windows

Se puede ejecutar:

- [git-safe-merge.bat](/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.bat)
- o directamente [git-safe-merge.ps1](/Users/leg4/.nuke/LGA_ToolPack/tools/git-safe-merge.ps1)

El `.bat` copia el `.ps1` a `%TEMP%` antes de ejecutarlo para que el script sobreviva a un `checkout` durante el proceso.

## Nota

La herramienta no reemplaza revisar qué estás mergeando. Su objetivo es evitar errores operativos básicos antes de tocar `main` o la branch destino.
