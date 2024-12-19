import tkinter as tk
import interface
import time

placements = 6
root = tk.Tk()
ui = interface.UserInterface(root)
ui.update_placements(placements)
ui.update_live_feed()
root.mainloop()