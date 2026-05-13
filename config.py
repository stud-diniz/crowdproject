# Particle defined
partnr = 1000     # Count of particles
r = 0.2         # Radius of particle in meter
h = 1           # Radius of search in meter
m = 80          # Mass in kg

# Speeds
sl = 1          # Multiplier on the random start speed
v_pref = 1.4    # Preferred speed in m/s (matches paper)

# Particle forces
strength = 20    # Multiplier on the force between particles
cutoff = 5      # Threshold of proximity
long_strength = 0.5  # Multiplier on the force between distant particles
long_cutoff = 10     # Threshold of proximity of distant particles

# Kernel variables
tau   = 0.5     # Relaxation time — how quickly particle steers toward goal. "Smoothing" force so they are gentle
rho0  = 1.0    # Rest density (P/m²) — target crowd density
k_sph = 1.0    # Gas constant — stiffness of pressure response
mu = 5.0        # Viscosity — dampens relative motion between neighbors

# Wall forces
wallf = 2.0     # Walls repellant force

# Door
door_x1 = 14.75
door_x2 = 16.25
# Door attactive force location
goal_x = 15.5   # center of door (12.5 to 18.5)
goal_y = 35.0   # just above the top wall (30.5) to pull them through


fps = 60