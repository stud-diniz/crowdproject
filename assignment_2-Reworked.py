# assignment 2 option 3reworked
# marcus blem
# 18/11-25

# repulsive particles

# this program can make particles that repel each other based on distanece

# side by pressing w





import pygame
import sys
import random
import numpy as np


BLACK = 0, 0, 0
WHITE = 255, 255, 255
BLUE = 0, 0, 255
RED = 255, 0, 0

particle_nr = 30
frames_s = 60


radius = 0.2 # in meters # fuck, er i pixles? skifter ikke størrelse nåd du zoomer
mass = 1

slow = 1 #multiplier on the random start speed

strength= 2 # multiplier on the force between particles
cutoff = 5 # how close do the particles need to be to reppel,


wall_force = 1.0
# long range to minimize clustering
long_strength= 0.5 # how far should the long range be?
long_cutoff = 10 # how strong?

width = 30   # the width in m of the simulation
height = 30  # the height in m of the simulation

scale_factor = 25 # pixles per meter
desired_screen_width = 750 # in pixles
screen_multiplier = desired_screen_width / (width * scale_factor)


screen_width = int(width * scale_factor * screen_multiplier) # the width of the screen
screen_height = int(height * scale_factor * screen_multiplier) # multiply the screenwidth


#x_grid = 0.1 # the interval of x-axis grid of the coordinate system
#y_grid = 0.1  # the interval of y-axis grid of the coordinate system

sim_width_pix = width * scale_factor
sim_height_pix = height * scale_factor

screen_x = (screen_width - width * scale_factor) // 2
screen_y = (screen_height - height * scale_factor) //2



running = True



pygame.init()

# 2. define screen
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()



import pygame
import random


# makes a class, like a dictionarry, but not quite
class Particle:
    def __init__(self, x, y, vx, vy, radius, color = WHITE):
        # __init__ runs automatically when a new particle is created
        # everything is in m and m/s
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.mass = mass
        self.color = color



    def update(self, fx, fy):
        # a = f/m
        # calculate the acceleration in x and y
        ax = fx / self.mass
        ay = fy / self.mass
        # calculate the new position for the particle
        self.vx += ax *dt
        self.vy += ay* dt

        self.x += self.vx *dt
        self.y += self.vy *dt


        #self.vx *= 0.99
        #self.vy *= 0.99



    def soft_wall(self, width, height, wall_force ):
        fx=0
        fy=0
        #left side
        #linear force with distance outside, back on the screen
        if self.x < 0:      fx+= wall_force*(abs(self.x))
        if self.x > width:  fx-= wall_force*((abs(self.x-width)))

        if self.y < 0:      fy += wall_force * (abs(self.y) )
        if self.y > height: fy -= wall_force * ((abs(self.y-height)))

        return fx,fy


    def draw(self, screen, scale_factor):
        #calculate the pixle positions
        pix_x = int(self.x * scale_factor * screen_multiplier)
        # pygames y-axis is flipped, so we subtract height
        pix_y = int ((height -self.y) * scale_factor* screen_multiplier)
        pix_radius = int(self.radius * scale_factor)
        # draw the particle
        pygame.draw.circle(screen,self.color, (pix_x,pix_y),pix_radius )




def f_repulse (p1, p2, strength):
    # strength detirmines the repulisve forces between the particles
    dist_x = p1.x - p2.x # distance in x
    dist_y = p1.y - p2.y # distance in y
    dist_xy = ((dist_x *dist_x + dist_y *dist_y) ** 0.5 )+ 0.001# distance from p1 to p2
    # add 0.001 to make sure nothing breaks when particles occupy the same space
    #if dist_xy ==0: return 0,0

    # calculate the unit vector
    unit_x = dist_x / dist_xy
    unit_y = dist_y / dist_xy

    if dist_xy > cutoff:
        return 0,0

    if dist_xy < cutoff:
        force_ = strength * (cutoff - dist_xy)
        #force_ = strength/(dist_xy*dist_xy)
    elif dist_xy < long_cutoff:
        force_ = long_strength *(long_cutoff - dist_xy)

    else: return 0,0
    fx_repulse =  force_ * unit_x
    fy_repulse =  force_ * unit_y


    return fx_repulse, fy_repulse


particles = []
for placeholder in range(particle_nr):
    x = random.uniform(0, width)
    y = random.uniform(0, height)
    vx = (random.uniform(-1, 1)*slow)
    vy = random.uniform(-1, 1)* slow
    particles.append(Particle(x, y, vx, vy, radius))
# makes a list to save forces in

dt = 1/frames_s


running = True
while running:




    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
            pygame.quit()
            sys.exit()




    # reset the forces
    forces = [(0, 0) for placeholder in particles ]
    
    # forces hold the force in x and y direction for all particles
    # we calculate all and then apply them

        #calculate forces between particles
    for particle_i in range (len(particles)):
        #look at particle i
        for particle_j in range (particle_i + 1, len(particles)):
            # compare to particle j, so a particle isnt compared to itself
            # and when 2 particles have been compared, they wont be compared the other way
            # (when particle 1 and 2 have run, we dont do 2 and 1

            fx_repulse, fy_repulse = f_repulse(particles[particle_i],
                                               particles[particle_j], strength)
            # for particle i save the force in x and y direction
            forces[particle_i] = (forces[particle_i][0] + fx_repulse,
                                  forces[particle_i][1] + fy_repulse)
            # for particle j save the force in x and y direction
            forces[particle_j] = (forces[particle_j][0] - fx_repulse,
                                  forces[particle_j][1] - fy_repulse)



    for i in range(len(particles)):
        p = particles[i]#
        fx,fy = forces[i]

        fx_wall, fy_wall = p.soft_wall(width,height,wall_force)

        total_fx = fx+ fx_wall
        total_fy = fy+ fy_wall


        p.update(total_fx,total_fy)


    screen.fill(BLACK)
    for p in particles:
        p.draw(screen, scale_factor)

    pygame.display.flip()
    clock.tick(frames_s)
    pygame.display.set_caption(f'repulsive particles')

# Draw particle


pygame.quit()



