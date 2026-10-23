> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Blur-Fusion v1.00

Estimación del color del frente en bordes semitransparentes (pelo, motion blur) a partir del PLATE y un matte,
sin placa limpia. Es el método de *Approximate Fast Foreground Colour Estimation* (Marco Forte y François Pitié,
ICIP 2021), armado con nodos nativos de Nuke dentro de un Group.

Menú: **TP > NODE BUILDS > Blur-Fusion**, sin atajo. Crea el Group `BlurFusion1` colgado del nodo seleccionado
(input **Source**); sin selección lo deja en el centro de la vista del Node Graph. Se apaga desde Enable Tools con
la clave `Build_Blur_Fusion`.

## Entradas y salida

- **Source** (input 0): el PLATE; se usa su rgb.
- **Matte** (input 1): el matte en su **alpha**. Si no está conectado, se usa el alpha del Source
  (`Switch` con `[exists parent.input1]`). Un matte que viene en rgb (un PNG gris) hay que pasarlo antes a alpha.
- El alpha se recorta a [0, 1].
- Salida: rgb = F premultiplicado por el matte y alpha = matte. Con **premultiply** apagado sale F sin premultiplicar
  (con el matte en el alpha). Fuera del matte (a = 0) la salida premultiplicada es 0, así que lo que valga F ahí no
  importa.
- Todo se calcula en el espacio de trabajo del script (luz lineal en un proyecto normal). La salida queda recortada al
  formato.

## Las dos pasadas

Una pasada, con un blur de caja de ancho r (filtro `box` del Blur):

    F^ = blur(Fsrc · a) / (blur(a) + eps)              color medio del frente cercano
    B^ = blur(Bsrc · (1 − a)) / (blur(1 − a) + eps)    color medio del fondo cercano
    F  = F^ + a · (I − a · F^ − (1 − a) · B^)          corrección por la ecuación de mezcla

- Pasada 1: Fsrc = Bsrc = I (el PLATE), r = **large size** (90 por defecto).
- Pasada 2: Fsrc = F de la pasada 1, Bsrc = B^ de la pasada 1, r = **small size** (6 por defecto).
- La salida es el F de la pasada 2.

Es el mismo esquema que el código de referencia de los autores (repo `Photoroom/fast-foreground-estimation`,
`FB_blur_fusion_foreground_estimator_2`). Diferencias deliberadas:

- **Ancho de la caja.** El Blur box de Nuke de tamaño r es una caja simétrica de ancho r (medio peso en los dos
  extremos); `cv2.blur` con (r, r) es una caja de r píxeles levemente corrida. Los defaults 90 y 6 son los del paper.
- **Bordes del cuadro.** Numerador y denominador se recortan al formato con negro afuera antes del blur, así el
  promedio sigue normalizado junto al borde de la imagen. Por eso el fondo se divide por blur(1 − a) y no por
  1 − blur(a): adentro del cuadro son lo mismo, en el borde sólo el primero es correcto.
- **Recorte de valores.** El código de referencia recorta F a [0, 1] en cada pasada porque trabaja en imágenes de
  display. En lineal los brillos pasan de 1, así que sólo se llevan a cero los negativos (**clamp negatives**,
  prendido por defecto).
- **eps** es el knob **epsilon** (1e-5, como el paper).

El Blur fuerza `quality` por encima del tamaño (`max(15, size + 1)`): con la quality por defecto (15), Nuke calcula
las cajas grandes a menor resolución y deja de ser exacto.

Verificado contra una implementación numpy de las mismas fórmulas (caja simétrica, ceros fuera del cuadro): diferencia
máxima 7e-7 sobre una imagen sintética de 640×400, premultiplicado, sin premultiplicar y con el matte por el input 1.

## Knobs

| Knob | Default | Qué hace |
|---|---|---|
| `large_size` | 90 | Ancho de la caja de la pasada 1. |
| `small_size` | 6 | Ancho de la caja de la pasada 2. |
| `premultiply` | on | Salida premultiplicada por el matte. |
| `clamp_negative` | on | Negativos a cero (no recorta arriba). |
| `epsilon` | 1e-5 | Se suma a los divisores. |
| `version` | — | Texto con la versión de la tool que creó el nodo. |

Los tooltips viven en el diccionario `TOOLTIPS` del módulo, en castellano, para que el paso a bilingüe sea un cambio
de datos.

## Rendimiento

Todo CPU (Blur, Expression, MergeExpression, Copy, Crop, Premult: ningún nodo usa la GPU). En una placa UHD
(3840×2160) en Nuke 17 en modo terminal: unos 0,23 s por cuadro con cajas 90/6 y 0,42 s con 181/13, contra 0,19 s de
un Read + Premult + Write del mismo cuadro.

## Referencias técnicas

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_build_BlurFusion.py`
  - `build_group()`: crea el Group con sus knobs y su grafo interno; no depende de la GUI.
  - `main()`: entrada del menú; conecta el Group al nodo seleccionado (`LGA_ToolPack_Selection.selected_node`).
  - `_add_knobs()`: knobs del Group y texto de versión (`_tool_version()`, leída del header).
  - `_build_internals()`: Inputs, elección del matte, las dos pasadas, Premult y Output.
  - `_pass()`: una pasada (F^, B^ y corrección); `_local_mean()`: blur(x·w)/(blur(w)+eps).
  - `_crop_to_format()`, `_box_blur()`, `_expression()`, `_merge_expression()`: piezas del grafo.
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\LGA_ToolPack_menu.py`: entrada `Blur-Fusion` en NODE BUILDS (`add_tool`).
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\Enabled.default.ini`: clave `Build_Blur_Fusion`.
