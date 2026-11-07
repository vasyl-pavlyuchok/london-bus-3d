# -*- coding: utf-8 -*-
"""Dentro de Blender (por mcp_run.py): copia de una foto con rejilla de coordenadas para MEDIR,
ampliada y opcionalmente recortada. Líneas cada <paso> px originales (amarillas cada 5 pasos).

Uso: python3 mcp_run.py rejilla.py <foto_sin_extension> <salida.png> [paso=25] [zoom=2] [x0 y0 x1 y1]
La foto puede pasarse sin extensión."""
import bpy, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ("png", "hull"):          # Blender guarda módulos entre llamadas: usa siempre los de la skill
    sys.modules.pop(_m, None)
from png import write_png, resolver_foto

a = sys.argv[1:]
foto, salida = a[0], a[1]
paso = int(a[2]) if len(a) > 2 else 25
zoom = int(a[3]) if len(a) > 3 else 2
im = bpy.data.images.load(resolver_foto(foto))
w, h = im.size
px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3].copy()
bpy.data.images.remove(im)
x0, y0, x1, y1 = (int(v) for v in a[4:8]) if len(a) >= 8 else (0, 0, w, h)
fino = np.array((0.0, 0.6, 0.6), np.float32)
for x in range(0, w, paso):
    px[:, x] = (1.0, 1.0, 0.0) if x % (5 * paso) == 0 else px[:, x] * 0.4 + fino
for y in range(0, h, paso):
    px[y, :] = (1.0, 1.0, 0.0) if y % (5 * paso) == 0 else px[y, :] * 0.4 + fino
img = px[y0:y1, x0:x1]
img = np.repeat(np.repeat(img, zoom, 0), zoom, 1)
write_png(os.path.abspath(salida), img)
print("rejilla: %s (%dx%d px originales, paso %d, zoom x%d)" % (salida, w, h, paso, zoom))
