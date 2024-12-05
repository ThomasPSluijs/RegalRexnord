import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Box:
    def __init__(self, total_boxes, box_centers, box_size):
        self.total_boxes = total_boxes
        self.box_centers = box_centers
        self.box_size = box_size



class Part:
    def __init__(self, product_size):
        self.product_size = product_size
        self.part_size_x = product_size[0]
        self.part_size_y = product_size[1]
        self.part_size_z = product_size[2]



class Pack_Box():
    def __init__(self, box, part):
        self.box = box
        self.part = part

    def get_pack_pos(self):
        pass


box = Box(total_boxes=2, box_centers=[(100,200), (100, 400)], box_size=(365,365,170))
part = Part((187,170,13))

pack_box = Pack_Box(box=box, part=part)




