# -*- coding: utf-8 -*-
"""Dentro de Blender (por mcp_run.py): MIDE un objeto en una foto LATERAL PURA, píxel a píxel.
La escala sale del largo real conocido (de extremo a extremo de la silueta en la foto).

Saca, en metros (u = desde el extremo izquierdo de la foto, z = sobre el suelo):
  - perfil superior (techo) por columnas,
  - perfil izquierdo/derecho por filas,
  - en cada altura (cada 10 cm) los tramos de OTRO color dentro de la silueta: ventanas, puertas,
    zonas negras, rejillas, logos.
Guarda un JSON y lo imprime resumido.

Uso: python3 mcp_run.py medir_lateral.py <foto_sin_extension> <largo_m> <salida.json> <x0 y0 x1 y1> [canal=r] [ratio=1.6] [y_suelo]
  x0..y1: caja que contiene SOLO el objeto (evita otros objetos del mismo color).
  canal:  color dominante de la carrocería (r, g o b); ratio: cuánto debe dominar sobre los otros dos.
  y_suelo: fila del suelo si la detección por neumáticos falla.
Ojo: el cristal y la sombra del suelo se confunden con el borde. Mira siempre el resultado sobre la
rejilla antes de convertir una tabla de píxeles en perfil; las esquinas se modelan como curvas suaves."""
import bpy, numpy as np, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ("png", "hull"):          # Blender guarda módulos entre llamadas: usa siempre los de la skill
    sys.modules.pop(_m, None)
from png import resolver_foto

a = sys.argv[1:]
foto, largo, salida = a[0], float(a[1]), a[2]
X0, Y0, X1, Y1 = (int(v) for v in a[3:7])
canal = a[7] if len(a) > 7 else "r"
ratio = float(a[8]) if len(a) > 8 else 1.6
im = bpy.data.images.load(resolver_foto(foto))
w, h = im.size
px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
bpy.data.images.remove(im)
i = "rgb".index(canal)
c = px[..., i]
o1, o2 = px[..., (i + 1) % 3], px[..., (i + 2) % 3]
col = (c > 0.25) & (c > ratio * o1) & (c > ratio * o2)
caja = np.zeros_like(col); caja[Y0:Y1, X0:X1] = True
col &= caja
cols = np.where(col.sum(0) >= 4)[0]
xl, xr = int(cols.min()), int(cols.max())
if len(a) > 9:
    y_suelo = int(a[9])
else:
    oscuro = px.mean(2) < 0.10
    filas = [y for y in range(Y0, Y1) if oscuro[y, xl:xr].sum() > 8]
    y_suelo = max(filas) if filas else Y1
s = (xr - xl + 1) / largo
U = lambda x: (x - xl) / s
Z = lambda y: (y_suelo - y) / s
y_top = int(np.where(col[:, xl:xr].sum(1) >= 3)[0].min())
sil = np.zeros_like(col)
for y in range(h):
    xs = np.where(col[y])[0]
    if len(xs) > 3:
        sil[y, xs.min():xs.max() + 1] = True
out = {"foto": foto, "px_por_m": float(s), "x_izq": xl, "x_der": xr, "y_suelo": y_suelo, "alto_medido": round(Z(y_top), 3)}
out["techo_u_z"] = [(round(U(x), 2), round(Z(int(np.where(col[:, x])[0].min())), 3))
                    for x in range(xl, xr + 1, 3) if col[:, x].any()]
out["perfil_z_uizq_uder"] = [(round(Z(y), 2), round(U(int(np.where(col[y])[0].min())), 3), round(U(int(np.where(col[y])[0].max())), 3))
                             for y in range(y_top, y_suelo + 1, 2) if col[y].sum() > 3]
tramos = {}
for zz in np.arange(0.2, Z(y_top), 0.10):
    y = int(round(y_suelo - zz * s))
    fila = sil[y] & ~col[y]
    runs, x = [], xl
    while x <= xr:
        if fila[x]:
            x0 = x
            while x <= xr and fila[x]:
                x += 1
            if x - x0 >= 3:
                runs.append((round(U(x0), 2), round(U(x - 1), 2)))
        x += 1
    tramos["%.2f" % zz] = runs
out["otro_color_por_altura"] = tramos
json.dump(out, open(os.path.abspath(salida), "w"), indent=1)
print("px/m %.2f · extremos x %d..%d · suelo y=%d · alto %.2f m" % (s, xl, xr, y_suelo, Z(y_top)))
for k, v in tramos.items():
    print(k, v)
