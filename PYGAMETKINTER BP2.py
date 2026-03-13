import tkinter as tk
import tkinter.ttk as ttk
from tkinter import *
import pygame as pg
import sys
import numpy as np
from random import *
import os


class Wall:
    def __init__(self, x, y, w, h, color=(0,0,0)):
        self.rect = pg.Rect(x, y, w, h)
        self.color = color

    def draw(self, surface):
        pg.draw.rect(surface, self.color, self.rect)

    def collides(self, other_rect):
        return self.rect.colliderect(other_rect)


class agenda(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.master.update_idletasks()
        self.skærm()

    def skærm(self):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        fw = sw // 3

        scale = 40          # pixels per meter
        cols = (fw // scale) - 1   # how many full cells fit in the frame, minus 1 for safety
        rows = cols                 # keep it square

        cw = cols * scale
        ch = rows * scale

        x_offset = (fw - cw) // 2
        y_offset = (sh - ch) // 2

        # LEFT FRAME
        lffr = tk.Frame(self, width=fw, height=sh, bg="red")
        lffr.grid(row=0, column=0, sticky="w")
        lffr.grid_propagate(False)

        # CENTER FRAME
        cenfr = tk.Frame(self, width=fw, height=sh, bg="blue")
        cenfr.grid(row=0, column=1, rowspan=2, sticky="nw")
        cenfr.grid_propagate(False)
        cenfr.update_idletasks()

        # RIGHT FRAME
        rgfr=tk.Frame(self, width=fw, height=sh, bg="green")
        rgfr.grid(row=0, column=2, rowspan=2, sticky="n")
        rgfr.grid_propagate(False)

        # Embed pygame into center frame
        embed = tk.Frame(cenfr, width=cw, height=ch)
        embed.place(x=x_offset, y=y_offset)
        embed.update_idletasks()

        os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
        os.environ['SDL_VIDEODRIVER'] = 'windib'  # use 'x11' on Linux/Mac

        pg.init()


        screen = pg.display.set_mode((cw, ch))

        # Define walls as objects
        walls = [
            Wall(0, 0, scale, ch),   # left wall
            Wall(cw - scale, 0, scale, ch),   # right wall
        ]

        def draw():
            screen.fill((255, 255, 255))

            # Draw grid
            for i in range(0, cw, scale):
                pg.draw.line(screen, (180, 180, 180), (i, 0), (i, ch))
            for i in range(0, ch, scale):
                pg.draw.line(screen, (180, 180, 180), (0, i), (cw, i))

            # Draw walls
            for wall in walls:
                wall.draw(screen)

            pg.display.flip()

        draw()
        self.pygame_loop(draw)

    def pygame_loop(self, draw):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
        draw()
        self.after(16, self.pygame_loop, draw)  # ~60fps


if __name__ == "__main__":
    root = tk.Tk()
    app = agenda(root)
    app.pack(fill="both", expand=True)
    root.geometry("{}x{}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
    root.mainloop()