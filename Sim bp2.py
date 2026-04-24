import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
import scipy as sp
from scipy.spatial import cKDTree
import time
from random import uniform

#
#####################################################################################
#                               VARIABLES

partnr = 1500     # Count of particles
fps = 60
r = 0.2         # Radius of particle in meter
h = 1           # Radius of search in meter
m = 70          # Mass in kg
sl = 2          # Multiplier on the random start speed
strength = 10    # Multiplier on the force between particles
wallf = 1.0     # Walls repellant force
cutoff       = 5  #threshold of proximity
long_strength = 0.5 #Multiplier on the force between distant particles
long_cutoff  = 10 #threshold of proximity of distant particles
goal_x = 45.5   # center of the exit gap
goal_y = 91.0
v_pref = 1.4    # preferred speed in m/s (matches paper)
tau   = 0.5     # relaxation time — how quickly particle steers toward goal. "Smoothing" force so they are gentle
rho0  = 1.0    # rest density (P/m²) — target crowd density
k_sph = 1.0    # gas constant — stiffness of pressure response
mu = 5.0        # viscosity — dampens relative motion between neighbors

# Class "Variables" from CSV file for easier run
def rgb(r, g, b):
    return (r/255, g/255, b/255)

#####################################################################################
#                              PARTICLE

class Particle:
    def __init__(self, r, m, color=None, edgecolor=None):
        self.radius = r #radius of individual particles
        self.mass = m #mass of particle
        self.color = color if color else rgb(107, 255, 149)
        self.edgecolor = edgecolor if edgecolor else rgb(0,0,0)

    def f_repulse(self, i, j):
        dx = px[i] - px[j]
        dy = py[i] - py[j]
        dist = (dx**2 + dy**2) ** 0.5 + 0.001
        ux, uy = dx / dist, dy / dist

        # applying the cutoff to prioritise interactions
        if dist < cutoff:
            force = strength * (cutoff - dist)
        elif dist < long_cutoff:
            force = long_strength * (long_cutoff - dist)
        else:
            return 0, 0

        return force * ux, force * uy

#########################################################
#                           ROOM

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
        #defining the bounds of the room
        rect = patches.Rectangle(
            (self.x, self.y), self.w, self.h,
            linewidth=2, edgecolor='black', facecolor='lightyellow', zorder=1
        )
        ax.add_patch(rect)

    def roomexit(self,ax):
        # Making the doors
        

    def bounce_np(self):
        """Bounce particles off room walls using numpy arrays"""
        # Left wall
        mask = px - r < self.x
        px[mask] = self.x + r
        vx[mask] = np.abs(vx[mask])
        # Right wall
        mask = px + r > self.x + self.w
        px[mask] = self.x + self.w - r
        vx[mask] = -np.abs(vx[mask])
        # Bottom wall
        mask = py - r < self.y
        py[mask] = self.y + r
        vy[mask] = np.abs(vy[mask])
        # Top wall
        mask = py + r > self.y + self.h
        py[mask] = self.y + self.h - r
        vy[mask] = -np.abs(vy[mask])

#############################################################
#                           WALL-E

class Wall:
    def __init__(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Four corners of the wall polygon, defined clockwise"""
        self.corners = [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

    def draw(self, ax):
        #drawing the walls
        poly = patches.Polygon(
            self.corners,
            closed=True, edgecolor='black', facecolor='gray', zorder=3
        )
        ax.add_patch(poly)

    def bounce_np(self):
        """Bounce all particles off this wall using numpy arrays"""
        for k in range(len(self.corners)):
            #breaking up variables for each corner position
            x1, y1 = self.corners[k]
            x2, y2 = self.corners[(k + 1) % len(self.corners)]

            # Edge vectors -- using Pythagorean Theorem to find x,y of each edge wall
            ex = x2 - x1
            ey = y2 - y1
            edge_len = (ex**2 + ey**2) ** 0.5 #Pythagorean theorem

            # Skip very short edges (end caps)
            if edge_len < 0.3:
                continue

            # Unit edge direction
            tx = ex / edge_len
            ty = ey / edge_len

            # Normal vector
            nx = -ty
            ny = tx

            # Vector from edge start to each particle
            dx = px - x1
            dy = py - y1

            # How far along the edge each particle projects
            along = dx * tx + dy * ty
            in_range = (along >= 0) & (along <= edge_len)

            # "Actual" distance from wall in either direction
            dist = dx * nx + dy * ny

            # Only act if particle is within radius of the wall
            close = np.abs(dist) < r
            active = in_range & close

            if not np.any(active):
                continue

            # Only bounce if moving toward the wall
            dot = vx * nx + vy * ny
            bounce_mask = active & (
                ((dist > 0) & (dot < 0)) | ((dist < 0) & (dot > 0))
            )
            vx[bounce_mask] -= 2 * dot[bounce_mask] * nx
            vy[bounce_mask] -= 2 * dot[bounce_mask] * ny

            # Conversation of energy and "repel" on the walls aswell. phi = 1/2 k (x-x0)^2 for all around.
            # Look into gradient

            # Push out based on which side the particle is on
            pos_side = active & (dist >= 0)
            neg_side = active & (dist < 0)
            px[pos_side] = x1 + along[pos_side] * tx + nx * r
            py[pos_side] = y1 + along[pos_side] * ty + ny * r
            px[neg_side] = x1 + along[neg_side] * tx - nx * r
            py[neg_side] = y1 + along[neg_side] * ty - ny * r

#####################################################################################
#                               SETUP
                                    #(0.5, 90.5) ─────────────── (90.5, 90.5)   ← top
                                    #    |                               |
                                    #    |                               |
                                    #    |                               |
                                    #(0.5, 0.5) ─────────────── (90.5, 0.5)   ← bottom
                                    #↑ left                        right ↑

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(0, 90)
ax.set_ylim(0, 90)
ax.set_aspect('equal')
ax.axis('off')

# --- Define your floor plan dimensions here ---
room = Room(0.5, 0.5, 90, 90)

inner_walls = [
    #(x1,y1), (x2,y2), (x3,y3), (x4,y4)
    Wall(0.5, 80,   0.5, 70.5,   40, 90.5,   30.8, 90.5),   # left wall
    Wall(90.5, 80,   90.5, 70.5,   50.8, 90.5, 60, 90.5),   # right wall
]

room.draw(ax)
for wall in inner_walls:
    wall.draw(ax)

# Particle spawn
dt = 1 / fps  #frame time
px_list, py_list, vx_list, vy_list = [], [], [], []

for _ in range(partnr):
    while True:
        # finding random positions
        x = uniform(room.x + r, room.x + room.w - r)
        y = uniform(room.y + r, room.y + room.h - r)

        # Make sure it doesn't spawn inside a wall
        in_wall = False
        for wall in inner_walls:
            xs = [c[0] for c in wall.corners]
            ys = [c[1] for c in wall.corners]
            if (min(xs) < x < max(xs) and min(ys) < y < max(ys)):
                in_wall = True
                break
        if not in_wall:
            break

    px_list.append(x)
    py_list.append(y)
    vx_list.append(uniform(-sl, sl))  # sl - multiplier of the random start speed
    vy_list.append(uniform(-sl, sl))

# Convert to numpy arrays after spawn
px       = np.array(px_list)
py       = np.array(py_list)
vx       = np.array(vx_list)
vy       = np.array(vy_list)
rho      = np.zeros(partnr)
pressure = np.zeros(partnr)
neighbors = [[] for _ in range(partnr)]

# Single prototype particle for shared properties
particle_proto = Particle(r, m)

# Circles for drawing
circles = [patches.Circle((px[i], py[i]), r, facecolor=particle_proto.color, edgecolor="black", zorder=4) for i in range(partnr)]
for c in circles:
    ax.add_patch(c)

#####################################################################################
#                               GRID

grid_spacing = 1      # size of each cell in meters
grid_cols = int(90 / grid_spacing)   # number of columns
grid_rows = int(90 / grid_spacing)   # number of rows

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
    grid_data[:] = 0    # reset
    for i in range(partnr):
        row, col = get_grid_cell(px[i], py[i])
        grid_data[row, col] += 1
    #^^ Only keeping track of total count and not neighborhoods

def draw_grid():
    # Draw the grid lines on the plot
    for i in range(grid_cols + 1):
        x = room.x + i * grid_spacing
        ax.plot([x, x], [room.y, room.y + room.h], color='lightblue', linewidth=0.5, zorder=2)
    for j in range(grid_rows + 1):
        y = room.y + j * grid_spacing
        ax.plot([room.x, room.x + room.w], [y, y], color='lightblue', linewidth=0.5, zorder=2)

#####################################################################################
#                               ANIMATION

frame_count = 0

def recaller():
    global px, py, vx, vy, rho, pressure, neighbors

    # Build KDTree from current positions
    positions = np.column_stack((px, py))
    tree = cKDTree(positions)

    # Get neighbors
    neighbor_lists = tree.query_ball_point(positions, r=h)
    # Attaching the pairs based on the "bell" kernel from SPH
    for i in range(partnr):
        neighbors[i] = neighbor_lists[i]

    # Speeds to goal
    dx = goal_x - px
    dy = goal_y - py
    dist = np.sqrt(dx**2 + dy**2) + 0.001
    # Unit vector toward goal, scaled to preferred speed
    vpx = (dx / dist) * v_pref
    vpy = (dy / dist) * v_pref
    # Nudge current velocity toward preferred velocity over time tau
    vx += (vpx - vx) / tau * dt
    vy += (vpy - vy) / tau * dt

    # Vector forces and particle counting
    for i in range(partnr):
        for j in neighbors[i]:
            if j <= i:  # avoid double counting
                continue
            fx, fy = particle_proto.f_repulse(i, j)
            

            # Applies force to both particles in opposite directions
            vx[i] += (fx / m) * dt
            vy[i] += (fy / m) * dt
            vx[j] -= (fx / m) * dt
            vy[j] -= (fy / m) * dt

    # SPH density and pressure. Makes them move like "liquid"-esque
    for i in range(partnr):
        rho_i = 0.0
        for j in neighbors[i]:
            dx_ij = px[i] - px[j]
            dy_ij = py[i] - py[j]
            dist_ij = (dx_ij**2 + dy_ij**2) ** 0.5

            # Poly6 smoothing kernel
            if dist_ij < h:
                w = (h**2 - dist_ij**2) ** 3
                rho_i += m * w

        # Normalize kernel
        rho[i] = rho_i * (4 / (np.pi * h**8))

        # Equation of state — pressure from density
        pressure[i] = k_sph * (rho[i] - rho0)

    # SPH pressure and viscosity acceleration. Makes it smoother towards exit
    for i in range(partnr): #For loop issue, will look into it
        ax_sph = 0.0
        ay_sph = 0.0
        for j in neighbors[i]:
            if j == i:
                continue
            dx_ij = px[i] - px[j]
            dy_ij = py[i] - py[j]
            dist_ij = (dx_ij**2 + dy_ij**2) ** 0.5 + 0.001
            ux, uy = dx_ij / dist_ij, dy_ij / dist_ij

            # Spiky kernel gradient for pressure
            if dist_ij < h:
                dw = -3 * (h - dist_ij)**2  # derivative of spiky kernel

                # Pressure force — pushes from high to low density
                pressure_term = (pressure[i] / (rho[i]**2 + 0.001) +
                                 pressure[j] / (rho[j]**2 + 0.001))
                ax_sph += -m * pressure_term * dw * ux
                ay_sph += -m * pressure_term * dw * uy

                # Viscosity — dampens relative velocity between neighbors
                ax_sph += mu * (vx[j] - vx[i]) * dw / (rho[j] + 0.001)
                ay_sph += mu * (vy[j] - vy[i]) * dw / (rho[j] + 0.001)

        vx[i] += ax_sph * dt
        vy[i] += ay_sph * dt

    # Actually move them
    px += vx * dt
    py += vy * dt

    # Outer wall bounce
    room.bounce_np()

    # Inner wall bounce
    for wall in inner_walls:
        wall.bounce_np()

    update_grid()

def update(frame):
    global frame_count
    frame_count += 1
    recaller()
    for i in range(partnr):
        circles[i].center = (px[i], py[i])
        # Update the drawn circle position
    return circles

start_time = time.time()
draw_grid()

animation = FuncAnimation(
    fig=fig,
    func=update,
    interval=1000 // fps,
    blit=True,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()  # blocks here until the window is closed

end_time = time.time()
elapsed = end_time - start_time

print(grid_data)            # raw array
print(grid_data.shape)      # (18, 18) for 0.5 spacing in a 9x9 room

print(f"\n--- Simulation Summary ---")
print(f"Runtime:          {elapsed:.2f}s")          # Name speaks for itself
print(f"Frames rendered:  {frame_count}")          # Absolute Fps count
print(f"Total particles:  {int(grid_data.sum())}")  # Incase we forget the particle sum
print(f"Peak cell count:  {int(grid_data.max())}")  # The highest amount of particles in any cell

raek, kol = np.unravel_index(np.argmax(grid_data), grid_data.shape) #raek=row, kol=column. Danishfied to avoid mishap
print(f"Peak cell index:  ({int(raek)}, {int(kol)})") # Tells which cell has the max particles