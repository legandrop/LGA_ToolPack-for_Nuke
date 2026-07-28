# Reglas de LGA ToolPack

- `AGENTS.md` es la fuente única de verdad para las reglas del repo.
- `CLAUDE.md` y `.cursor/rules/instructions.mdc` son espejos. Al modificar
  cualquiera, sincronizar los tres en la misma pasada. Solo el archivo de Cursor
  puede agregar el frontmatter `alwaysApply: true`.
- Las reglas se mantienen versionadas para que acompañen todos los clones.

## Alcance y arquitectura

- Repo fuente macOS: `~/.nuke/LGA_ToolPack/`.
- Repo fuente Windows: `%USERPROFILE%\\.nuke\\LGA_ToolPack\\`.
- `menu.py` es un wrapper mínimo de compatibilidad de host.
- `LGA_ToolPack_menu.py` contiene la implementación completa del menú.
- `init.py` registra el path `py/` y el callback del Viewer únicamente en hosts
  de composición.
- No mover lógica del pack al `init.py` global de `~/.nuke`.

## Compatibilidad de host

- El pack carga en Nuke, NukeX, Nuke Indie y demás hosts de composición.
- No debe cargar en Hiero ni Nuke Studio.
- Usar el contrato oficial:

```python
if not (nuke.env["hiero"] or nuke.env["studio"]):
    ...
```

- `nuke.env` no es un `dict` normal. No usar
  `nuke.env.get("clave", False)`: su segundo argumento no es un valor default.
- El guard debe ejecutarse antes de importar módulos, registrar callbacks,
  agregar paths runtime o crear menús.

## Versión publicada y changelog

- `VERSION` es la única fuente de verdad de la versión publicada.
- Changelog principal: `docs/ChangeLog.md`.
- Durante desarrollo normal no modificar `VERSION`, la versión del README ni
  ninguna superficie visible de versión.
- El bump real se hace únicamente mediante
  `LGA_Release/_LGA_ReleaseGen-ToolPack.bat`, cuando el usuario lo pide.
- El menú debe leer `VERSION` en runtime; no hardcodear la versión global en
  headers Python ni labels.

Después de cada cambio relevante:

1. Leer `VERSION` y la versión más alta del changelog.
2. Si son iguales, crear una sección nueva con bump `+0.01` solo en changelog.
3. Si el changelog ya está exactamente `+0.01`, agregar la entrada nueva arriba
   de las existentes dentro de esa misma sección.
4. Si la diferencia es otra, detenerse e investigar; no inventar una versión.

- Las entradas son append-only: nunca reescribir una entrada existente.
- Cada entrada termina con una sugerencia breve de commit en castellano entre
  `[ ]` y una línea en blanco.
- Registrar cambios funcionales, fixes, arquitectura, instalación,
  compatibilidad o documentación relevante. Omitir únicamente ajustes triviales
  sin efecto.
- No crear ni subir versiones internas de cada `.py` por rutina. Los headers
  históricos pueden conservarse, pero el historial canónico es el changelog.

## Documentación y código

- Mantener actualizada la documentación relacionada con el cambio.
- Los docs técnicos describen el estado vigente; el historial vive solo en
  `docs/ChangeLog.md`.
- Texto visible de UI: inglés.
- Comentarios, logs de diagnóstico y changelog: castellano.
- Mantener compatibilidad con las versiones de Python incluidas en las versiones
  de Nuke soportadas.
- No importar PySide directamente cuando exista un adapter Qt del pack.
- No bloquear la UI con IO, red o trabajo pesado.

## Verificación

- Para cambios de startup ejecutar `py_compile`, probar la matriz de flags de
  host y, cuando corresponda, validar con Nuke real.
- En terminal mode, `nuke.menu(...)` puede fallar con `not in GUI mode`; eso no
  equivale a un fallo del menú en la aplicación gráfica.
- No compilar: este repo es Python.

## Commits y GitHub

- Nunca hacer commits, tags, pushes o releases automáticamente. Solo cuando el
  usuario lo pida explícitamente.
- Usar exclusivamente la identidad Git de `legandrop`; sin coautores ni footers
  de atribución.
- No mencionar asistentes, agentes o modelos en commits, changelogs, README,
  documentación de producto, issues, PRs, releases, comentarios de código o
  logs visibles. Las reglas internas son la única excepción necesaria.
