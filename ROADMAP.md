# Roadmap

Pendientes conocidos. No es un changelog: aca va lo que falta hacer, no lo que
ya se hizo. Al completar un item se borra de aca y se registra en el changelog.

---

## UI

### Rutas coloreadas: anclar el color en el shotname

Regla nueva (ver `Docu_UI_Style.md` de LGA_ToolPack y el AGENTS.md de cada
repo): cuando en una ruta se puede detectar un nombre de shot, todos los
segmentos ANTERIORES al shot van en un solo color (el de parte comun,
`PATH_COMMON`) y la paleta por nivel arranca recien en el shotname. Colorear
por nivel desde la raiz queda solo para rutas sin shot detectable.

Hay que rechequear y arreglar:

- `colorize_path()` ya quedo anclado al shotname en las cuatro copias del
  modulo de estilo (v1.22). Falta `colorize_path_pair()`, que tras la
  parte comun del par sigue coloreando por nivel sin mirar el shot.
- Todas las ventanas del repo que muestren rutas, revisarlas contra la regla.

Donde mirar ejemplos de como detectar el shot en una ruta:

- HieroTools `LGA_NKS_Shared/LGA_NKS_Flow_NamingUtils.py`:
  `extract_shot_code_from_path()` e `is_shot_folder_name()` (naming
  PROYECTO_SEQ_SHOT_VENDOR validado contra la DB de PipeSync).
- HieroTools `LGA_NKS_Edit_Panel_py/LGA_NKS_ApplyAMF.py`:
  `resolve_shot_dir()` — fallback estructural: subir directorios hasta el que
  contenga `_input`.
