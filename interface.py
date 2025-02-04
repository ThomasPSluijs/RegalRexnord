import customtkinter
import tkinter as tk
from PIL import Image
from functools import partial
import time
from boxing_machine import BoxingMachine
import threading
import logging
import numpy as np
from conveyor import Conveyor
import cv2
import subprocess
from configuration import*


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


        '''setup UI parameters'''
        self.percentage_msg = 0.0
        self.start_button_msg = "start"
        self.start_button = True

        self.stop_button_msg = "stop"

        self.font = "Century Regular"
        self.fontsize = 20

        self.background_color = ['gray92', 'gray14']
        self.button_color = ['#0C955A', '#106A43']
        self.frame_color = ['gray86', 'gray17']
        self.state_color = "red"
        self.start_button_color = self.button_color 

        self.leftbar_button_width = 160
        self.camscale = 1

        self.machine_run_t = None #placeholder for machine thread
        self.stop_event = threading.Event() #event to signal thread to stop



        '''setup robot and machine class'''
        robot_ip = "192.168.0.1"  #Define ip
        self.machine = BoxingMachine(robot_ip, interface=self) #Create and start BoxingMachine

        '''start conveyer'''
        self.conveyor = Conveyor()
       # conveyer_start = threading.Thread(target=self.conveyor.run, args=(self.machine.robot,),daemon=True)
        #conveyer_start.start()


        self.setup_ui() #setup UI


        self.started_before = False #if not started before, a start thread will be started to start the machine, otherwise, resume will be used
        self.stopped = False


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
            logging.info("start/resume button pressed")
            self.update_status("running/packing")

            self.hoisting_mode.configure(state="disabled")
            self.running_mode.configure(state="disabled")

            self.start_button_msg = "pause"
            self.start_button_color = "red"
            self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)
            self.state_color = "green"

            # Update the color of the statuslight
            self.statuslight.configure(fg_color=self.state_color)

            #calls a thread to start running the machine. if started before, just resume
            if self.started_before == False: 
                logging.info("start new machine thread!")
                self.machine_run_t = threading.Thread(target=self.machine.start, daemon=True)
                self.machine_run_t.start()
            else: self.machine.resume()

            if self.started_before == False: self.started_before=True

            self.start_button = False

        else:
            self.update_status("paused")

            #pause boxing machine. pausing for now instead of stopping
            self.machine.pause()

            self.hoisting_mode.configure(state="disabled")
            self.running_mode.configure(state="disabled")

            self.start_button_msg = "start/resume"
            self.start_button_color = '#106A43'
            self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)

            self.state_color = "red"

            # Update the color of the statuslight
            self.statuslight.configure(fg_color=self.state_color)

            self.start_button = True


    #check if stop button pressed
    def stop_button_pressed(self):
        self.update_status("Stopped")


        #change pause button
        self.hoisting_mode.configure(state="enabled")
        self.running_mode.configure(state="enabled")
        self.start_button_msg = "start"
        self.start_button_color = '#106A43'
        self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)
        self.start_button = True
        self.state_color = "red"

       # Update the color of the statuslight
        self.statuslight.configure(fg_color=self.state_color)


        self.update_status("stopped: replace boxes before starting")
        self.started_before = False
        self.stopped = True

    def restart_button_pressed(self):
        logging.error("restart button pressed")
        """Herstart de service 'regalrexnordrobot'."""
        try:
            # Voer het commando uit
            subprocess.run(["sudo", "service", "regalrexnordrobot", "restart"], check=True)
            print("Service regalrexnordrobot is succesvol herstart.")
        except subprocess.CalledProcessError as e:
            print(f"Er trad een fout op bij het herstarten van de service: {e}")
        except Exception as e:
            print(f"Een onverwachte fout is opgetreden: {e}")

    '''update placementes of parts on the display'''
    def update_placements(self):
        while True:
        # Reset alle labels eerst, zodat ze niet over elkaar heen staan
            #placements,box_no,boxes_full = 0,0,0
            with self.machine.thread_lock:
                boxes_full = self.machine.boxes_are_full
                totalplacements = self.machine.total_parts
                placements = self.machine.placements
                #logging.info(f"placements: {placements}")
            if boxes_full:
                 self.started_before = False
                 logging.info("boxes are full")
                 self.start_button_msg = "start"
                 self.start_button_color = '#106A43'
                 self.start_but.configure(text=self.start_button_msg, fg_color=self.start_button_color, hover_color=self.start_button_color)
                 with self.machine.thread_lock:
                    self.machine.boxes_are_full = False
                 self.stopped = True

            with self.machine.thread_lock:
                box_no = self.machine.current_box
        
                part_box_0 = self.machine.last_part_box_0
                part_box_1 = self.machine.last_part_box_1
            

            if placements == 0: progress = 0
            else:
                progress = placements / totalplacements

            if part_box_0 == 0:
                part_box_0 =  {"box_number": 0,
                    "part_number": 0,
                    "layer_number": 1,
                    "partcount": 0}
            if part_box_1 == 0:
                part_box_1 =  {"box_number": 0,
                    "part_number": 0,
                    "layer_number": 1,
                    "partcount": 0}
                
            self.progressbar.set(progress)
            self.percentage_value = int(progress*100)
            self.percentage.configure(text=f"{self.percentage_value}%")
            #logging.info(f"placements: {placements}  totalplacementes: {totalplacements}")

            if box_no == 0:
                box1state = "filling" #other states should be: empty, full or error
                box1partnr = part_box_0['partcount']
                box1layernr = part_box_0['layer_number']
                self.boxstate_text1.configure(text=(f"box 1:\n status: {box1state}\n parts: {box1partnr}\n layer: {box1layernr}"))
                
            if box_no == 1:
                box2state = "filling" #other states should be: empty, full or error
                box1state = "full"
                box2partnr = part_box_1['partcount']
                box2layernr = part_box_1['layer_number']
                self.boxstate_text1.configure(text=(f"box 1:\n status: {box1state}\n parts: {box1partnr}\n layer: {box1layernr}"))
                self.boxstate_text2.configure(text=(f"box 2:\n status: {box2state}\n parts: {box2partnr}\n layer: {box2layernr}"))
            
            if boxes_full:
                box2state = "full"
                self.boxstate_text2.configure(text=(f"box 2:\n status: {box2state}\n parts: {box2partnr}\n layer: {box2layernr}"))
                time.sleep(0.5)



    #updates images on the interface that have been taking by the camera 
    def update_live_feed(self, camera_position):
        logging.info("Starting display thread...")
        numpy_image = None
        while camera_position.display_thread_running:
            with camera_position.frame_lock:  # Access the frame safely
                if camera_position.last_frame is not None:
                    numpy_image = camera_position.last_frame.copy()
            if numpy_image is not None:
                rgb_image = cv2.cvtColor(numpy_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)
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
        self.root.geometry('1024x600')                      #should be deleted
        self.root.configure(bg='gray14')

        # Setup close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configure the Grid Layout
        self.root.grid_rowconfigure(0, weight=1)  # row for leftbar and camview
        self.root.grid_columnconfigure(0, weight=0)  # first column for leftbar
        self.root.grid_columnconfigure(1, weight=0)  # second column for camview
        self.root.grid_columnconfigure(2, weight=1)  # third column for next placement
        self.root.grid_columnconfigure(3, weight=0)  # third column for next placement
        
        # Left Bar (Sidebar)
        self.leftbar = customtkinter.CTkFrame(master=self.root, corner_radius=0)
        self.leftbar.grid(row=0, column=0, sticky="nswe")

        self.leftbar.grid_rowconfigure(0, weight=0)  # Rows for buttons at the top
        self.leftbar.grid_rowconfigure(1, weight=0)
        self.leftbar.grid_rowconfigure(2, weight=0)
        self.leftbar.grid_rowconfigure(3, weight=0)
        self.leftbar.grid_rowconfigure(4, weight=0)  # Empty space below labels (bottom space)
        self.leftbar.grid_rowconfigure(5, weight=1)
        self.leftbar.grid_rowconfigure(6, weight=0)



        # hoisting mode button
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

        #running mode button
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

        #add a start/pause button
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

        #add a stop button
        self.stop_but = customtkinter.CTkButton(
            master=self.leftbar,
            corner_radius=0,
            text=self.stop_button_msg,
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.start_button_color,
            anchor="w",
            command=self.stop_button_pressed  # Add functionality here
        )
        self.stop_but.grid(row=3, column=0, pady=(20, 0), padx=0, sticky="w")

        self.restart_but = customtkinter.CTkButton(
            master=self.leftbar,
            corner_radius=0,
            text=("Restart"),
            font=(self.font, self.fontsize),
            width=self.leftbar_button_width,
            height=60,
            fg_color=self.start_button_color,
            anchor="w",
            command=self.restart_button_pressed  # Add functionality here
        )
        self.restart_but.grid(row=4, column=0, pady=(20, 0), padx=0, sticky="w")

        # Add Status Text at the Top Center
        self.status_text = customtkinter.CTkLabel(
            master=self.root,
            text="Status: Ready",
            font=(self.font, self.fontsize, "bold"),
            fg_color="transparent",
            text_color="white",
        )
        self.status_text.grid(row=0, column=1, pady=(10, 0), sticky="n")


        #add status
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
        self.camview.grid(row=0, column=1, padx=(20,0), pady=(30,0), sticky="")
        self.light_image = Image.open("Regal_Rexnord_Corporation_logo.jpg")  
        self.my_image = customtkinter.CTkImage(light_image=self.light_image, size=(640 / self.camscale, 420 / self.camscale))

        self.image_label = customtkinter.CTkLabel(self.camview, image=self.my_image, text="")
        self.image_label.image = self.my_image
        self.image_label.grid(row=0, column=0, padx=(20, 0), sticky="")

        self.boxstate = customtkinter.CTkLabel(self.camview, text="", fg_color="transparent")
        self.boxstate.grid(row=1, column=0, padx=0, pady=0, sticky="we")
        
        self.boxstate_text1 = customtkinter.CTkLabel(
            master=self.boxstate,
            text=(f"box 1:\n status: empty\n parts: 0\n layer: 1 "),
            font=(self.font, self.fontsize, "bold"),
            fg_color="transparent",
            text_color="white",
        )
        self.boxstate_text1.grid(row=1, column=0, padx=(120,0), sticky="nw")

        self.boxstate_text2 = customtkinter.CTkLabel(
            master=self.boxstate,
            text=(f"box 2:\n status: empty\n parts: 0\n layer: 1"),
            font=(self.font, self.fontsize, "bold"),
            fg_color="transparent",
            text_color="white",
        )
        self.boxstate_text2.grid(row=1, column=1, padx=(0,100), sticky="ne")


        # Progress Section
        self.progress = customtkinter.CTkFrame(master=self.root, fg_color=self.frame_color)
        self.progress.grid(row=0, column=3, padx=(30,0), pady=0, sticky="nswe")
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



    #update status text
    def update_status(self, new_status):
        """Update the status text displayed at the top center."""
        self.status_text.configure(text=new_status)



    #gets called when running_mode button is pressed. puts the robot in correct starting position
    def running_mode_func(self):
        #go to start position
        #print('moving to start position')
        move_to_start_pos_t = threading.Thread(target=self.machine.normal_mode, daemon=True) 
        move_to_start_pos_t.start() 

    #gets called when packing mode is called. puts robot in packing mode
    def packing_mode_func(self):
        #go to packing place
        #print('moving to packing position')
        move_to_pack_pos_t = threading.Thread(target=self.machine.packing_mode, daemon=True) 
        move_to_pack_pos_t.start() 
        



