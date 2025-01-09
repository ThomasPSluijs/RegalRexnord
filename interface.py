import customtkinter
import tkinter as tk
from PIL import Image
from functools import partial
import time
from boxing_machine import BoxingMachine
import threading
import logging
import numpy as np


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class UserInterface:
    def __init__(self, root, on_close_callback=None):
        # Initialiseer de GUI-elementen
        self.root = root
        self.on_close_callback = on_close_callback

        self.percentage_msg = 0.0
        self.start_button_msg = "start"
        self.start_button = True

        self.font = "Century Regular"
        self.fontsize = 20

        self.background_color = ['gray92', 'gray14']
        self.button_color = ['#0C955A', '#106A43']
        self.frame_color = ['gray86', 'gray17']
        self.state_color = "red"
        self.start_button_color = self.button_color 

        self.leftbar_button_width = 160
        self.camscale = 1.3


        '''setup robot and machine class'''
        robot_ip = "192.168.0.1"  #Define ip
        self.machine = BoxingMachine(robot_ip, interface=self) #Create and start BoxingMachine


        self.setup_ui() #setup UI


        self.started_before = False #if not started before, a start thread will be started to start the machine, otherwise, resume will be used


        '''start display thread to start showing images'''
        #start display thread
        self.display_thread = threading.Thread(target=self.update_live_feed, args=(self.machine.camera,), daemon=True) 
        self.display_thread.start() 

        #start update placementes thread. looks for updates regarding the placing of parts
        self.update_placements_thread = threading.Thread(target=self.update_placements, daemon=True)
        self.update_placements_thread.start()



    '''function that gets called when stop/start button gets pressed. stops or starts the machine'''
    def start_button_pressed(self):
        #start packing
        if self.start_button == True:
    

            print('packing')
            self.hoisting_mode.configure(state="disabled")
            self.running_mode.configure(state="disabled")
            #self.partselection.configure(state="disabled")
            
            self.start_button_msg = "stop"
            self.start_button_color = "red"

            self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)


            #calls a thread to start running the machine. if started before, just resume
            if not self.started_before: threading.Thread(target=self.machine.start, daemon=True).start()
            else: self.machine.resume()

            if not self.started_before: self.started_before=True

            self.start_button = False

        else:
            print("stopped")

            #pause boxing machine. pausing for now instead of stopping
            self.machine.pause()

            self.hoisting_mode.configure(state="enabled")
            self.running_mode.configure(state="enabled")
            #self.partselection.configure(state="enabled")

            self.start_button_msg = "start"
            self.start_button_color = '#106A43'

            self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)

            self.start_button = True



    '''update placementes of parts on the display'''
    def update_placements(self):
        while True:
        # Reset alle labels eerst, zodat ze niet over elkaar heen staan
            placements,box_no,boxes_full = 0,0,0
            with self.machine.thread_lock:
                placements = self.machine.current_part_number 
                box_no = self.machine.current_box
                boxes_full = self.machine.boxes_are_full
            
            if boxes_full:
                 self.started_before = False
                 logging.info("boxes are full")
                 self.start_button_msg = "start"
                 self.start_button_color = '#106A43'
                 self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)
                 self.machine.boxes_are_full = False
            
            totalplacements = self.machine.total_parts * 2
            progress = placements / totalplacements

            self.progressbar.set(progress)
            self.percentage_value = int(progress*100)
            self.percentage.configure(text=f"{self.percentage_value}%")
            time.sleep(0.5)

    #idk man
    def update_activity(self, activity_msg):
         self.activity.configure(text=activity_msg)
        

    #updates images on the interface that have been taking by the camera 
    def update_live_feed(self, camera_position):
        logging.info("Starting display thread...")
        numpy_image = None
        while camera_position.display_thread_running:
            with camera_position.frame_lock:  # Access the frame safely
                if camera_position.last_frame is not None:
                    numpy_image = camera_position.last_frame.copy()
            if numpy_image is not None:
                pil_image = Image.fromarray(numpy_image)
                self.my_image = customtkinter.CTkImage(light_image=pil_image, size=(640/self.camscale, 420/self.camscale))
                self.image_label.configure(image=self.my_image)
                self.image_label.image = self.my_image  # Houd een referentie vast
            time.sleep(0.05)  # Limit display thread to ~30 FPS
        logging.info("Stopping display thread...")



    #setup user interface with all the buttons and widgets etc
    def setup_ui(self):
        # Set appearance mode and theme
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        # Configure window
        self.root.attributes("-fullscreen", True)       #should be true and uncommented
        #self.root.geometry('1024x600')                      #should be deleted
        self.root.configure(bg='gray14')

        # Setup close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configure the Grid Layout
        self.root.grid_rowconfigure(0, weight=1)  # row for leftbar and camview
        self.root.grid_columnconfigure(0, weight=0)  # first column for leftbar
        self.root.grid_columnconfigure(1, weight=0)  # second column for camview
        self.root.grid_columnconfigure(2, weight=0)  # third column for next placement

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
            command=self.packing_mode_func  # Add functionality here
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
            command=self.running_mode_func  # Add functionality here
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
            command=self.start_button_pressed  # Add functionality here
        )
        self.start_but.grid(row=2, column=0, pady=(20, 0), padx=0, sticky="w")

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
        self.statuslight.grid(row=6, column=0, padx=(80, 0), pady=(0, 10), sticky="w")

        # Camera View Section
        self.camview = customtkinter.CTkFrame(master=self.root, corner_radius=0, fg_color=self.background_color)
        self.camview.grid(row=0, column=1, padx=0, pady=0, sticky="")


        height, width = 420, 640  # Define the size of the image
        yellow_color = [255, 255, 0]  # RGB values for yellow
        numpy_image = np.full((height, width, 3), yellow_color, dtype=np.uint8)

        # Convert the NumPy array to a PIL image
        pil_image = Image.fromarray(numpy_image)
        self.my_image = customtkinter.CTkImage(light_image=pil_image, size=(640 / self.camscale, 420 / self.camscale))

        self.image_label = customtkinter.CTkLabel(self.camview, image=self.my_image, text="")
        self.image_label.image = self.my_image
        self.image_label.grid(row=0, column=0, padx=(20, 0), sticky="")

        # Progress Section
        self.progress = customtkinter.CTkFrame(master=self.root, fg_color=self.frame_color)
        self.progress.grid(row=0, column=2, padx=(30,0), pady=0, sticky="nswe")
        self.progress.grid_rowconfigure(0, weight=20)
        self.progress.grid_rowconfigure(1, weight=1)

        self.progressbar = customtkinter.CTkProgressBar(master=self.progress, corner_radius=5, orientation="vertical", width=100)
        self.progressbar.grid(row=0, column=0, pady=(10, 0), padx=10, sticky="ns")
        self.progressbar.set(self.percentage_msg)

        percentage_value = self.percentage_msg * 100
        self.percentage = customtkinter.CTkLabel(master=self.progress, text=f"{percentage_value}%", font=(self.font, self.fontsize), fg_color=self.frame_color)
        self.percentage.grid(row=1, column=0, padx=0, pady=20, sticky="n")



    #gets called when windows is closed. this function will kill all connections with camera's, robots and stop threads
    def on_closing(self):
        if self.on_close_callback:
            self.on_close_callback()

        #stop threads, stop robot control, stop camera stream etc
        self.machine.camera.stop_display_thread()
        self.machine.stop()
        self.display_thread.join()
        self.root.quit()


    #gets called when running_mode button is pressed. puts the robot in correct starting position
    def running_mode_func(self):
            #go to start position
            print('moving to start position')
            move_to_start_pos_t = threading.Thread(target=self.machine.normal_mode, daemon=True) 
            move_to_start_pos_t.start() 

    #gets called when packing mode is called. puts robot in packing mode
    def packing_mode_func(self):
            #go to packing place
            print('moving to packing position')
            move_to_pack_pos_t = threading.Thread(target=self.machine.packing_mode, daemon=True) 
            move_to_pack_pos_t.start() 

        



