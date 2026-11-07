# Método: un objeto real en 3D a partir de fotos, con Blender sin interfaz

Las herramientas con las que se hizo este autobús, para repetirlo con otro objeto.

## Requisitos

- Blender 4.x con un servidor MCP que acepte `execute_code` en `localhost:9876` (por ejemplo
  [blender-mcp](https://github.com/ahujasid/blender-mcp)). Se puede usar sin ventana (`blender -b`).
- Python 3 con numpy (el de Blender ya lo trae).
- Un asistente que escriba el script de modelado (aquí, Claude).

## Pasos

1. **Fotos.** La que más rinde es una **vista lateral pura** (de lado, a la altura del objeto, sin
   perspectiva). Después frontal, trasera y tres cuartos. Si falta la lateral, consíguela antes de empezar.
2. **Rejilla para mirar:** `python3 scripts/mcp_run.py scripts/rejilla.py fotos/lateral salida.png 25 2`
3. **Medir la lateral con el largo real como escala:**
   `python3 scripts/mcp_run.py scripts/medir_lateral.py fotos/lateral 11.23 medidas.json x0 y0 x1 y1`
   Da el perfil superior, delantero y trasero y, en cada altura, dónde hay ventanas, puertas y zonas de
   otro color. Las esquinas se modelan luego como curvas suaves: los píxeles confunden cristal y borde.
4. **Modelar por perfiles** (perfil lateral, sección y planta), con la carrocería como carcasa con
   grosor y las ventanas recortadas. Un cristal por cada cristal continuo de la foto y todos los
   cambios de dirección redondeados.
5. **Comparar cada ronda** desde la cámara de cada foto:
   `python3 scripts/mcp_run.py scripts/comparar.py modelo camaras.json fotos salida r1`
   y **de cerca, por zonas**, que es donde se ven los fallos:
   `python3 scripts/mcp_run.py scripts/zonas.py fotos/lateral salida/r1_lateral_render salida/r1 trasera:30,100,180,300`
6. **Visor web:** `python3 scripts/hacer_visor.py modelo visor "Título" "Subtítulo."` crea un HTML que
   se abre con doble clic, con panel de vistas, LOD, interior y giro.

Las rutas de fotos y modelos se pueden pasar con o sin extensión.
