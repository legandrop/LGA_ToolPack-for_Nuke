<p>
  <img src="Doc_Media/image1.png" alt="LGA Tool Pack logo" width="56" height="56" align="left" style="margin-right:8px;">
  <span style="font-size:1.6em;font-weight:700;line-height:1;">LGA TOOL PACK</span><br>
  <span style="font-style:italic;line-height:1;">Lega | v2.51</span><br>
</p>
<br clear="left">





## Instalación

- Copiar la carpeta **LGA_ToolPack** que contiene todos los archivos del ToolPack a **%USERPROFILE%/.nuke**.<br> Debería quedar así:
   ```
   .nuke/
   └─ LGA_ToolPack/
      ├─ menu.py
      ├─ py/
      └─ ...
  ```

- Con un editor de texto, agregar esta línea de código al archivo
  **init.py** que está dentro de la carpeta **.nuke**:

  ```
  nuke.pluginAddPath('./LGA_ToolPack')
  ```

- El ToolPack permite **activar/desactivar** herramientas editando el archivo **\_LGA_ToolPack_Enabled.ini**<br>
  Por defecto todas las herramientas están en **True**. Las que se cambian a **False**, se ocultan y evitan cargarse.<br>
  Para conservar la configuración en futuras actualizaciones, se puede copiar el archivo **.ini** a la carpeta **\~/.nuke/**

<br><br>
<img src="Doc_Media/read_n_write.svg" alt="READ n WRITE" width="262" height="33">

## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Media manager v1.6 | Lega

Para revisar y ordenar toda la media del proyecto de forma rápida.<br>
Al ejecutarlo escanea toda la media de la carpeta del shot y todas las rutas de los nodos Read del script, mostrando el estado de cada archivo como OK, Offline, Outside o Unused para poder decidir si relinkear, copiar o borrar.<br><br>
![](Doc_Media/image3.png)



**Funciones**
- <strong>Go to read:</strong> (Alt+G) Muestra en el node graph el read que contiene a la media seleccionada.
- <strong>Explorer:</strong> (Alt+E) Abre la media en Windows Explorer.
- <strong>Relink:</strong> (Alt+L) Abre una ventana para elegir una ubicación para buscar un archivo que está marcado como offline. Busca en las carpeta y subcarpetas hasta encontrar un match, y cambia la ruta del Read por la ruta encontrada.
- <strong>Delete:</strong> Borra los archivos seleccionados. Funciona con selección múltiple de filas.
- <strong>Copy to:</strong> Copia la media seleccionada a el destino elegido y cambia la ruta del Read por la ruta donde fue copiado. Esta función sólo se habilita para archivos marcados como Outside.
<br><br>

**Opciones disponibles en los Settings**

- <strong>Shot folder depth:</strong> Determina cuántos niveles de carpetas se deben retroceder desde la carpeta donde está ubicado el script (proyecto) hasta la carpeta principal del shot. <br>Si por ejemplo el shot está en T:/Client/Film/Shot/Comp/Project/e101s005.nk entonces para retroceder hasta el Shot folder tenemos que retroceder 3 niveles desde Project (1), Comp (2), Shot (3).
- <strong>Copy to:</strong> Determina las carpetas para el menú “Copy to”. El Name es el que aparecerá en el menú. Usando el signo & se agrega un shortcut para esa acción. La ruta se comienza a formar desde la carpeta del shot.
<br><br>

![](Doc_Media/image29.png)
<br><br>
<img src="Doc_Media/media_manager_shortcut.svg" alt="Media manager shortcut" width="135" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Media path replacer v1.6 | Lega

Para cuando hay missing media porque se cambió la ubicación del proyecto y su media.<br>
Permite buscar y reemplazar rutas en los nodos Read y Write. Da la opción de filtrar listas, incluir sólo nodos Read o Write, y tiene un sistema de presets para guardar y cargar configuraciones frecuentes.<br>
![](Doc_Media/image17.png)<br>
Útil para actualizar rutas de archivos cuando se mueven proyectos a otras carpetas o discos.
<br><br>
<img src="Doc_Media/media_path_replacer_shortcut.svg" alt="Media path replacer shortcut" width="195" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Read from Write v2.3 | Fredrik Averpil

[https://www.nukepedia.com/python/misc/readfromwrite](https://www.nukepedia.com/python/misc/readfromwrite)<br>
Genera un nodo Read a partir de la ruta y archivo del nodo Write seleccionado.
<br><br>
<img src="Doc_Media/read_from_write_shortcut.svg" alt="Read from Write shortcut" width="150" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Write Presets v1.9 | Lega

Para crear nodos Write con configuraciones predefinidas para diferentes tipos de render.<br>
Abre una ventana con opciones de render pre configuradas que se cargan desde un archivo .ini. Permite crear Writes basados en el nombre del script o en el nombre del nodo Read más alto. Según la configuración, puede abrir un diálogo para nombrar el render y crear automáticamente un backdrop con Write y Switch. Los presets incluyen configuraciones específicas para diferentes formatos (mov, tiff, exr) con parámetros optimizados para cada caso.<br>
![](Doc_Media/image6.png)
![](Doc_Media/image19.png)

También incluye un botón para poder previsualizar un path TCL como una ruta absoluta, seleccionando primero el nodo Write a inspeccionar:<br>
![](Doc_Media/image4.png)
![](Doc_Media/image22.png)
<br><br>
<img src="Doc_Media/write_presets_shortcut.svg" alt="Write Presets shortcut" width="150" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Write focus v1.0 | Lega

Para ir rápidamente al nodo Wirte principal.<br>
Busca un nodo Write con un nombre definido en los settings del ToolPack, lo pone en foco y lo abre en el panel de propiedades.
<br><br>
<img src="Doc_Media/write_focus_shortcut.svg" alt="Write focus shortcut" width="225" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Write send mail v1.0 | Lega

Útil para renders largos, permite mandar un mail cuando termina el render.<br>
Agrega a los nodos Write seleccionados un checkbox para enviar mail. También lo agrega a cualquier nuevo nodo Write creado desde que está instalado este script.<br>
![](Doc_Media/image25.png)<br>
La información para enviar el mail se debe completar en los settings del ToolPack.<br>
Funciona en conjunto con la herramienta Render Complete (a continuación).
<br><br>
<img src="Doc_Media/write_send_mail_shortcut.svg" alt="Write send mail shortcut" width="205" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Render complete v1.1 | Lega

Ejecuta las acciones siguientes cuando termina el render:

- Reproduce un sonido por defecto es un wav llamado LGA_Render_Complete.wav que está dentro de la carpeta LGA_ToolPack. Puede ser reemplazado por cualquier otro wav o deshabilitado desde los settings del ToolPack
- Calcula la duración al finalizar el render y la agrega en un knob con esa información en el tab User del nodo Write.
- Envía un email con los detalles del render si se ha creado un checkbox usando la herramienta Write send mail y si ese checkbox está activado.

<br><br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Show in Explorer v1.0 | Lega

Revela la ubicación del archivo de un nodo Read o Write seleccionado en el Explorador de Windows. Si no hay ningún nodo seleccionado, revela la ubicación del script/proyecto actual.
<br><br>
<img src="Doc_Media/show_in_explorer_shortcut.svg" alt="Show in Explorer shortcut" width="150" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> Show in Flow v2.0 - 2024 | Lega

Abre la URL, revela en el internet browser la ubicación de la task comp del shot que pertenece al script/proyecto actual. Se puede elegir si hacerlo desde el browser por defecto o desde uno específico.<br>
Para el login completar la información en los settings del ToolPack.
<br><br>
<img src="Doc_Media/show_in_flow_shortcut.svg" alt="Show in Flow shortcut" width="205" height="43">

<br>



## <img src="Doc_Media/image7.png" alt="" width="6" height="16" style="margin-right:3px;"> RnW ColorSpace favs v1.1 | Lega

Para cambiar rapidamente el espacio de color de un Read, Write, etc.<br>
Abre una ventana con una lista de espacios de color que se pueden aplicar sobre todos los nodos Read y/o Write seleccionados.<br>
![](Doc_Media/image31.png)<br>
Esta lista se puede editar en los settings del ToolPack.
<br><br>
<img src="Doc_Media/rnw_colorspace_favs_shortcut.svg" alt="RnW ColorSpace favs shortcut" width="150" height="43">

<br>



<img src="Doc_Media/frame_range.svg" alt="FRAME RANGE" width="245" height="33">

## <img src="Doc_Media/image8.png" alt="" width="6" height="16" style="margin-right:3px;"> Frame range | Read to Project v1.0 | Lega</strong>

Útil para cuando se empieza un proyecto nuevo y se quiere usar el frame range de un nodo Read en los settings del proyecto.
<br><br>
<img src="Doc_Media/frame_range_read_to_project_shortcut.svg" alt="Frame range Read to Project shortcut" width="150" height="43">

<br>



## <img src="Doc_Media/image8.png" alt="" width="6" height="16" style="margin-right:3px;"> Frame range | Read to Project (+Res) v1.0 | Lega

Igual que el anterior, pero además de copiar el frame range del Read, también se copia la resolución a los settings del proyecto.
<br><br>
<img src="Doc_Media/frame_range_read_to_project_res_shortcut.svg" alt="Frame range Read to Project res shortcut" width="205" height="43">

<br><br>



<img src="Doc_Media/rotate_transform.svg" alt="ROTATE TRANSFORM" width="335" height="33">

## <img src="Doc_Media/image21.png" alt="" width="6" height="16" style="margin-right:3px;"> Rotate Transform v1.0 | Lega

Cambia los valores de rotación de los nodos Transform seleccionados.<br>
Shortcuts (usando las teclas / y * del teclado numérico):

- Ctrl + * gira 0.1 grados hacia la derecha
- Ctrl + shift + * gira 0.1 grados hacia la derecha
- Ctrl + / gira 0.1 grados hacia la izquierda
- Ctrl + shift + / gira 0.1 grados hacia la izquierda

<br><br>



<img src="Doc_Media/node_builds.svg" alt="NODE BUILDS" width="235" height="33">

Esta sección es para armar setups de nodos que se usan repetidamente usando shortcuts.<br>
Similar al uso de toolSets, pero más ágil y con más posibilidades.



## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Build Iteration v1.1 | Lega

![](Doc_Media/image14.png)
<br><br>
<img src="Doc_Media/build_iteration_shortcut.svg" alt="Build Iteration shortcut" width="135" height="43">

<br>



## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Build Roto Blur in mask input v1.1 | Lega

Agrega un nodo Roto y un Blur en el input mask del nodo seleccionado.<br>
![](Doc_Media/image32.png)
![](Doc_Media/image33.png)
<br><br>
<img src="Doc_Media/build_roto_blur_shortcut.svg" alt="Build Roto Blur shortcut" width="135" height="43">

<br>



## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Build Merge | Switch Merge operations v1.31 | Lega

Si NO hay un nodo Merge seleccionado, crea un nodo Merge con operación en Mask y bbx en ‘A’, y en el input A suma un nodo Roto y un Blur.<br>
![](Doc_Media/image16.png)<br>
Si en cambio se ejecuta con un nodo Merge seleccionado, cambia sus operaciones y va rotando entre 'over' con bbox 'B', 'mask' con bbox 'A' y 'stencil' con bbox 'B'.
<br><br>
<img src="Doc_Media/build_merge_shortcut.svg" alt="Build Merge shortcut" width="150" height="43">

<br>




## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Build Grade v1.1 | Lega

Crea un nodo Grade y en el input Mask suma un nodo Roto y un Blur.<br>
![](Doc_Media/image24.png)
<br><br>
<img src="Doc_Media/build_grade_shortcut.svg" alt="Build Grade shortcut" width="150" height="43">

<br>




## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Build Grade Highlights v1.1 | Lega

Crea un nodo Grade y en el input Mask suma un nodo Keyer que sale de la rama del grade y un Shuffle para poder evaluar el canal alpha con el viewer en RGB.<br>
![](Doc_Media/image28.png)
<br><br>
<img src="Doc_Media/build_grade_highlights_shortcut.svg" alt="Build Grade Highlights shortcut" width="205" height="43">

<br><br>




<img src="Doc_Media/knobs.svg" alt="KNOBS" width="120" height="33">



## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Channels Cycle v1.1 | Lega

Cambia el valor del knob 'channels' de un nodo seleccionado. Rota el valor entre 'rgb', 'alpha' y 'rgba'.<br>
![](Doc_Media/image12.png)
<br><br>
<img src="Doc_Media/channels_cycle_shortcut.svg" alt="Channels Cycle shortcut" width="205" height="43">

<br>



## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Disable A/B v1.0 | Lega

Útil para comparar rápidamente dos grupos de nodos (grupo A vs grupo B) o dos nodos iguales con distintos valores.<br>
Crea un nodo que, al habilitarlo o deshabilitarlo (shortcut D), actúa como un switch global entre un grupo y otro.<br>
Ideal para comparar, por ejemplo, dos Grades, o un blur vs un defocus, o también para crear un master switch que deshabilite nodos pesados durante el trabajo y se puedan volver a habilitar desde un solo nodo antes del render.

**Modo de uso**

Seleccionar todos los nodos que pertenecerán a ambos grupos y ejecutar la herramienta (Shift+D)<br>
Abre una ventana que muestra una lista con todos los nodos seleccionados, usando el color de cada uno, y permite seleccionar si pertenecen al grupo A o grupo B.<br>
Luego linkea el knob Disable de los nodos seleccionados a un nodo master llamado Disable_A_B para facilitar el cambio de un grupo a otro.<br>
Una vez creado el grupo, si se ejecuta Shift+D seleccionado en nodo master Disable_A_B se desconectarán y volverá todo a su estado inicial.<br>
![](Doc_Media/image23.png)
![](Doc_Media/image11.png)
<br><br>
<img src="Doc_Media/disable_ab_shortcut.svg" alt="Disable A B shortcut" width="150" height="43">

<br>




## <img src="Doc_Media/image5.png" alt="" width="6" height="16" style="margin-right:3px;"> Channel Hotbox v2.0 | Falk Hofmann

[http://www.nukepedia.com/python/ui/channel-hotbox](http://www.nukepedia.com/python/ui/channel-hotbox)<br>
Abre una GUI que permite cambiar fácilmente los canales actualmente disponibles del viewer (rgba, depth, motion, AOVs, etc, evitando el menú desplegable, page up/down.<br>
También permite mostrar, shufflear o aplicar un grade a los canales disponibles en el nodo al que está conectado el Viewer actual.<br>
![](Doc_Media/image15.png)


**Shortcuts**
Shift + H Abre la GUI<br>
Shortcuts con la GUI abierta:
- Click Cambia el visor al canal seleccionado.
- Shift+Click Shufflea todos los canales seleccionados.
- Ctrl+Click Crea un nodo Grade con el canal configurado al seleccionado.
- Alt Cambia el visor de vuelta a RGBA.

<br><br>



<img src="Doc_Media/va.svg" alt="VA" width="55" height="33">

## <img src="Doc_Media/image13.png" alt="" width="6" height="16" style="margin-right:3px;"> Viewer Rec709 v1.0 | Lega</strong>

Cambia el viewer a Rec709.
<br><br>
<img src="Doc_Media/viewer_rec709_shortcut.svg" alt="Viewer Rec709 shortcut" width="150" height="43">

<br>




## <img src="Doc_Media/image13.png" alt="" width="6" height="16" style="margin-right:3px;"> Take/Show Snapshot v1.0 | Lega</strong>

Take: Toma un snapshot (jpg), lo guarda en la carpeta de archivos temporales, y también lo guarda en una galería.<br>
Show: Muestra el último snapshot tomado, el de la carpeta de archivos temporales.<br>
Además de los shortcuts en el menú, también se agregan estos botones al viewer:<br>
![](Doc_Media/image9.png)

El último botón abre una galería con todos los snapshots que se guardan, separados por proyecto:<br>
![](Doc_Media/image27.png)
<br><br>
<img src="Doc_Media/take_show_snapshot_shortcut.svg" alt="Take Show Snapshot shortcuts" width="330" height="59">

<br>




## <img src="Doc_Media/image13.png" alt="" width="6" height="16" style="margin-right:3px;"> Reset workspace v1.0 | Checho

Reinicia el workspace.
<br><br>
<img src="Doc_Media/reset_workspace_shortcut.svg" alt="Reset workspace shortcut" width="195" height="43"><br>

<br>




## <img src="Doc_Media/image13.png" alt="" width="6" height="16" style="margin-right:3px;"> Restart NukeX v1.12 | Lega</strong>

Reinicia NukeX. Antes de hacerlo espera a que se guarde o no el proyecto actual, busca cual es la versión actual de Nuke abierta y lo reinicia usando la misma consola que se estaba usando.<br>
Útil cuando borrar la caché no es suficiente para que Nuke vuelva a funcionar correctamente y es necesario cerrarlo y volver a abrirlo.
<br><br>
<img src="Doc_Media/restart_nukex_shortcut.svg" alt="Restart NukeX shortcut" width="225" height="43"><br>
