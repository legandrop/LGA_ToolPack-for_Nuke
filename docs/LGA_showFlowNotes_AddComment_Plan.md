> **Regla de documentacion**: este archivo describe el estado actual del codigo y el plan tecnico de implementacion. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_showFlowNotes - Plan tecnico Add Comment oculto

## 1. Objetivo

Implementar en `LGA_showFlowNotes` una funcion oculta para usuarios reviewers: agregar un boton `Add Comment` en el header de cada version, abrir un popover de comentario, enviar la nota a Flow, adjuntar imagenes opcionales, insertar la nota en la DB local de PipeSync y refrescar el popover de notas.

Esta funcion no debe documentarse en el `README.md` publico del ToolPack ni agregarse al changelog/header visible del script, porque no es una funcionalidad pensada para artistas.

## 2. Comportamiento esperado

1. `LGA_showFlowNotes.py` lee el shot desde el nombre del script abierto en Nuke.
2. La task se infiere desde el nombre:
   - si aparece `_roto_`, usa `roto`;
   - si aparece `_cleanup_`, usa `cleanup`;
   - en cualquier otro caso, usa `comp`.
3. El popover muestra versiones y notas desde la DB local de PipeSync.
4. Si el usuario actual es reviewer segun la misma logica de PipeSync C++, cada version muestra un boton `Add Comment`.
5. El boton abre un popover para escribir comentario y elegir adjuntos `.jpg`, `.jpeg` o `.png`.
6. Al enviar:
   - crea una entidad `Note` en Flow vinculada a la `Version`;
   - sube los adjuntos a la `Note`;
   - inserta la nota en `version_notes` de la DB local;
   - refresca la UI para que la nota nueva aparezca sin reiniciar Nuke.

## 3. Decision sobre reviewers

La implementacion debe replicar el comportamiento del C++ de PipeSync:

- El boton `Add Comment` se habilita por rol interno `SpecialUsers::Reviewer`.
- Ese rol se determina desde el login de Flow del usuario.
- No se debe usar `Flow.PermissionGroup` para decidir si aparece el boton.

Motivo: en PipeSync C++ `PermissionGroup` se lee, pero no controla el boton. El boton usa:

```cpp
QString flowLogin = SecureConfig::getInstance().getFlowLogin();
bool isReviewer = SpecialUsers::getRolesForUser(flowLogin).contains(SpecialUsers::Reviewer);
```

Para paridad con PipeSync, el ToolPack debe tener la misma lista de usuarios reviewers o una funcion equivalente.

Python no puede consultar directamente el `QMap` hardcodeado dentro del binario C++ de PipeSync. La forma practica para `v1.01` es copiar esa lista en el helper Python y documentar que debe mantenerse sincronizada con `SpecialUsers.cpp`. Una alternativa mas limpia a futuro seria mover esos roles a un archivo compartido o a una tabla/config comun que lean tanto C++ como Python, pero hoy esa fuente compartida no existe.

La config segura del usuario guarda `Flow.Login` y `Flow.PermissionGroup`, entre otros valores. No guarda el rol interno `SpecialUsers::Reviewer`.

## 4. Archivos a modificar o crear

### Script principal

`C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_showFlowNotes.py`

Responsabilidades:

- mantener la UI principal del popover de notas;
- cargar mas metadata desde la DB:
  - `project_sg_id`;
  - `task` local DB id;
  - `version` local DB id;
  - `version_sg_id`;
- mostrar el boton `Add Comment` solo si el helper indica que el usuario es reviewer;
- abrir el popover de comentario;
- refrescar los datos luego de insertar la nota.

### Helper nuevo

`C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_showFlowNotes_AddComment.py`

Responsabilidades propuestas:

- `is_current_user_reviewer(db_path)`: obtiene el login actual y evalua la lista de reviewers de PipeSync.
- `get_current_user(db_path)`: lee `user_id`, `user_login` y `user_name` desde `app_settings`.
- `add_comment_to_flow(project_id, version_sg_id, user_id, content, attachment_paths, progress_callback=None)`: crea la `Note` en Flow y sube adjuntos.
- `insert_local_comment(db_path, version_db_id, version_sg_id, note_sg_id, content, author_name, attachment_paths, created_on=None)`: inserta la nota en `version_notes`.

Este helper debe usar el `shotgun_api3` que ya existe dentro del ToolPack.

### API Flow local

`C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\shotgun_api3`

Uso esperado:

- importar `shotgun_api3` desde el path local del ToolPack;
- seguir el patron ya usado por `LGA_showInlFlow.py`.

### Secure config

`C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\SecureConfig_Reader.py`

Uso esperado:

- copiar o reutilizar la funcion estable que obtiene credenciales de Flow;
- evitar duplicar comportamiento si el import compartido funciona correctamente desde Nuke.

### DB local de PipeSync usada por ToolPack

`C:\Portable\LGA\PipeSync\cache\pipesync.db`

Tablas relevantes:

- `app_settings`: usuario actual (`user_id`, `user_login`, `user_name`);
- `projects`: `project_sg_id`;
- `tasks`: task local y relacion con shot;
- `versions`: version local DB id, `version_sg_id`, numero, descripcion, autor, fecha;
- `version_notes`: notas locales, links y adjuntos.

## 5. Formato de insercion local

La insercion local debe copiar el comportamiento de PipeSync C++:

```sql
INSERT INTO version_notes
  (version_id, note_sg_id, content, created_by, created_on, from_playlist,
   playlist_name, note_links, attachment_info, local_attachment_paths)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

Valores:

- `version_id`: id local de `versions.id`;
- `note_sg_id`: id de la `Note` creada en Flow;
- `content`: comentario escrito;
- `created_by`: `user_name` de `app_settings` o fallback al login;
- `created_on`: fecha/hora actual;
- `from_playlist`: `false`;
- `playlist_name`: string vacio;
- `note_links`: JSON compacto con la `Version`, por ejemplo `[{"type":"Version","id":1234}]`;
- `attachment_info`: JSON compacto con archivos locales seleccionados;
- `local_attachment_paths`: rutas de adjuntos separadas por `;`.

## 6. UI del popover Add Comment

La UI debe copiar la intencion del C++:

- campo multilinea `Comentario:`;
- selector de adjuntos limitado a `.jpg`, `.jpeg`, `.png`;
- evitar adjuntos duplicados;
- boton `Add Comment`;
- atajo `Ctrl+Enter` para enviar;
- `Escape` para cerrar;
- cierre automatico luego de exito;
- no cerrar por click accidental fuera del popover si se implementa como dialogo modal.

## 7. Envio a Flow

Debe copiarse la funcion ya probada de PipeSync:

`C:\Portable\LGA_PipeSync_2\py_scr\add_version_comment_to_flow.py`

Comportamiento a replicar:

1. leer credenciales de Flow;
2. crear `Note` con:
   - `project`: `Project` con `project_sg_id`;
   - `content`: comentario;
   - `user`: `HumanUser` con `user_id`;
   - `note_links`: `Version` con `version_sg_id`;
3. subir cada adjunto con `sg.upload("Note", note_id, path)`;
4. devolver el `note_id`.

## 8. Cuidado tecnico

- No bloquear la UI de Nuke durante el envio a Flow. PipeSync C++ usa `QProcess`; en Nuke conviene usar un worker con `QThread` o `threading.Thread` y reportar resultado a Qt.
- Si faltan `project_sg_id`, `version_sg_id`, `version_db_id` o `user_id`, el boton debe fallar con un mensaje claro y no intentar escribir en Flow.
- Si el usuario no es reviewer, no se muestra el boton.
- Si Flow falla pero la DB local no fue escrita, no debe quedar una nota local falsa.
- La DB local se escribe solo despues de recibir `note_sg_id` valido desde Flow.

## 9. Validacion

Validacion minima:

```powershell
python -m py_compile .\LGA_ToolPack\py\LGA_showFlowNotes.py .\LGA_ToolPack\py\LGA_showFlowNotes_AddComment.py
```

Validacion manual en Nuke:

1. abrir un script con nombre de shot valido;
2. ejecutar `Show Flow Notes`;
3. confirmar que un usuario reviewer ve `Add Comment`;
4. confirmar que un usuario no reviewer no ve `Add Comment`;
5. enviar comentario sin adjuntos;
6. enviar comentario con `.jpg` o `.png`;
7. confirmar que la nota aparece en Flow;
8. confirmar que la nota se inserta en `version_notes`;
9. confirmar que la UI se refresca.

## 10. Referencias tecnicas

### ToolPack

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_showFlowNotes.py`
  - `ShotGridManager.find_shot`
  - `FlowNotesPopover`
  - `NukeOperations.process_current_script`
  - `main`
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_showFlowNotes_AddComment.py`
  - helper nuevo planificado
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_showInlFlow.py`
  - patron de import de `shotgun_api3`
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\shotgun_api3`
  - API local de Flow/ShotGrid

### PipeSync C++

- `C:\Portable\LGA_PipeSync_2\Docs\Doc_Flow_VersionNotes.md`
  - seccion `Boton Add Comment para Reviewers`
- `C:\Portable\LGA_PipeSync_2\src\features\shots\components\FlowNotesPopover.cpp`
  - `FlowNotesPopover::fetchVersionDataFromDB`
  - `FlowNotesPopover::updateUIWithVersionData`
  - uso de `SpecialUsers::getRolesForUser`
- `C:\Portable\LGA_PipeSync_2\include\pipesync\FlowNotesPopover.h`
  - `VersionInfo`
- `C:\Portable\LGA_PipeSync_2\src\features\shots\components\AddVersionCommentPopover.cpp`
  - `AddVersionCommentPopover::setVersionInfo`
  - `AddVersionCommentPopover::submitComment`
  - `AddVersionCommentPopover::insertLocalComment`
  - `AddVersionCommentPopover::onAttachmentButtonClicked`
- `C:\Portable\LGA_PipeSync_2\include\pipesync\AddVersionCommentPopover.h`
  - interfaz del popover de comentario
- `C:\Portable\LGA_PipeSync_2\src\services\VersionCommentService.cpp`
  - `VersionCommentService::addCommentToFlow`
  - parseo de `NOTE_SG_ID`
- `C:\Portable\LGA_PipeSync_2\py_scr\add_version_comment_to_flow.py`
  - `create_note`
  - `upload_attachments`
  - `main`
- `C:\Portable\LGA_PipeSync_2\src\core\config\SpecialUsers.cpp`
  - `SpecialUsers::getRolesForUser`
- `C:\Portable\LGA_PipeSync_2\src\core\config\SecureConfig.cpp`
  - `SecureConfig::getFlowLogin`
  - `SecureConfig::getFlowPermissionGroup`

### Configuracion y DB

- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\SecureConfig_Reader.py`
  - `read_secure_config`
  - `get_flow_credentials`
- `C:\Portable\LGA\PipeSync\cache\pipesync.db`
  - DB local real que debe leer/escribir el ToolPack
