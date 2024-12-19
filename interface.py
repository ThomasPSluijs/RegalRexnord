import customtkinter
import tkinter as tk
from PIL import Image
from functools import partial
import time
from main import *

class UserInterface:
    def start(self):
        #start packing
        if self.start_button == True:
            print('packing')
            self.hoisting_mode.configure(state="disabled")
            self.running_mode.configure(state="disabled")
            self.partselection.configure(state="disabled")
            
            self.start_button_msg = "stop"
            self.start_button_color = "red"

            self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)


            self.start_button = False

            # Define configurations
            robot_ip = "192.168.0.1"

            # Create and start BoxingMachine
            machine = BoxingMachine(robot_ip)

        else:
            print("stopped")
            self.hoisting_mode.configure(state="enabled")
            self.running_mode.configure(state="enabled")
            self.partselection.configure(state="enabled")

            self.start_button_msg = "start"
            self.start_button_color = '#106A43'

            self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)

            self.start_button = True

    def update_placements(self, placements):
        # Reset alle labels eerst, zodat ze niet over elkaar heen staan
        print(placements)
        self.p1nw.grid_remove()
        self.p1sw.grid_remove()
        self.p1se.grid_remove()
        self.p1ne.grid_remove()
        self.p2nw.grid_remove()
        self.p2sw.grid_remove()
        self.p2se.grid_remove()
        self.p2ne.grid_remove()
        
        if placements <= 56:
            if placements % 4 == 1:
                self.p1ne.grid()
            elif placements % 4 == 2:
                self.p1nw.grid()
            elif placements % 4 == 3:
                self.p1sw.grid()
            elif placements % 4 == 0:
                self.p1se.grid()
        if placements > 56:
            if placements % 4 == 1:
                self.p2ne.grid()
            elif placements % 4 == 2:
                self.p2nw.grid()
            elif placements % 4 == 3:
                self.p2sw.grid()
            elif placements % 4 == 0:
                self.p2se.grid()

    def update_activity(self, activity_msg):
         self.activity.configure(text=activity_msg)
        
    def update_progressbar(self, progress, totalplacements):
            progress = progress / totalplacements
            self.progressbar.set(progress)
            self.percentage_value = int(progress*100)
            self.percentage.configure(text=f"{self.percentage_value}%")

        

    def update_live_feed(self):
        try:
            # Voeg een timestamp toe aan het pad om caching te voorkomen
            file_path = f"User Interface/Pictures/picture.jpeg?{int(time.time())}"

            # Herlaad de afbeelding
            new_image = Image.open(file_path.split('?')[0])  # Alleen het pad gebruiken zonder de query
            self.my_image = customtkinter.CTkImage(light_image=new_image, size=(640/self.camscale, 420/self.camscale))

            # Update het label met de nieuwe afbeelding
            self.image_label.configure(image=self.my_image)
            self.image_label.image = self.my_image  # Houd een referentie vast
            print("Afbeelding succesvol geüpdatet")
        except FileNotFoundError:
            print("Fout: De afbeelding is niet gevonden.")
        except Exception as e:
            print(f"Er is een fout opgetreden: {e}")
        
        # Roep deze functie opnieuw aan na 2000 ms (2 seconden)
        self.camview.after(2000, self.update_live_feed)


    def __init__(self, root, on_close_callback=None):
        # Initialiseer de GUI-elementen
        self.root = root
        self.on_close_callback = on_close_callback

        self.percentage_msg = 0.3
        self.start_button_msg = "start"
        self.start_button = True

        self.font = "Century Regular"
        self.fontsize = 20

        self.background_color = ['gray92', 'gray14']
        self.button_color = ['#0C955A', '#106A43']
        self.frame_color = ['gray86', 'gray17']
        self.state_color = "red"
        self.start_button_color = self.button_color 

        self.leftbar_button_width = 250
        self.camscale = 1

        self.setup_ui()

    def setup_ui(self):
        # Set appearance mode and theme
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        # Configure window
        self.root.attributes("-fullscreen", False)       #should be true
        self.root.configure(bg='gray14')

        # Setup close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configure the Grid Layout
        self.root.grid_rowconfigure(0, weight=1)  # row for leftbar and camview
        self.root.grid_columnconfigure(0, weight=0)  # first column for leftbar
        self.root.grid_columnconfigure(1, weight=0)  # second column for camview
        self.root.grid_columnconfigure(2, weight=0)  # third column for next placement
        self.root.grid_columnconfigure(3, weight=0)  # fourth column for progress

        # Left Bar (Sidebar)
        self.leftbar = customtkinter.CTkFrame(master=self.root, corner_radius=0)
        self.leftbar.grid(row=0, column=0, sticky="nswe")

        self.leftbar.grid_rowconfigure(0, weight=0)  # Rows for buttons at the top
        self.leftbar.grid_rowconfigure(1, weight=0)
        self.leftbar.grid_rowconfigure(2, weight=0)
        self.leftbar.grid_rowconfigure(3, weight=0)
        self.leftbar.grid_rowconfigure(4, weight=1)  # Empty space below labels (bottom space)
        self.leftbar.grid_rowconfigure(5, weight=0)
        self.leftbar.grid_rowconfigure(6, weight=0)

        # Buttons in Left Bar
        self.hoisting_mode = customtkinter.CTkButton(
            master=self.leftbar,
            corner_radius=0,
            text="hoisting mode",
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.button_color,
            anchor="w",
            command=packing_mode_func  # Add functionality here
        )
        self.hoisting_mode.grid(row=0, column=0, pady=(20, 0), padx=0, sticky="w")

        self.running_mode = customtkinter.CTkButton(
            master=self.leftbar,
            corner_radius=0,
            text="running mode",
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.button_color,
            anchor="w",
            command=running_mode_func  # Add functionality here
        )
        self.running_mode.grid(row=1, column=0, pady=(20, 0), padx=0, sticky="w")

        self.start_but = customtkinter.CTkButton(
            master=self.leftbar,
            corner_radius=0,
            text=self.start_button_msg,
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.start_button_color,
            anchor="w",
            command=self.start  # Add functionality here
        )
        self.start_but.grid(row=2, column=0, pady=(20, 0), padx=0, sticky="w")

        def dropdown_callback(selected_value):
            dropdown(selected_value, parts)

        parts = ["select a value", "big blue", "small blue"]

        self.partselection = customtkinter.CTkOptionMenu(
            master=self.leftbar,
            corner_radius=0,
            values=parts,
            font=(self.font, self.fontsize),
            dropdown_font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.button_color,
            anchor="w",
            button_color=self.button_color,
            button_hover_color=self.button_color,
            dropdown_hover_color=self.button_color,
            command=dropdown_callback,
        )
        self.partselection.grid(row=3, column=0, pady=(20, 0), padx=0, sticky="w")
        
        self.activity = customtkinter.CTkLabel(
            master=self.leftbar,
            text="power off",
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.frame_color,
            anchor="w"
        )
        self.activity.grid(row=5, column=0, pady=(0, 10), padx=(5, 0), sticky="w")

        self.status = customtkinter.CTkLabel(
            master=self.leftbar,
            text="status:",
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.frame_color,
            anchor="w"
        )
        self.status.grid(row=6, column=0, pady=(0, 10), padx=(5, 0), sticky="w")

        self.statuslight = customtkinter.CTkLabel(
            master=self.leftbar,
            width=38,
            height=38,
            corner_radius=19,
            fg_color=self.state_color,
            text=None
        )
        self.statuslight.grid(row=6, column=0, padx=(200, 0), pady=(0, 10), sticky="w")

        # Camera View Section
        self.camview = customtkinter.CTkFrame(master=self.root, corner_radius=0, fg_color=self.background_color)
        self.camview.grid(row=0, column=1, padx=0, pady=0, sticky="")

        self.light_image = Image.open("User Interface\Pictures\Foto.jpeg")  
        self.my_image = customtkinter.CTkImage(light_image=self.light_image, size=(640/self.camscale, 420/self.camscale))

        self.image_label = customtkinter.CTkLabel(self.camview, image=self.my_image, text="")
        #self.image_label.image = self.my_image
        self.image_label.grid(row=0, column=0, padx=(20, 0), sticky="")

        self.placement = customtkinter.CTkFrame(master=self.root, width=420, height=830, fg_color="#5E3E2C")
        self.placement.grid(row=0, column=2, padx=20, pady=(10,0))
        self.placement.grid_propagate(False)

        self.box = customtkinter.CTkFrame(master=self.placement, corner_radius=10, width=400, height=400, fg_color='orange')
        self.box.grid(row=0, column=0, padx=(10,0), pady=(10,0), sticky="")
        self.box.grid_propagate(False)
        self.box2 = customtkinter.CTkFrame(master=self.placement, corner_radius=10, width=400, height=400, fg_color='orange')
        self.box2.grid(row=1, column=0, padx=(10,0), pady=(10,0), sticky="n")
        self.box2.grid_propagate(False)

        self.box.grid_rowconfigure(0, weight=1)  
        self.box.grid_rowconfigure(1, weight=1)  
        self.box.grid_columnconfigure(0, weight=1)  
        self.box.grid_columnconfigure(1, weight=1)  

        self.box2.grid_rowconfigure(0, weight=1)  
        self.box2.grid_rowconfigure(1, weight=1)  
        self.box2.grid_columnconfigure(0, weight=1)  
        self.box2.grid_columnconfigure(1, weight=1)

        #-----placemets------
        self.p1nw = customtkinter.CTkLabel(master=self.box, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p1nw.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

        self.p1sw = customtkinter.CTkLabel(master=self.box, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p1sw.grid(row=1, column=0, padx=5, pady=5, sticky="sw")

        self.p1se = customtkinter.CTkLabel(master=self.box, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p1se.grid(row=1, column=1, padx=5, pady=5, sticky="se")

        self.p1ne = customtkinter.CTkLabel(master=self.box, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p1ne.grid(row=0, column=1, padx=5, pady=5, sticky="ne")

        self.p2nw = customtkinter.CTkLabel(master=self.box2, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p2nw.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

        self.p2sw = customtkinter.CTkLabel(master=self.box2, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p2sw.grid(row=1, column=0, padx=5, pady=5, sticky="sw")

        self.p2se = customtkinter.CTkLabel(master=self.box2, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p2se.grid(row=1, column=1, padx=5, pady=5, sticky="se")

        self.p2ne = customtkinter.CTkLabel(master=self.box2, corner_radius=10, text="", width=190, height=190, fg_color=self.button_color)
        self.p2ne.grid(row=0, column=1, padx=5, pady=5, sticky="ne")

        # Progress Section
        self.progress = customtkinter.CTkFrame(master=self.root, fg_color=self.frame_color)
        self.progress.grid(row=0, column=3, padx=0, pady=0, sticky="nswe")
        self.progress.grid_rowconfigure(0, weight=20)
        self.progress.grid_rowconfigure(1, weight=1)

        self.progressbar = customtkinter.CTkProgressBar(master=self.progress, corner_radius=5, orientation="vertical", width=100)
        self.progressbar.grid(row=0, column=0, pady=(10, 0), padx=10, sticky="ns")
        self.progressbar.set(self.percentage_msg)

        percentage_value = self.percentage_msg * 100
        self.percentage = customtkinter.CTkLabel(master=self.progress, text=f"{percentage_value}%", font=(self.font, self.fontsize), fg_color=self.frame_color)
        self.percentage.grid(row=1, column=0, padx=0, pady=20, sticky="n")



    def on_closing(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.root.quit()

    # Define functions for button actions

def packing_mode_func():
        #go to packing place
        print('moving to packing position')

def running_mode_func():
        #go to start position
        print('moving to start position')


def dropdown(variable, values):
        if variable != None:
                if variable == "select a value":
                        print("select a value")
#below this you can set the variables for every part, at selected value put everything on zero or something.
#also search for "partlist" and add the names of the new parts there :)
                if variable == "big blue":
                        print("big blue")
                        #thickness = 3
                if variable == "small blue":
                        print("small blue")
