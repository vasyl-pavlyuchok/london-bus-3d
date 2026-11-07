# -*- coding: utf-8 -*-
"""Envolvente convexa de una máscara (numpy puro), para comparar siluetas sin que cuenten las
ventanas, puertas negras ni el ruido de la foto."""
import numpy as np


def hull_points(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) < 3:
        return None
    # extremos por fila: basta para la envolvente
    rows = {}
    for y, x in zip(ys, xs):
        a = rows.get(y)
        rows[y] = (x, x) if a is None else (min(a[0], x), max(a[1], x))
    pts = sorted({(x, y) for y, (a, b) in rows.items() for x in (a, b)})

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1], float)


def hull_mask(mask):
    h, w = mask.shape
    P = hull_points(mask)
    out = np.ones((h, w), bool)
    if P is None:
        return np.zeros((h, w), bool)
    ys, xs = np.mgrid[0:h, 0:w]
    for (x0, y0), (x1, y1) in zip(P, np.roll(P, -1, 0)):
        out &= ((x1 - x0) * (ys - y0) - (y1 - y0) * (xs - x0)) >= -0.5
    return out
