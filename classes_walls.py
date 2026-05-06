import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from config import *

#####################################################################################
#                           WALL-E

class Wall:
    def __init__(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Four corners of the wall polygon, defined clockwise"""
        self.corners = [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

    def draw(self, ax):
        poly = patches.Polygon(
            self.corners,
            closed=True, edgecolor='black', facecolor='gray', zorder=3
        )
        ax.add_patch(poly)

    def bounce(self, px_arr, py_arr, vx_arr, vy_arr):
        for i in range(len(self.corners)):
            x1, y1 = self.corners[i]
            x2, y2 = self.corners[(i + 1) % len(self.corners)]

            ex, ey = x2 - x1, y2 - y1
            edge_len = (ex**2 + ey**2) ** 0.5

            if edge_len < 0.3:
                continue

            tx, ty = ex / edge_len, ey / edge_len
            nx, ny = -ty, tx

            dx = px_arr - x1
            dy = py_arr - y1

            along = dx * tx + dy * ty
            dist  = dx * nx + dy * ny
            on_edge = (along >= 0) & (along <= edge_len)
            near    = np.abs(dist) < r
            mask    = on_edge & near
            if not np.any(mask):
                continue

            dot = vx_arr[mask] * nx + vy_arr[mask] * ny
            d   = dist[mask]
            toward = ((d > 0) & (dot < 0)) | ((d < 0) & (dot > 0))
            idx = np.where(mask)[0][toward]
            dot_t = vx_arr[idx] * nx + vy_arr[idx] * ny
            vx_arr[idx] -= 2 * dot_t * nx
            vy_arr[idx] -= 2 * dot_t * ny

            a_t = along[mask][toward]
            pos_side = d[toward] >= 0
            px_arr[idx[pos_side]]  = x1 + a_t[pos_side]  * tx + nx * r
            py_arr[idx[pos_side]]  = y1 + a_t[pos_side]  * ty + ny * r
            px_arr[idx[~pos_side]] = x1 + a_t[~pos_side] * tx - nx * r
            py_arr[idx[~pos_side]] = y1 + a_t[~pos_side] * ty - ny * r

        return px_arr, py_arr, vx_arr, vy_arr  # ← now outside the loop


class inner_walls():
    wallie1 = [
        # wall setup wall(x1,y1, x2,y2, x3,y3, x4,y4)
        # Left funnel wall 
        Wall(0.5, 15.5,   0.5, 30.5,   13.5, 30.5,   12.5, 30.5),

        # Right funnel wall
        Wall(30.5, 15.5,  30.5, 30.5,  30.5, 30.5,   18, 30.5),
    ]
    wallie2 = [
        Wall(0.5, 20,   0.5, 30.5,   10, 30.5,   0.5, 20),   # left wall
        Wall(30.5, 20,   30.5, 0.5,   10, 30.5,  0.5, 30.5),  # right wall
    ]
    wallie3 = [
        Wall(0.5, 20,   0.5, 30.5,   10, 30.5,   0.5, 20),   # left wall
        Wall(30.5, 20,   30.5, 0.5,   10, 30.5,  0.5, 30.5),  # right wall
    ]