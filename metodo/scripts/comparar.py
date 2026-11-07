# -*- coding: utf-8 -*-
"""Dentro de Blender (por mcp_run.py): renderiza un .glb desde la cámara de cada foto (Cycles CPU, pocas
muestras, 960 px) y compone <salida>/<ronda>_<foto>.png = foto (contorno del render en magenta) |
render (silueta de la foto en verde). Imprime el IoU de silueta (envolvente convexa) de cada foto.

Uso: python3 mcp_run.py comparar.py <modelo_sin_extension> <camaras.json> <carpeta_fotos> <salida> <ronda> [foto ...]
camaras.json: {"cams": {"ref1": {"loc": [x,y,z], "rot": [rx,ry,rz], "lens_mm": 50, "size": [w,h],
               "ortho": <ancho en m, solo para fotos laterales puras>}}}  (coordenadas de Blender)
La silueta de cada foto se toma del color dominante (canal r por defecto: "canal" en la entrada)."""
import bpy, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ("png", "hull"):          # Blender guarda módulos entre llamadas: usa siempre los de la skill
    sys.modules.pop(_m, None)
from png import write_png, resolver_foto
from hull import hull_mask

a = sys.argv[1:]
glb, camjson, fotos_dir, salida, tag = (os.path.abspath(v) if i < 4 else v for i, v in enumerate(a[:5]))
glb = resolver_foto(glb, (".glb",))   # acepta la ruta con o sin extensión
CAMS = json.load(open(camjson))["cams"]
fotos = a[5:] or list(CAMS)
os.makedirs(salida, exist_ok=True)

scn = bpy.context.scene
for o in list(scn.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in list(scn.objects):
    if "LOD1" in o.name:
        o.hide_render = True
me = bpy.data.meshes.new("suelo")
me.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new("suelo", me); scn.collection.objects.link(g); g.is_shadow_catcher = True
w = scn.world or bpy.data.worlds.new("mundo"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.64, 0.7, 1)
sun = bpy.data.lights.new("sol", 'SUN'); sun.energy = 2.6; sun.angle = 0.3
so = bpy.data.objects.new("sol", sun); so.rotation_euler = (0.75, 0.0, 0.5); scn.collection.objects.link(so)
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 16; scn.cycles.use_denoising = True
scn.render.film_transparent = True
scn.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new("CAM_foto", bpy.data.cameras.new("CAM_foto")); scn.collection.objects.link(cam); scn.camera = cam


def contorno(m):
    e = m.copy()
    for _ in range(2):
        n = e.copy(); n[1:, :] &= e[:-1, :]; n[:-1, :] &= e[1:, :]; n[:, 1:] &= e[:, :-1]; n[:, :-1] &= e[:, 1:]; e = n
    return m & ~e


def reduce(arr, h, w):
    H, W = arr.shape[:2]
    return arr[(np.arange(h) * H / h).astype(int)][:, (np.arange(w) * W / w).astype(int)]


for nombre in fotos:
    c = CAMS[nombre]
    W, H = c["size"]
    sc = 960.0 / max(W, H)
    w_, h_ = int(round(W * sc)), int(round(H * sc))
    scn.render.resolution_x, scn.render.resolution_y = w_, h_
    cam.data.sensor_fit = 'HORIZONTAL'; cam.data.sensor_width = 36.0; cam.data.lens = c.get("lens_mm", 50)
    cam.data.type = 'ORTHO' if c.get("ortho") else 'PERSP'
    if c.get("ortho"):
        cam.data.ortho_scale = c["ortho"]
    cam.location = c["loc"]; cam.rotation_mode = 'XYZ'; cam.rotation_euler = c["rot"]
    out = os.path.join(salida, "%s_%s_render.png" % (tag, nombre))
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(out)
    rp = np.array(im.pixels[:], dtype=np.float32).reshape(h_, w_, 4)[::-1]; bpy.data.images.remove(im)
    rgb = rp[..., :3] * rp[..., 3:4] + 0.82 * (1 - rp[..., 3:4])
    rsil = hull_mask(rp[..., 3] > 0.97)
    fp = [f for f in os.listdir(fotos_dir) if os.path.splitext(f)[0] == nombre][0]
    im = bpy.data.images.load(os.path.join(fotos_dir, fp))
    pp = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1, :, :3]; bpy.data.images.remove(im)
    foto = reduce(pp, h_, w_).copy()
    i = "rgb".index(c.get("canal", "r"))
    col = (foto[..., i] > 0.30) & (foto[..., i] > 1.7 * foto[..., (i + 1) % 3]) & (foto[..., i] > 1.7 * foto[..., (i + 2) % 3])
    if "caja" in c:                      # caja del objeto en la foto (px originales)
        x0, y0, x1, y1 = (int(v * sc) for v in c["caja"])
        m = np.zeros_like(col); m[y0:y1, x0:x1] = True; col &= m
    psil = hull_mask(col)
    iou = float((psil & rsil).sum()) / max(1, float((psil | rsil).sum()))
    izq = foto.copy(); izq[contorno(rsil)] = (1.0, 0.0, 1.0)
    der = rgb.copy(); der[contorno(psil)] = (0.0, 1.0, 0.0)
    write_png(os.path.join(salida, "%s_%s.png" % (tag, nombre)), np.concatenate([izq, np.ones((h_, 6, 3)), der], 1))
    print("%s %s: IoU silueta %.3f" % (tag, nombre, iou))
