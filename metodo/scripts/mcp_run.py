# Cliente mínimo del servidor MCP de Blender sin ventana (puerto 9876).
# Uso: python3 mcp_run.py fichero.py [args...]  -> ejecuta el fichero dentro de Blender.
import socket, json, sys, os

def cmd(t, timeout=900, **p):
    s = socket.create_connection(("localhost", 9876), timeout=timeout)
    s.sendall(json.dumps({"type": t, "params": p}).encode())
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            return json.loads(buf)
        except Exception:
            continue
    return json.loads(buf)

if __name__ == "__main__":
    path = os.path.abspath(sys.argv[1])
    args = sys.argv[2:]
    code = ("import sys\nsys.argv=%r\n__file__=%r\nexec(compile(open(%r).read(), %r, 'exec'), "
            "{'__name__':'__main__','__file__':%r,'bpy':bpy})" % (["x"] + args, path, path, path, path))
    r = cmd("execute_code", code=code)
    if r.get("status") == "success":
        print(r["result"].get("result", ""))
    else:
        msg = r.get("message", r)
        try:
            print(json.loads(msg)["traceback"])
        except Exception:
            print(msg)
        sys.exit(1)
