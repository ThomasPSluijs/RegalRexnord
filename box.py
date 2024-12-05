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

            # Box dimensions
            box_length, box_width, box_height = self.box.box_size

            # Part dimensions
            part_length = self.part.part_size_x
            part_width = self.part.part_size_y
            part_height = self.part.part_size_z

            # Layer height and number of layers available
            layer_height = part_height
            layers = floor(box_height / layer_height)
            logging.info(f"Total layers available: {layers}")

            # Calculate parts in non-rotated and rotated orientation
            parts_in_row_non_rot = floor(box_length / part_length)
            parts_in_col_non_rot = floor(box_width / part_width)

            parts_in_row_rot = floor(box_length / part_width)
            parts_in_col_rot = floor(box_width / part_length)

            max_parts_in_layer = 0
            best_configuration = None

            

            # Try every combination of non-rotated and rotated parts
            for row_non_rot in range(parts_in_row_non_rot + 1):
                for col_non_rot in range(parts_in_col_non_rot + 1):
                    remaining_length = box_length - (row_non_rot * part_length)
                    remaining_width = box_width - (col_non_rot * part_width)

                    # How many rotated parts fit in the remaining space
                    row_rot = floor(remaining_length / part_width)
                    col_rot = floor(remaining_width / part_length)

                    fit = (row_non_rot * col_non_rot) + (row_rot * col_rot)
                    if fit > max_parts_in_layer:
                        max_parts_in_layer = fit
                        best_configuration = (row_non_rot, col_non_rot, row_rot, col_rot)

            logging.info(f"Max parts per layer: {max_parts_in_layer}")

            # Place the parts based on the best configuration found
            for layer in range(layers):
                row_non_rot, col_non_rot, row_rot, col_rot = best_configuration

                # Place non-rotated parts
                for row in range(row_non_rot):
                    for col in range(col_non_rot):
                        x = box_center[0] - box_length / 2 + (row + 0.5) * part_length
                        y = box_center[1] - box_width / 2 + (col + 0.5) * part_width
                        z = layer * layer_height
                        positions.append((x, y, z))
                        rotations.append(0)  # Non-rotated part
                        layers_info.append(layer + 1)

                # Place rotated parts
                for row in range(row_rot):
                    for col in range(col_rot):
                        x = box_center[0] - box_length / 2 + (row + 0.5) * part_width
                        y = box_center[1] - box_width / 2 + (col + 0.5) * part_length
                        z = layer * layer_height
                        positions.append((x, y, z))
                        rotations.append(90)  # Rotated part
                        layers_info.append(layer + 1)

        return positions, rotations, layers_info


# Create instances for box and part
box = Box(total_boxes=2, box_centers=[(100, 200), (100, 400)], box_size=(365, 365, 170))
part = Part((170, 170, 13))

# Initialize Pack_Box and get packing positions
pack_box = Pack_Box(box=box, part=part)
positions, rotations, layers = pack_box.get_pack_pos()

# Print the placement positions, rotations, and layers
print("Placement Coordinates, Rotations, and Layers:")
for pos, rot, layer in zip(positions, rotations, layers):
    print(f"Position: {pos}, Rotation: {rot}°, Layer: {layer}")
