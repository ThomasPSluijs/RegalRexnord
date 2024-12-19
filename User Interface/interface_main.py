import tkinter as tk
import interface

placements = 6
root = tk.Tk()
ui = interface.UserInterface(root)
ui.update_placements(placements)

root.mainloop()

