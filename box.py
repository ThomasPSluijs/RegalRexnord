import logging
from math import floor

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Box:
    def __init__(self, total_boxes, box_centers, box_size):
        self.total_boxes = total_boxes
        self.box_centers = box_centers
        self.box_size = box_size  # (length, width, height)


class Part:
    def __init__(self, product_size):
        self.product_size = product_size
        self.part_size_x = product_size[0]
        self.part_size_y = product_size[1]
        self.part_size_z = product_size[2]


class Pack_Box:
    def __init__(self, box, part):
        self.box = box
        self.part = part

    def get_pack_pos(self):
        positions = []
        rotations = []
        layers_info = []

        for box_index in range(self.box.total_boxes):
            box_center = self.box.box_centers[box_index]
            logging.info(f"Packing in Box {box_index + 1} at center {box_center}")

            # Determine dimensions of the box
            box_length, box_width, box_height = self.box.box_size

            # Determine possible orientations for placing parts
            part_orientations = [
                (self.part.part_size_x, self.part.part_size_y, 0),   # Default orientation
                (self.part.part_size_y, self.part.part_size_x, 90),  # Rotated orientation
            ]

            

            # Find optimal orientation
            max_parts_per_layer = 0
            best_orientation = None
            for part_length, part_width, rotation in part_orientations:
                parts_in_length = floor(box_length / part_length)
                parts_in_width = floor(box_width / part_width)
                parts_per_layer = parts_in_length * parts_in_width
                if parts_per_layer > max_parts_per_layer:
                    max_parts_per_layer = parts_per_layer
                    best_orientation = (part_length, part_width, rotation)

            part_length, part_width, rotation = best_orientation
            logging.info(f"Best orientation: {part_length}x{part_width} with rotation {rotation}°")
            logging.info(f"Max parts per layer: {max_parts_per_layer}")





            # Generate placement positions layer by layer
            parts_in_length = floor(box_length / part_length)
            parts_in_width = floor(box_width / part_width)
            layer_height = self.part.part_size_z
            layers = floor(box_height / layer_height)

            for layer in range(layers):
                for row in range(parts_in_length):
                    for col in range(parts_in_width):
                        x = box_center[0] - box_length / 2 + (row + 0.5) * part_length
                        y = box_center[1] - box_width / 2 + (col + 0.5) * part_width
                        z = layer * layer_height
                        positions.append((x, y, z))
                        rotations.append(rotation)
                        layers_info.append(layer + 1)

                        logging.debug(
                            f"Placed part at ({x:.1f}, {y:.1f}, {z:.1f}) "
                            f"with rotation {rotation}° in Box {box_index + 1}, Layer {layer + 1}"
                        )

        return positions, rotations, layers_info


# Create instances for box and part
box = Box(total_boxes=2, box_centers=[(100, 200), (100, 400)], box_size=(365, 365, 170))
part = Part((187, 170, 13))

# Initialize Pack_Box and get packing positions
pack_box = Pack_Box(box=box, part=part)
positions, rotations, layers = pack_box.get_pack_pos()

# Print the placement positions, rotations, and layers
#print("Placement Coordinates, Rotations, and Layers:")
#for pos, rot, layer in zip(positions, rotations, layers):
#    print(f"Position: {pos}, Rotation: {rot}°, Layer: {layer}")
