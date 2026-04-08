import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
from random import uniform

#
#####################################################################################
#                               VARIABLES

partnr = 150     # Count of particles
fps = 60
r = 0.2         # Radius of particle in meter
m = 70          # Mass in kg
sl = 2          # Multiplier on the random start speed
strength = 10    # Multiplier on the force between particles
wallf = 1.0     # Walls repellant force
cutoff       = 5  #threshold of proximity
long_strength = 0.5 #Multiplier on the force between distant particles
long_cutoff  = 10 #threshold of proximity of distant particles

        # Class "Variables" from CSV file for easier run
def rgb(r, g, b):
    return (r/255, g/255, b/255)

#####################################################################################
#                              PARTICLE

class Particle:
    def __init__(self, x, y, vx, vy, r, m, color=None, edgecolor=None):
        self.x = x #position
        self.y = y #position
        self.vx = vx #velocity of x
        self.vy = vy #velocity of y
        self.radius = r #radius of individual particles
        self.mass = m #mass of particle
        self.color = color if color else rgb(107, 255, 149)
        self.edgecolor = edgecolor if edgecolor else rgb(0,0,0)
        # parr = np.array([])

    def f_repulse(self, other):   
        
        #finding the distance between particles
        dx   = self.x - other.x 
        dy   = self.y - other.y
        dist = (dx*dx + dy*dy) ** 0.5 + 0.001
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

    def contains_spawn(self, px, py, radius):
        """Check if a point is safely inside this room"""
        return (self.x + radius < px < self.x + self.w - radius and
                self.y + radius < py < self.y + self.h - radius)

    def draw(self, ax):
        #defining the bounds of the room
        rect = patches.Rectangle(
            (self.x, self.y), self.w, self.h,
            linewidth=2, edgecolor='black', facecolor='lightyellow', zorder=1
        )
        ax.add_patch(rect)

    def bounce(self, p):
        """Bounce particle off room walls"""
        if p.x - p.radius < self.x: #If particle in wall
            p.x = self.x + p.radius #Define where particle should be, when not in all
            p.vx = abs(p.vx) #Make particle go out of wall
        if p.x + p.radius > self.x + self.w:
            p.x = self.x + self.w - p.radius
            p.vx = -abs(p.vx)
        if p.y - p.radius < self.y:
            p.y = self.y + p.radius
            p.vy = abs(p.vy)
        if p.y + p.radius > self.y + self.h:
            p.y = self.y + self.h - p.radius
            p.vy = -abs(p.vy)

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
            closed=True, edgecolor='black', facecolor='gray',zorder=3
        )
        ax.add_patch(poly)

    def bounce(self, p):
        for i in range(len(self.corners)):
            #breaking up variables for each corner position
            x1, y1 = self.corners[i]
            x2, y2 = self.corners[(i + 1) % len(self.corners)]

            # Edge vectors -- using Pythagorean Theorem to find x,y of each edge wall
            ex = x2 - x1
            ey = y2 - y1
            edge_len = (ex**2 + ey**2) ** 0.5 #Pytpytmands formel (Pythagoras)

            # Skip very short edges (end caps)
            if edge_len < 0.3:
                continue

            # Unit edge direction
            tx = ex / edge_len
            ty = ey / edge_len

            # Normal vector
            nx = -ty
            ny = tx

            # Vector from edge start to particle
            dx = p.x - x1
            dy = p.y - y1

            # How far along the edge the particle projects
            along = dx * tx + dy * ty
            if along < 0 or along > edge_len:
                continue  # outside the edge length, skip

            # "Actual" distance from wall in either direction
            dist = dx * nx + dy * ny

            # Only act if particle is within radius of the wall
            if abs(dist) < p.radius:
                # Only bounce if moving toward the wall
                dot = p.vx * nx + p.vy * ny
                if (dist > 0 and dot < 0) or (dist < 0 and dot > 0):
                    p.vx -= 2 * dot * nx
                    p.vy -= 2 * dot * ny
# Conversation of energy and "repel" on the walls aswell. phi = 1/2 k (x-x0)^2 for all around.
# Look into gradient 
                # Push out based on which side the particle is on
                if dist >= 0:
                    p.x = x1 + along * tx + nx * p.radius
                    p.y = y1 + along * ty + ny * p.radius
                else:
                    p.x = x1 + along * tx - nx * p.radius
                    p.y = y1 + along * ty - ny * p.radius
#####################################################################################
#                               SETUP
                                    #(0.5, 9.5) ─────────────── (9.5, 9.5)   ← top
                                    #    |                               |
                                    #    |                               |
                                    #    |                               |
                                    #(0.5, 0.5) ─────────────── (9.5, 0.5)   ← bottom
                                    #↑ left                        right ↑
                                            
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')

# --- Define your floor plan dimensions here ---
room = Room(0.5, 0.5, 9, 9)

inner_walls = [
    #(x1,y1), (x2,y2), (x3,y3), (x4,y4)
    Wall(0.5, 8,   0.5, 7.5,   4, 9.5,   3.8, 9.5),   # left wall
    Wall(9.5, 8,   9.5, 7.5,     5.8, 9.5, 6, 9.5),   # right  wall
]

room.draw(ax)
for wall in inner_walls:
    wall.draw(ax)

# Particle spawn
dt = 1 / fps #frame time
particles = []
circles = []

for _ in range(partnr):
    while True:
        # finding random positions
        px = uniform(room.x + r, room.x + room.w - r)
        py = uniform(room.y + r, room.y + room.h - r)

        # Make sure it doesn't spawn inside a wall
        in_wall = False
        for wall in inner_walls:
            xs = [c[0] for c in wall.corners]
            ys = [c[1] for c in wall.corners]
            if (min(xs) < px < max(xs) and min(ys) < py < max(ys)):
                in_wall = True
                break

        if not in_wall:
            break

    vx = uniform(-sl, sl) # sl - multiplier of the random start speed
    vy = uniform(-sl, sl)
    p = Particle(px, py, vx, vy, r, m)
    particles.append(p)

    circle = patches.Circle((px, py), r, facecolor=p.color, edgecolor="black", zorder=4)
    ax.add_patch(circle)
    circles.append(circle)


#####################################################################################
#                               GRID


grid_spacing = 1      # size of each cell in meters
grid_cols = int(9 / grid_spacing)   # number of columns
grid_rows = int(9 / grid_spacing)   # number of rows

# 2D array to store data — e.g. particle count per cell
grid_data = np.zeros((grid_rows, grid_cols))



def get_grid_cell(px, py):
    # Convert particle x,y position to grid cell index
    col = int((px - room.x) / grid_spacing)
    row = int((py - room.y) / grid_spacing)
    # Binding grid to room space
    col = max(0, min(col, grid_cols - 1))
    row = max(0, min(row, grid_rows - 1))

    row = (grid_rows - 1) - row
    return row, col

def update_grid():
    # Count how many particles are in each cell
    grid_data[:] = 0    # reset
    for p in particles:
        row, col = get_grid_cell(p.x, p.y)
        grid_data[row, col] += 1


            #^^ Only keeping track of total count and not neighborhoods

def draw_grid(ax):
    # Draw the grid lines on the plot
    for i in range(grid_cols + 1):
        x = room.x + i * grid_spacing
        ax.plot([x, x], [room.y, room.y + room.h], color='lightblue', linewidth=0.5, zorder=2)
    for j in range(grid_rows + 1):
        y = room.y + j * grid_spacing
        ax.plot([room.x, room.x + room.w], [y, y], color='lightblue', linewidth=0.5, zorder=2)


#####################################################################################
#                               ANIMATION


def recaller():
    for i in range(len(particles)):
        for j in range(i + 1, len(particles)):  # i+1 avoids double counting
            p1 = particles[i]
            p2 = particles[j]

            fx, fy = Particle.f_repulse(p1, p2)
            # ^^ Get only "related" particles like neighborhoods

            # Applies force to both particles in opposite directions
            p1.vx += (fx / p1.mass) * dt
            p1.vy += (fy / p1.mass) * dt
            p2.vx -= (fx / p2.mass) * dt
            p2.vy -= (fy / p2.mass) * dt
    
    for _, p in enumerate(particles):
        # Move
        p.x += p.vx * dt
        p.y += p.vy * dt

        # Outer wall bounce
        room.bounce(p)

        # Inner wall bounce
        for wall in inner_walls:
            wall.bounce(p)
    update_grid()
    
    
def update(frame):
    recaller()
    for i, p in enumerate(particles):
        circles[i].center = (p.x, p.y)
        # Update the drawn circle position 
    draw_grid(ax)
    return circles

animation = FuncAnimation(
    fig=fig,
    func=update,
    interval=1000 // fps,
    blit=True,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()

print(grid_data)            # raw array
print(grid_data.shape)      # (18, 18) for 0.5 spacing in a 9x9 room

# e.g. get the cell with the most particles
print(np.argmax(grid_data))

# e.g. get total particles counted
print(grid_data.sum())