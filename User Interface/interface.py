import customtkinter
import sys
from PIL import Image, ImageTk

#%% Variables
activity_msg = "activity message"
percentage_msg = 0.3

font = "Century Regular"
fontsize = 20

background_color = ['gray92', 'gray14']
button_color = ['#0C955A', '#106A43']
frame_color = ['gray86', 'gray17']
state_color = "red"

leftbar_button_width = 250
camscale = 1

#%% Setup
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

root = customtkinter.CTk()
root.attributes("-fullscreen", True)

def on_closing():
    root.destroy()
    sys.exit()
root.protocol("WM_DELETE_WINDOW", on_closing)

#%% Configure the Grid Layout
root.grid_rowconfigure(0, weight=1)  # row for leftbar and camview
root.grid_columnconfigure(0, weight=0)  # first column for leftbar
root.grid_columnconfigure(1, weight=0)  # second column for camview
root.grid_columnconfigure(2, weight=0)  # third column for next placement
root.grid_columnconfigure(3, weight=0)  # fourth column for progress

#%% Left Bar (Sidebar)
leftbar = customtkinter.CTkFrame(master=root, corner_radius=0)
leftbar.grid(row=0, column=0, sticky="nswe")

leftbar.grid_rowconfigure(0, weight=0)  # Rijen met knoppen bovenaan
leftbar.grid_rowconfigure(1, weight=0)
leftbar.grid_rowconfigure(2, weight=0)
leftbar.grid_rowconfigure(3, weight=0)
leftbar.grid_rowconfigure(4, weight=1)  # Voeg lege ruimte toe boven de labels (onderaanruimte)
leftbar.grid_rowconfigure(5, weight=0)
leftbar.grid_rowconfigure(6, weight=0)

packing_mode = customtkinter.CTkButton(master=leftbar, corner_radius=0, text="packing mode", font=(font, fontsize), width=leftbar_button_width, height=60, fg_color=button_color, anchor="w")
packing_mode.grid(row=0, column=0, pady=(20, 0), padx=0, sticky="w")

running_mode = customtkinter.CTkButton(master=leftbar, corner_radius=0, text="running mode", font=(font, fontsize), width=leftbar_button_width, height=60, fg_color=button_color, anchor="w")
running_mode.grid(row=1, column=0, pady=(20, 0), padx=0, sticky="w")

start_but = customtkinter.CTkButton(master=leftbar, corner_radius=0, text="start", font=(font, fontsize), width=leftbar_button_width, height=60, fg_color=button_color, anchor="w")
start_but.grid(row=2, column=0, pady=(20, 0), padx=0, sticky="w")

parts = ["big blue", "small blue"]
partselection = customtkinter.CTkOptionMenu(master=leftbar, corner_radius=0, values=parts, font=(font, fontsize), dropdown_font=(font, fontsize), width=leftbar_button_width, height=60, fg_color=button_color, anchor="w", button_color=button_color, button_hover_color=button_color, dropdown_hover_color=button_color)
partselection.grid(row=3, column=0, pady=(20, 0), padx=0, sticky="w")

activity = customtkinter.CTkLabel(master=leftbar, text=activity_msg, font=(font, fontsize), width=leftbar_button_width, height=60, fg_color=frame_color, anchor="w")
activity.grid(row=5, column=0, pady=(0, 10), padx=(5, 0), sticky="w")

status = customtkinter.CTkLabel(master=leftbar, text="status:", font=(font, fontsize), width=leftbar_button_width, height=60, fg_color=frame_color, anchor="w")
status.grid(row=6, column=0, pady=(0, 10), padx=(5, 0), sticky="w")

statuslight = customtkinter.CTkLabel(master=leftbar, width=38, height=38, corner_radius=19, fg_color=state_color, text=None)
statuslight.grid(row=6, column=0, padx=(200, 0), pady=(0, 10), sticky="w")

#%% Camera View Section
camview = customtkinter.CTkFrame(master=root, corner_radius=0, fg_color=background_color)
camview.grid(row=0, column=1, padx=0, pady=0, sticky="")

light_image = Image.open('picture.jpeg')  

my_image = customtkinter.CTkImage(light_image=light_image, size=(640/camscale, 420/camscale))  # Pas de grootte aan naar wens

image_label = customtkinter.CTkLabel(camview, image=my_image, text="")
image_label.image = my_image
image_label.grid(row=0, column=0, padx=(20,0), sticky="")

#%% next placement
placement = customtkinter.CTkFrame(master=root, width=420, height=830, fg_color="#5E3E2C")
placement.grid(row=0, column=2, padx=20, pady=(10,0))
placement.grid_propagate(False)

box = customtkinter.CTkLabel(master=placement, corner_radius=10, text="", width=400, height=400, fg_color='orange')
box.grid(row=0, column=0, padx=(10,0), pady=(10,0), sticky="n")

box2 = customtkinter.CTkLabel(master=placement, corner_radius=10, text="", width=400, height=400, fg_color='orange')
box2.grid(row=1, column=0, padx=(10,0), pady=(10,0), sticky="n")

#-----placemets------
p1nw = customtkinter.CTkLabel(master=box, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p1nw.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

p1sw = customtkinter.CTkLabel(master=box, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p1sw.grid(row=0, column=0, padx=5, pady=5, sticky="sw")

p1se = customtkinter.CTkLabel(master=box, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p1se.grid(row=0, column=0, padx=5, pady=5, sticky="se")

p1ne = customtkinter.CTkLabel(master=box, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p1ne.grid(row=0, column=0, padx=5, pady=5, sticky="ne")

p2nw = customtkinter.CTkLabel(master=box2, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p2nw.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

p2sw = customtkinter.CTkLabel(master=box2, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p2sw.grid(row=0, column=0, padx=5, pady=5, sticky="sw")

p2se = customtkinter.CTkLabel(master=box2, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p2se.grid(row=0, column=0, padx=5, pady=5, sticky="se")

p2ne = customtkinter.CTkLabel(master=box2, corner_radius=10, text="", width=190, height=190, fg_color=button_color)
p2ne.grid(row=0, column=0, padx=5, pady=5, sticky="ne")

#%% progress
progress = customtkinter.CTkFrame(master=root, fg_color=frame_color)
progress.grid(row=0, column=3, padx=0, pady=0, sticky="nswe")
progress.grid_rowconfigure(0, weight=20)
progress.grid_rowconfigure(1, weight=1)

progressbar = customtkinter.CTkProgressBar(master=progress, corner_radius=5, orientation="vertical", width=100)
progressbar.grid(row=0, column=0, pady=(10,0), padx=10, sticky="ns")
progressbar.set(percentage_msg)

percentage_value=percentage_msg*100
percentage = customtkinter.CTkLabel(master=progress, text=f"{percentage_value}%", font=(font, fontsize), fg_color=frame_color)
percentage.grid(row=1, column=0, padx=0, pady=20, sticky="n")

root.mainloop()
