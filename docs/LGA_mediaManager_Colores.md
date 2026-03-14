# Colores de paths en LGA_mediaManager

---

## Diccionario de colores por nivel

```python
colors = {
    0: "#ffff66",  # Amarillo           T
    1: "#28b5b5",  # Verde Cian         Proye
    2: "#ff9a8a",  # Naranja pastel     Grupo
    3: "#0088ff",  # Rojo coral         Shot
    4: "#ffd369",  # Amarillo mostaza
    5: "#28b5b5",  # Verde Cian
    6: "#ff9a8a",  # Naranja pastel
    7: "#6bc9ff",  # Celeste
    8: "#ffd369",  # Amarillo mostaza
    9: "#28b5b5",  # Verde Cian
    10: "#ff9a8a",  # Naranja pastel
    11: "#6bc9ff",  # Celeste
    # Anade mas colores si hay mas niveles
}
```

- El color por defecto si el nivel no está en el diccionario es negro: `#000000`.

---

## Lógica de aplicación en la UI

- Cada parte de la ruta (separada por `/`) recibe un color según su nivel (índice en la ruta) usando el diccionario anterior.
- Si la parte de la ruta coincide con la parte correspondiente del `project_folder`, se usa el color especial `#c56cf0` (lavanda) para esa parte.
- El nombre del archivo (última parte de la ruta) siempre se muestra en blanco y negrita: `rgb(200, 200, 200)`.
- Los separadores `/` se muestran en blanco.

### Ejemplo de uso en HTML (PySide2 QLabel):

```html
<span style='color: #ffff66;'>T</span><span style="color: white;">/</span><span style='color: #28b5b5;'>Proye</span><span style="color: white;">/</span>...<span style='color: #c56cf0;'>Shot</span><span style="color: white;">/</span><b style='color: rgb(200, 200, 200);'>archivo.ext</b>
```

---

## Resumen de colores por nivel

| Nivel | Color      | Descripción         |
|-------|------------|--------------------|
| 0     | #ffff66    | Amarillo (T)       |
| 1     | #28b5b5    | Verde Cian (Proye) |
| 2     | #ff9a8a    | Naranja pastel     |
| 3     | #0088ff    | Rojo coral (Shot)  |
| 4     | #ffd369    | Amarillo mostaza   |
| 5     | #28b5b5    | Verde Cian         |
| 6     | #ff9a8a    | Naranja pastel     |
| 7     | #6bc9ff    | Celeste            |
| 8     | #ffd369    | Amarillo mostaza   |
| 9     | #28b5b5    | Verde Cian         |
| 10    | #ff9a8a    | Naranja pastel     |
| 11    | #6bc9ff    | Celeste            |

- Color especial para coincidencia con project_folder: `#c56cf0` (lavanda)
- Nombre de archivo: `rgb(200, 200, 200)` (blanco)
- Separador `/`: blanco

---

## Notas
- Esta lógica se usa tanto en la función `change_footage_text_color` como en `apply_color_to_label` para colorear rutas en la tabla de media.
- Puedes copiar este bloque para reutilizar la lógica de colores en otros scripts o UIs.
