import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
from scipy.spatial import cKDTree
import time
from random import uniform
from collections import defaultdict
from classes_walls import inner_walls
from classes_walls import *
from config import *
from bollard_class import *
import tkinter as tk
import pandas as pd
import os

root = tk.Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.destroy()

banking = 'bank_v2.csv'
if not os.path.exists(banking):
    pd.DataFrame(columns=['sim_nr','wall_setup', 'elapsed_s', 'total_exited', 'avg_flow_ps', 'frames', 'avg_fps', 'particles', 'bollard_type']
                 ).to_csv(banking, index=False)

BOLLARD = bollard_pos.centered
ACTIVE_WALLS = inner_walls.wallie2  # change here to switch layouts

def rgb(r, g, b):
    return (r/255, g/255, b/255)

#####################################################################################
#                               ROOM

class Room:
    def __init__(self, x, y, w, h):
        """x, y = bottom-left corner, w = width, h = height"""
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains_spawn(self, x, y, radius):
        """Check if a point is safely inside this room"""
        return (self.x + radius < x < self.x + self.w - radius and
                self.y + radius < y < self.y + self.h - radius)

    def draw(self, ax):
        # Defining the bounds of the room
        rect = patches.Rectangle(
            (self.x, self.y), self.w, self.h,
            linewidth=2, edgecolor='black', facecolor='lightyellow', zorder=1
        )
        ax.add_patch(rect)

        
    def bounce(self):
            global px_arr, py_arr, vx_arr, vy_arr
            left  = px_arr - r < self.x
            right = px_arr + r > self.x + self.w
            bot   = py_arr - r < self.y
            # Top wall: only bounce particles that are NOT in the door's x-range
            in_door_gap = (px_arr >= door_x1) & (px_arr <= door_x2)
            top   = (py_arr + r > self.y + self.h) & ~in_door_gap

            px_arr[left]  = self.x + r;          vx_arr[left]  = np.abs(vx_arr[left])
            px_arr[right] = self.x + self.w - r; vx_arr[right] = -np.abs(vx_arr[right])
            py_arr[bot]   = self.y + r;          vy_arr[bot]   = np.abs(vy_arr[bot])
            py_arr[top]   = self.y + self.h - r; vy_arr[top]   = -np.abs(vy_arr[top])

#####################################################################################
#                         OPEN THE NOOR

# Door x-range constants — used by both Door.check() and Room.bounce() to agree on the gap

class Door:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def draw(self, ax):
        ax.plot([self.x1, self.x2], [self.y1, self.y2], #Change this here for predefined coordinates
                color='red', linewidth=3, zorder=5)

    def check(self):
        global alive
        # A particle exits when it reaches the top wall AND is within the door's x-range.
        # Room.bounce() already skips bouncing these particles, so they pass straight through.
        in_x   = (px_arr >= door_x1) & (px_arr <= door_x2)
        past_top = py_arr + r > room.y + room.h
        alive[in_x & past_top] = False

#####################################################################################
#                               SETUP
                                    #(0.5, 40.5) ─────────────── (30.5, 40.5)   ← top
                                    #    |                               |
                                    #    |                               |
                                    #    |                               |
                                    #(0.5, 0.5) ─────────────── (30.5, 0.5)   ← bottom
                                    #↑ left                        right ↑

# Inserted figure into window to display infomation
fig = plt.figure(figsize=(screen_w/100, screen_h/100))
manager = plt.get_current_fig_manager()
manager.window.wm_geometry(f"{screen_w}x{screen_h}+0+0")

ax = fig.add_axes([0.02, 0.02, 0.7, 0.96])
info_ax = fig.add_axes([0.73, 0.0, 0.27, 1.0])
info_ax.axis('off')

ax.set_xlim(0, 31)
ax.set_ylim(0, 41)
ax.set_aspect('equal')
ax.axis('off')


# --- Define your floor plan dimensions here ---
room = Room(0.5, 0.5, 30, 40)

room.draw(ax)

door = Door(door_x1, 40.5, door_x2, 40.5)   # the gap between your two inner_walls
door.draw(ax)

#####################################################################################
#                               PARTICLE

# Particle spawn
dt = 1 / fps  # Frame time
px_list, py_list, vx_list, vy_list = [], [], [], []
spawn_limit = room.y + room.h / 3 #creates a limit for the first 1/3 of the room as a bounds for the particles spawning
for _ in range(partnr):
    attempts = 0
    while True:
        attempts += 1
        if attempts > 1000:  # give up and place anywhere
            x = uniform(room.x + r, room.x + room.w - r)
            y = uniform(room.y + r, spawn_limit - r)
            break
            
        x = uniform(room.x + r, room.x + room.w - r)
        y = uniform(room.y + r, spawn_limit - r)

        in_wall = False
        for wall in ACTIVE_WALLS:
            xs = [c[0] for c in wall.corners]
            ys = [c[1] for c in wall.corners]
            if (min(xs) < x < max(xs) and min(ys) < y < max(ys)):
                in_wall = True
                break
        if not in_wall:
            break
    px_list.append(x)
    py_list.append(y)
    vx_list.append(uniform(-sl, sl))  # sl — multiplier of the random start speed
    vy_list.append(uniform(-sl, sl))
for wall in ACTIVE_WALLS:
    wall.draw(ax)
for bollard in BOLLARD:          # BOLLARD is already a list
    bollard.draw(ax)

# Convert to numpy arrays after spawn
px_arr = np.array(px_list)
py_arr = np.array(py_list)
vx_arr = np.array(vx_list)
vy_arr = np.array(vy_list)
alive  = np.ones(partnr, dtype=bool)

# SPH state arrays — sized to partnr on init, trimmed by flush_dead() as particles exit
rho_arr      = np.zeros(partnr)
pressure_arr = np.zeros(partnr)

circles = [
    patches.Circle((px_arr[i], py_arr[i]), r, facecolor="lime", edgecolor="black", zorder=4)
    for i in range(partnr)
]
for c in circles:
    ax.add_patch(c)

#####################################################################################
#                               GRID

grid_spacing = 1      # Size of each cell in meters
grid_cols = int(30 / grid_spacing)   # Number of columns
grid_rows = int(40 / grid_spacing)   # Number of rows

# 2D array to store data — e.g. particle count per cell
grid_data = np.zeros((grid_rows, grid_cols))

def get_grid_cell(x, y):
    # Convert particle x,y position to grid cell index
    col = int((x - room.x) / grid_spacing)
    row = int((y - room.y) / grid_spacing)
    # Binding grid to room space
    col = max(0, min(col, grid_cols - 1))
    row = max(0, min(row, grid_rows - 1))
    row = (grid_rows - 1) - row
    return row, col

def update_grid():
    # Count how many particles are in each cell
    grid_data[:] = 0    # Reset
    n = len(px_arr)
    for i in range(n):
        row, col = get_grid_cell(px_arr[i], py_arr[i])
        grid_data[row, col] += 1
    # ^^ Only keeping track of total count and not neighborhoods

def draw_grid():
    # Draw the grid lines on the plot
    for i in range(grid_cols + 1):
        x = room.x + i * grid_spacing
        ax.plot([x, x], [room.y, room.y + room.h], color='lightblue', linewidth=0.5, zorder=2)
    for j in range(grid_rows + 1):
        y = room.y + j * grid_spacing
        ax.plot([room.x, room.x + room.w], [y, y], color='lightblue', linewidth=0.5, zorder=2)

#####################################################################################
#                               FLUSH DEAD

def flush_dead():
    global px_arr, py_arr, vx_arr, vy_arr, alive, circles, rho_arr, pressure_arr

    if np.all(alive):
        return

    dead_indices = np.where(~alive)[0]
    for i in reversed(dead_indices):
        circles[i].remove()
        circles.pop(i)

    px_arr       = px_arr[alive]
    py_arr       = py_arr[alive]
    vx_arr       = vx_arr[alive]
    vy_arr       = vy_arr[alive]
    rho_arr      = rho_arr[alive]
    pressure_arr = pressure_arr[alive]
    alive        = np.ones(len(px_arr), dtype=bool)

#####################################################################################
#                               SPH RECALLER

def apply_goal_force(px_arr, py_arr, vx_arr, vy_arr):
   
    # --- Goal-seeking force ---
    # Vector toward exit, scaled to preferred speed
    dx = goal_x - px_arr
    dy = goal_y - py_arr
    dist = np.sqrt(dx**2 + dy**2) + 0.001
    # Unit vector toward goal, scaled to preferred speed
    vpx = (dx / dist) * v_pref
    vpy = (dy / dist) * v_pref
    # Nudge current velocity toward preferred velocity over relaxation time tau
    vx_arr += (vpx - vx_arr) / tau * dt
    vy_arr += (vpy - vy_arr) / tau * dt

def build_neighbor_list(px_arr,py_arr):
    # Build KDTree from current positions
    positions = np.column_stack((px_arr, py_arr))
    tree = cKDTree(positions)

    # Get neighbors within search radius h
    neighbor_lists = tree.query_ball_point(positions, r=h)
    # Attaching the pairs based on the "bell" kernel from SPH
    return(neighbor_lists)

def repulse(px_arr,py_arr,vx_arr,vy_arr,neighbors):
    # --- Pairwise repulsion (short + long range) ---
    # Applies force to both particles in opposite directions
    n=len(px_arr)
    for i in range(n):
        for j in neighbors[i]:
            if j <= i:  # Avoid double counting
                continue

            ddx = px_arr[i] - px_arr[j]
            ddy = py_arr[i] - py_arr[j]
            d = np.sqrt(ddx**2 + ddy**2) + 0.001
            ux, uy = ddx / d, ddy / d

            # Applying the cutoff to prioritise interactions
            if d < cutoff:
                force = strength * (cutoff - d)
            elif d < long_cutoff:
                force = long_strength * (long_cutoff - d)
            else:
                continue

            fx, fy = force * ux, force * uy
            vx_arr[i] += (fx / m) * dt
            vy_arr[i] += (fy / m) * dt
            vx_arr[j] -= (fx / m) * dt
            vy_arr[j] -= (fy / m) * dt

def sph_density(px_arr,py_arr,rho_arr,pressure_arr, neighbors):
# --- SPH density + pressure ---
    # Makes them move like "liquid"-esque
    n=len(px_arr)
    for i in range(n):
        rho_i = 0.0
        for j in neighbors[i]:
            ddx = px_arr[i] - px_arr[j]
            ddy = py_arr[i] - py_arr[j]
            dist_ij = np.sqrt(ddx**2 + ddy**2)

            # Poly6 smoothing kernel
            if dist_ij < h:
                w = (h**2 - dist_ij**2) ** 3
                rho_i += m * w

        # Normalize kernel
        rho_arr[i] = rho_i * (4 / (np.pi * h**8))
        # Equation of state — pressure from density
        pressure_arr[i] = k_sph * (rho_arr[i] - rho0)

def sph_viscosity(px_arr,py_arr,vx_arr,vy_arr,rho_arr,pressure_arr, neighbors):
# --- SPH pressure + viscosity acceleration ---
        # Makes it smoother towards exit
        n= len(px_arr)
        for i in range(n):
            ax_sph = 0.0
            ay_sph = 0.0
            for j in neighbors[i]:
                if j == i:
                    continue
                ddx = px_arr[i] - px_arr[j]
                ddy = py_arr[i] - py_arr[j]
                dist_ij = np.sqrt(ddx**2 + ddy**2) + 0.001
                ux, uy = ddx / dist_ij, ddy / dist_ij
                # Spiky kernel gradient for pressure
                if dist_ij < h:
                    dw = -3 * (h - dist_ij)**2  # Derivative of spiky kernel
                    # Pressure force — pushes from high to low density
                    pressure_term = (pressure_arr[i] / (rho_arr[i]**2 + 0.001) +
                                    pressure_arr[j] / (rho_arr[j]**2 + 0.001))
                    ax_sph += -m * pressure_term * dw * ux
                    ay_sph += -m * pressure_term * dw * uy
                    # Viscosity — dampens relative velocity between neighbors
                    ax_sph += mu * (vx_arr[j] - vx_arr[i]) * dw / (rho_arr[j] + 0.001)
                    ay_sph += mu * (vy_arr[j] - vy_arr[i]) * dw / (rho_arr[j] + 0.001)
            vx_arr[i] += ax_sph * dt
            vy_arr[i] += ay_sph * dt

def recaller():
    global px_arr, py_arr, vx_arr, vy_arr, rho_arr, pressure_arr

    n = len(px_arr)
    if n == 0:
        return
   
    apply_goal_force(px_arr, py_arr, vx_arr, vy_arr)
    if n >= 2:   
        neighbors=build_neighbor_list(px_arr,py_arr)

        repulse(px_arr,py_arr,vx_arr,vy_arr,neighbors)
        
        sph_density(px_arr,py_arr,rho_arr,pressure_arr, neighbors)
        
        sph_viscosity(px_arr,py_arr,vx_arr,vy_arr,rho_arr,pressure_arr, neighbors)
    # --- Integrate positions ---
    px_arr += vx_arr * dt
    py_arr += vy_arr * dt

    # --- Boundary conditions ---
    room.bounce()
    for wall in ACTIVE_WALLS:
        px_arr, py_arr, vx_arr, vy_arr = wall.bounce(px_arr, py_arr, vx_arr, vy_arr)
    apply_goal_force(px_arr, py_arr, vx_arr, vy_arr)
    for bollard in BOLLARD:
        bollard.apply_force(px_arr, py_arr, vx_arr, vy_arr, dt)
    door.check()
    update_grid()

#Making the function for information shown on screen
def live_stats():
    total_exited = partnr - len(px_arr)
    elapsed_seconds = frame_idx[0] / fps
    avg_flow = total_exited / elapsed_seconds if elapsed_seconds > 0 else 0.0
    info_text.set_text(
        f"Elapsed\n{elapsed_seconds:.1f}s\n\n"
        f"Exited\n{total_exited}/{partnr}\n\n"
        f"Avg flow\n{avg_flow:.2f} p/s"
    )

def save_results():
    try:
        end_time = time.time()
        elapsed = end_time - start_time
        wall_name = [k for k, v in vars(inner_walls).items() if v is ACTIVE_WALLS][0]
        bollard_name = [k for k, v in vars(bollard_pos).items() if v is BOLLARD][0]

        if os.path.exists(banking):
            existing = pd.read_csv(banking)
            sim_nr = len(existing) + 1
        else:
            sim_nr = 1

        new_row = pd.DataFrame([{
            'sim_nr':       sim_nr,
            'wall_setup':   wall_name,
            'elapsed_s':    round(elapsed, 2),
            'total_exited': partnr,
            'avg_flow_ps':  round(partnr / elapsed, 2),
            'frames':       frame_idx[0],
            'avg_fps':      round(frame_idx[0] / elapsed, 2),
            'particles':    partnr,
            'bollard_type': bollard_name,
        }])

        new_row.to_csv(banking, mode='a', header=False, index=False)
        print(f"Sim {sim_nr} saved — {wall_name}, {elapsed:.1f}s")

    except Exception as e:
        print(f"Save failed: {e}")
        import traceback
        traceback.print_exc()
#####################################################################################
#                               ANIMATION
info_text = info_ax.text(0.5, 0.5, '', ha='center',
                          va='center', fontsize=11, transform=info_ax.transAxes)


flow_log  = []
frame_idx = [0]

def update(frame):
    recaller()
    frame_idx[0] += 1

    n_before = len(px_arr)
    flush_dead()
    n_after  = len(px_arr)
    new_exits = n_before - n_after
    if new_exits > 0:
        flow_log.append((frame_idx[0], new_exits))

    live_stats()

    if len(px_arr) == 0:
        animation.event_source.stop()
        save_results()        # ← save BEFORE closing
        plt.close(fig)

    for i, _ in enumerate(circles):
        circles[i].center = (px_arr[i], py_arr[i])
    return circles + [info_text]

start_time = time.time()
draw_grid()

animation = FuncAnimation(
    fig=fig,
    func=update,
    interval=1000 // fps,
    blit=True,
    cache_frame_data=False
)

plt.get_current_fig_manager().window.lift()  # for TkAgg
plt.show()

#####################################################################################
#                               POST-SIMULATION SUMMARY

flow_per_second = defaultdict(int)
for frame, count in flow_log:
    flow_per_second[frame // fps] += count

print("\n--- Flow per second ---")
for sec, count in sorted(flow_per_second.items()):
    print(f"Second {sec:4d}: {count} particles exited")

print(f"\nTotal exited: {sum(v for _, v in flow_log)}")

end_time = time.time()
elapsed = end_time - start_time

print(f"\n--- Simulation Summary ---")
print(f"Runtime:          {elapsed:.2f}s")          # Name speaks for itself
print(f"Frames rendered:  {frame_idx[0]}")
print(f"Average FPS:      {frame_idx[0] / elapsed:.2f}")
print(f"Total particles (start):  {partnr}")
print(f"Still in room:            {len(px_arr)}")
print(f"Exited:                   {partnr - len(px_arr)}")
print(f"Peak cell count:  {int(grid_data.max())}")  # The highest amount of particles in any cell

raek, kol = np.unravel_index(np.argmax(grid_data), grid_data.shape)  # raek=row, kol=column. Danishfied to avoid mishap
print(f"Peak cell index:  ({int(raek)}, {int(kol)})")  # Tells which cell has the max particles
