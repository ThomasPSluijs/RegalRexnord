import tkinter as tk
import interface

placements = 1
root = tk.Tk()
ui = interface.UserInterface(root)
root.mainloop()

ui.update_placements(placements)
