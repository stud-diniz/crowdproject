import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from config import *

class obstacle:
    def __init__(self, x, y, rar, influence=8.0, strength=5.0, splitter_length=4.0):
        self.x = x
        self.y = y
        self.radius = rar
        self.influence_radius = rar * influence
        self.strength = strength
        self.splitter_length = splitter_length  # how far up the invisible line extends

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

        # --- Hard ejection if inside bollard ---
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

        # --- Soft radial repulsion ---
        affected = (dist >= self.radius) & (dist < self.influence_radius)
        if np.any(affected):
            force_mag = self.strength / (dist[affected] ** 2)
            vx_arr[affected] += (dx[affected] / dist[affected]) * force_mag * dt
            vy_arr[affected] += (dy[affected] / dist[affected]) * force_mag * dt

        # --- Invisible splitter line above bollard ---
        # Particles below the top of the splitter and within x-range get nudged left or right
        above_center = py_arr > self.y                              # above bollard center
        in_splitter   = py_arr < (self.y + self.splitter_length)   # below splitter top
        near_x        = np.abs(dx) < self.radius * 2               # close to center x
        on_splitter   = above_center & in_splitter & near_x

        if np.any(on_splitter):
            # Push left if left of center, right if right — amplified by closeness to center
            side = np.sign(dx[on_splitter])
            side[side == 0] = 1  # nudge ambiguous particles to the right
            closeness = 1.0 - (np.abs(dx[on_splitter]) / (self.radius * 2))
            vx_arr[on_splitter] += side * closeness * self.strength * 0.5 * dt

    def bounce(self, px_arr, py_arr, vx_arr, vy_arr):
        dx = px_arr - self.x
        dy = py_arr - self.y
        dist = np.sqrt(dx**2 + dy**2) + 0.001
        hit = dist < (self.radius + r)
        if not np.any(hit):
            return px_arr, py_arr, vx_arr, vy_arr
        nx = dx[hit] / dist[hit]
        ny = dy[hit] / dist[hit]
        dot = vx_arr[hit] * nx + vy_arr[hit] * ny
        moving_in = dot < 0
        idx = np.where(hit)[0][moving_in]
        nx_in, ny_in = nx[moving_in], ny[moving_in]
        dot_in = dot[moving_in]
        vx_arr[idx] -= 2 * dot_in * nx_in
        vy_arr[idx] -= 2 * dot_in * ny_in
        px_arr[idx] = self.x + nx_in * (self.radius + r)
        py_arr[idx] = self.y + ny_in * (self.radius + r)
        return px_arr, py_arr, vx_arr, vy_arr


class bollard_pos():
    centered = [obstacle(15.5, 22.5, rar, splitter_length=5.0)]
    starwars = [obstacle(15.5, 20.5, rar, influence=8.0, strength=3.0)]
    hug      = [obstacle(18.5, 26.5, rar)]