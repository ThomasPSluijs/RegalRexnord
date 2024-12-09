import logging
from math import floor

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



#class that stores information for the boxes:
#total boxes, box centers(in x,y) box bottom z, boxsize
class Box:
    def __init__(self, total_boxes, box_pos, box_size):
        self.total_boxes = total_boxes
        self.box_centers = box_pos # center x, center y, bottom z
        self.box_size = box_size  # (length, width, height)


#class that stores information about parts: 
#part size x, y and z
class Part:
    def __init__(self, product_size):
        self.product_size = product_size
        self.part_size_x = product_size[0]
        self.part_size_y = product_size[1]
        self.part_size_z = product_size[2]



#class that determines all the coordinates for the parts in the boxes. 
#in total 4 parts per box, two rotated 90 degrees
#total parts in height gets calculated
class Pack_Box:
    def __init__(self, box, part):
        #get box info
        self.box = box
        self.box_length, self.box_width, self.box_height = self.box.box_size
        
        #get part info
        self.part = part
        self.part_length = self.part.part_size_x
        self.part_width = self.part.part_size_y
        self.part_height = self.part.part_size_z


        #array with boxes and parts locations
        self.filled_boxes = []

    def get_pack_pos(self):
        #for loop to go throug boxes and fill boxes 1 by 1
        for box_index in range(self.box.total_boxes):
            #get box center
            box_center = self.box.box_centers[box_index]
            logging.info(f"Packing in Box {box_index + 1} at center {box_center}")

            #check total z parts per box
            total_z_parts = floor(self.box_height/self.part_height)
            logging.info(f"total z parts: {total_z_parts}")

            #set start z_pos at bototm of box
            z_pos = box_center[2]

            #array for adding part locations for this box
            part_positions_box = []

            #for loop to go through total z parts to fill a box
            for z in range(total_z_parts):
                #array to place four parts per layer
                for i in range(4):  # Only 4 parts for now
                    if i == 0:
                        # First part (top left)
                        x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2
                        y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2
                        rotation=0
                    elif i == 1:
                        # Second part (top right)
                        x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2
                        y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2
                        rotation=90
                    elif i == 2:
                        # Third part (bottom left)
                        x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2
                        y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2
                        rotation=90
                    elif i == 3:
                        # Fourth part (bottom right)
                        x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2
                        y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2
                        rotation=0

                    # Store the positions
                    part_positions_box.append((x_pos, y_pos, z_pos, rotation))

                #layer has been filled, increase z_pos for next layer    
                z_pos += self.part_height

            #add filled box to total boxes
            self.filled_boxes.append(part_positions_box)

        return self.filled_boxes


# Create instances for box and part.
#neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
box = Box(total_boxes=2, box_pos=[(0, 0, 0.1), [400,400, 0.1]], box_size=(365, 365, 170))

#needs: part width, part length, part height
part = Part((187, 170, 13))

# Initialize Pack_Box and get packing positions
pack_box = Pack_Box(box=box, part=part)
positions = pack_box.get_pack_pos()
logging.info(positions[0])
