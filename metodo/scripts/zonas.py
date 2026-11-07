# -*- coding: utf-8 -*-
"""Dentro de Blender (por mcp_run.py): compara DE CERCA una foto y su render (misma cámara) por zonas,
ampliadas x3, con los bordes del color dominante de la foto en verde sobre el render. Es la prueba que
destapa lo que el contorno general no ve: esquinas, redondeos, huecos, alineaciones.

Uso: python3 mcp_run.py zonas.py <foto_sin_extension> <render_sin_extension> <salida_prefijo> <nombre:x0,y0,x1,y1> [...]
  coordenadas en píxeles de la FOTO; el render se reescala a la foto."""
import bpy, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ("png", "hull"):          # Blender guarda módulos entre llamadas: usa siempre los de la skill
    sys.modules.pop(_m, None)
from png import write_png, resolver_foto

a = sys.argv[1:]


def carga(p):
    im = bpy.data.images.load(resolver_foto(p))
    w, h = im.size
    x = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(im)
    return x[..., :3] * x[..., 3:4] + 0.82 * (1 - x[..., 3:4])


foto, rd = carga(a[0]), carga(a[1])
H, W = foto.shape[:2]
rd = rd[(np.arange(H) * rd.shape[0] / H).astype(int)][:, (np.arange(W) * rd.shape[1] / W).astype(int)].copy()
r, g, b = foto[..., 0], foto[..., 1], foto[..., 2]
col = (r > 0.25) & (r > 1.6 * g) & (r > 1.6 * b)
borde = col & ~(np.roll(col, 1, 0) & np.roll(col, -1, 0) & np.roll(col, 1, 1) & np.roll(col, -1, 1))
rd[borde] = (0.0, 0.9, 0.0)
for z in a[3:]:
    nombre, caja = z.split(":")
    x0, y0, x1, y1 = (int(v) for v in caja.split(","))
    img = np.concatenate([foto[y0:y1, x0:x1], np.ones((y1 - y0, 3, 3), np.float32), rd[y0:y1, x0:x1]], 1)
    write_png("%s_%s.png" % (os.path.abspath(a[2]), nombre), np.repeat(np.repeat(img, 3, 0), 3, 1))
    print("zona:", nombre)
