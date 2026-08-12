> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Activar y desactivar herramientas — LGA ToolPack

Casi cada herramienta del pack se puede ocultar del menu. Una herramienta
apagada no se muestra y ademas no se importa, asi que tampoco cuesta tiempo
de arranque.

Las dos excepciones son `Settings` y `Enable Tools`: son los accesos a la
configuracion del pack y estan siempre. No figuran en el manifiesto.

## Para el usuario

Menu **TP > Enable Tools**. Se destilda lo que no se quiere y se guarda.
Los cambios se ven **al reiniciar Nuke**: el menu se arma una sola vez, al
inicio, y las tools apagadas no llegan a registrarse.

La eleccion se guarda **fuera del pack**:

| Sistema | Archivo |
|---|---|
| Windows | `%APPDATA%\LGA\ToolPack\Enabled.ini` |
| macOS | `~/Library/Application Support/LGA/ToolPack/Enabled.ini` |

Para volver a los valores de fabrica: boton **Reset** y despues **Save**.
Borrar el archivo a mano puede no alcanzar: si quedo un ini viejo en
`.nuke` —que por diseno no se borra nunca— el arranque siguiente lo
vuelve a migrar.

## Por que vive afuera del pack

El instalador renombra la carpeta del pack a `LGA_ToolPack_backup` y copia la
version nueva limpia. Todo lo que viva adentro se pierde en cada update. Antes
el estado estaba ahi, y por eso se perdia.

## Las dos piezas

**`Enabled.default.ini`** (dentro del pack) es el manifiesto: la lista canonica de
tools con su valor de fabrica, agrupadas por los marcadores `; === X ===` que
el panel usa como titulos. Viaja con el pack y el instalador lo pisa en cada
update, asi que una edicion a mano se pierde ahi. Mientras tanto si aplica:
es la capa base de `load_flags()`, no solo una semilla inicial, asi que
sirve para armar un ZIP pre-configurado. Lo que el usuario haya tocado
desde el panel le gana igual.

**`Enabled.ini`** (carpeta de datos del usuario) guarda **solo los overrides**:
lo que difiere del manifiesto. Un usuario que no cambio nada tiene un archivo
vacio. Eso es lo que hace que agregar o borrar tools entre versiones sea
transparente: las tools nuevas aparecen habilitadas solas y las que ya no
existen desaparecen sin dejar claves muertas.

Precedencia en runtime: manifiesto, y encima el archivo del usuario. Una clave
que no esta en ninguno de los dos se considera habilitada.

## Migracion desde el sistema viejo

La primera vez que arranca, el pack siembra el archivo del usuario juntando lo
que hubiera configurado antes, de menor a mayor prioridad:

1. inis historicos de los packs hermanos — hay tools que cambiaron de pack, y
   quien apago `CopyCat_Cleaner` cuando vivia en LGA_ToolPack tiene que
   seguir viendolo apagado ahora que vive en LGA_ToolPack-B;
2. inis que quedaron dentro de las carpetas `<Pack>_backup`, para quien edito
   el ini adentro del pack;
3. el ini historico de `.nuke`, que es lo que documentaba el PDF viejo.

De los archivos ajenos solo se toman las claves que este pack reconoce.

El ini historico **no se borra ni se renombra nunca**: si alguien revierte a
una version anterior del pack, ese codigo lo vuelve a leer y encuentra su
configuracion.

**Limite conocido:** el rescate desde `<Pack>_backup` depende de que esa
carpeta siga estando. El instalador la borra al empezar la instalacion
siguiente, asi que dos instalaciones seguidas sin abrir Nuke en el medio se la
llevan puesta. Los usuarios cubiertos por el ini de `.nuke` no dependen de
esto.

## Que pasa cuando algo falla

- **Manifiesto ilegible o ausente:** se avisa por `nuke.warning`, el panel
  muestra un error en vez de una grilla vacia y **se bloquea el guardado**. Sin
  manifiesto todo pareceria igual al default y guardar dejaria el archivo del
  usuario vacio, borrandole la configuracion justo cuando cree que la guarda.
- **Archivo del usuario ilegible:** se avisa y se cae a los valores de fabrica.
- **Sin carpeta de datos del sistema:** la config va a
  `<.nuke>/LGA_Settings/ToolPack/Enabled.ini`. No se escribe sobre el ini
  historico, que puede tener comentarios y claves de otros packs.
- **El modulo de config no carga:** el menu se arma igual y con todo visible.
  Es preferible mostrar de mas a dejar al usuario sin herramientas.

## Referencias tecnicas

**`LGA_ToolPack/py/LGA_ToolPack_Enabled.py`**
- `get_user_path()` — resuelve el archivo del usuario, con fallback al `.nuke`.
- `get_nuke_dir()` — el `.nuke` REAL donde quedo instalado el pack; el
  instalador acepta rutas arbitrarias, asi que no se usa el home del usuario.
- `read_defaults()` / `read_default_groups()` — manifiesto y su agrupacion
  para el panel. Las claves salen siempre de `read_defaults()`.
- `load_flags()` / `is_enabled(key)` — estado efectivo, cacheado.
- `write_user_overrides(flags)` — escritura atomica de solo los overrides.
- `ensure_user_ini()` — sembrado one-shot descrito arriba.

**`LGA_ToolPack/py/LGA_ToolPack_EnabledPanel.py`**
- `EnabledPanel` — grilla de checkboxes agrupada como el menu.
- `main()` — abre el panel y lo mantiene vivo.

**`LGA_ToolPack/LGA_ToolPack_menu.py`**
- `is_enabled(key)` / `add_tool(...)` — registran cada tool solo si esta
  habilitada, con import diferido.
- Los comandos de menu `Settings` y `Enable Tools` **no** pasan por
  `is_enabled()`. `Settings` es la configuracion del pack, y `Enable Tools`
  es el unico camino de vuelta si el usuario apaga todo lo demas.

**`Enabled.default.ini`** — manifiesto de tools del pack.
