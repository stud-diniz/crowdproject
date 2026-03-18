import numpy as np
#import matplotlib.pyplot as plt


#Setting parameters

grid_width = 30 #width of the grid
grid_height = 30 #height of the grid
agent_size = 1 #size of the agent



    n_steps = int(t_end/dt)  # Number of steps

    ttable = np.zeros(n_steps)
    xtable = np.zeros(n_steps)
    vtable = np.zeros(n_steps)


    t = 0.0
    x = x0
    v = v0

    for i in range(n_steps):
        ttable[i] = t
        xtable[i] = x
        vtable[i] = v

        t = t + dt
        a = (-k*x)/m #Using F=ma and F=-kx
        v = v + a*dt  # a = dv/dt
        x = x + v*dt  # v = dx/dt

    return ttable, xtable, vtable

def FindPeriod(xtable, ttable):
    n = len(xtable)
    signshifts = np.argwhere(xtable[1:n]*xtable[0:n-1]<0)
    if len(signshifts)<2:
        print('Simulation no long enough to determine period!')
        return 0
    return 2*ttable[signshifts[1] - signshifts[0]][0]

mtable = []
Ttable = []
rtable = [] #ratio table
for m in range(50):
  m = m + 1
  ttable,xtable,vtable = LeapFrog(m, k=5, dt=0.01, t_end=100, v0=6, x0=5)
  mtable.append(m)
  T = FindPeriod(xtable,ttable)
  Ttable.append(T)
  rtable.append(m/5) # Because k=5
print(mtable)
print(Ttable)
print(rtable)

