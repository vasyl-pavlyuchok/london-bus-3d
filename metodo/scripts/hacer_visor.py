# -*- coding: utf-8 -*-
"""Mete un .glb (en base64) en la plantilla del visor y escribe:
  - <salida>.html: documento completo, se abre con doble clic (necesita internet para Three.js);
  - <salida>_artifact.html: solo el cuerpo, para publicarlo con la herramienta Artifact.
El visor trae el panel de mando a la izquierda (vistas, detallado/LOD1, ver interior, girar solo,
triángulos, materiales y medidas) (nacido con este autobús de Londres).

Uso (python3 del sistema): python3 hacer_visor.py <modelo_sin_extension> <salida_sin_extension> "<Título>" "<Subtítulo.>" ["<nota>"]
Convenciones que el visor espera: frontal hacia +Z, Y arriba; nodo ligero acabado en _LOD1; materiales
*_vidrio (cristal), *_pintura (barniz), *metal*."""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import resolver_foto

a = sys.argv[1:]
glb, salida, titulo, sub = resolver_foto(a[0], (".glb",)), a[1], a[2], a[3]   # .glb sin extensión
nota = a[4] if len(a) > 4 else "Modelo hecho en Blender a partir de fotos de referencia."
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "visor_plantilla.html"), encoding="utf-8").read()
b64 = base64.b64encode(open(glb, "rb").read()).decode("ascii")
cuerpo = (tpl.replace("__GLB_B64__", b64).replace("__TITULO__", titulo)
          .replace("__SUBTITULO__", sub).replace("__NOTA__", nota))
completo = ("<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            "</head>\n<body>\n" + cuerpo + "\n</body>\n</html>\n")
open(salida + ".html", "w", encoding="utf-8").write(completo)
open(salida + "_artifact.html", "w", encoding="utf-8").write(cuerpo)
print("%s.html: %.1f MB" % (salida, len(completo) / 1e6))
