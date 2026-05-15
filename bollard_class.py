import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from config import *

class obstacle:
    def __init__(self, x, y, rar, influence=15.0, strength=2.0):
        self.x = x
        self.y = y
        self.radius = rar
        self.influence_radius = rar * influence
        self.strength = strength

    def draw(self, ax):
        ball = patches.Circle(
            (self.x, self.y), self.radius,
            edgecolor="black", facecolor="blue", zorder=5
        )
        ax.add_patch(ball)

    def apply_force(self, px_arr, py_arr, vx_arr, vy_arr, dt):
        dx = px_arr - self.x
        dy = py_arr - self.y
        dist = np.sqrt(dx**2 + dy**2) + 0.001

        # Hard push — eject any particle inside the bollard immediately
        inside = dist < self.radius
        if np.any(inside):
            nx = dx[inside] / dist[inside]
            ny = dy[inside] / dist[inside]
            px_arr[inside] = self.x + nx * (self.radius + r)
            py_arr[inside] = self.y + ny * (self.radius + r)
            dot = vx_arr[inside] * nx + vy_arr[inside] * ny
            moving_in = dot < 0
            idx = np.where(inside)[0][moving_in]
            vx_arr[idx] -= 2 * dot[moving_in] * nx[moving_in]
            vy_arr[idx] -= 2 * dot[moving_in] * ny[moving_in]

        # Soft repulsion field outside
        affected = (dist >= self.radius) & (dist < self.influence_radius)
        if np.any(affected):
            force_mag = self.strength / (dist[affected] ** 2)
            vx_arr[affected] += (dx[affected] / dist[affected]) * force_mag * dt
            vy_arr[affected] += (dy[affected] / dist[affected]) * force_mag * dt

class bollard_pos():
    centered = [obstacle(15.5, 37.5, rar)]
    starwars = [obstacle(15.5, 20.5, rar)]
    hug      = [obstacle(18.5, 36.5, rar)]