# -*- coding: utf-8 -*-
"""Escritor PNG mínimo (numpy + zlib), para usarlo dentro y fuera de Blender."""
import zlib, struct
import numpy as np


def write_png(path, img):
    """img: array (h, w, 3) uint8 o float 0..1, y hacia abajo."""
    a = np.asarray(img)
    if a.dtype != np.uint8:
        a = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    h, w = a.shape[:2]
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(h))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    open(path, "wb").write(data)


def read_png_rgb(path):
    """Lector PNG mínimo para los PNG RGB/RGBA de 8 bits que escribe Blender o write_png."""
    d = open(path, "rb").read()
    pos, idat, w = 8, b"", 0
    while pos < len(d):
        n = struct.unpack(">I", d[pos:pos + 4])[0]
        t = d[pos + 4:pos + 8]
        body = d[pos + 8:pos + 8 + n]
        if t == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
            ch = {2: 3, 6: 4}[ct]
        elif t == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * ch
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    i = 0
    for y in range(h):
        f = raw[i]; line = np.frombuffer(raw[i + 1:i + 1 + stride], np.uint8).astype(np.int32); i += 1 + stride
        if f == 0:
            cur = line
        elif f == 2:
            cur = (line + prev) & 255
        else:
            cur = np.zeros(stride, np.int32)
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                if f == 1:
                    cur[x] = (line[x] + a) & 255
                elif f == 3:
                    cur[x] = (line[x] + (a + b) // 2) & 255
                else:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    cur[x] = (line[x] + pr) & 255
        out[y] = cur
        prev = cur
    return out.reshape(h, w, ch)[..., :3]


def resolver_foto(ruta, exts=(".jpg", ".jpeg", ".png", ".webp", ".glb")):
    """Acepta la ruta con o sin extensión (p. ej. referencias/ref5): busca en la carpeta el fichero con ese nombre."""
    import os
    ruta = os.path.abspath(ruta)
    if os.path.exists(ruta):
        return ruta
    d, base = os.path.split(ruta)
    for f in sorted(os.listdir(d)):
        if os.path.splitext(f)[0] == base and os.path.splitext(f)[1].lower() in exts:
            return os.path.join(d, f)
    raise FileNotFoundError("no hay ninguna foto llamada %s en %s" % (base, d))
