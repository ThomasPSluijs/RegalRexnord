from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Rectangles (parts) with unique IDs
rectangles = [(170, 185), (170, 185), (170, 185), (170, 185)]
rectangles_with_ids = [(i, *rect) for i, rect in enumerate(rectangles)]

# Bins (boxes)
bins = [(365, 365), (365, 365)]

# Initialize the packer
packer = newPacker()

# Add rectangles to the packing queue with IDs
for rid, width, height in rectangles_with_ids:
    packer.add_rect(width, height, rid)

# Add bins where the rectangles will be placed
for b in bins:
    packer.add_bin(*b)

# Start packing
packer.pack()

# Visualization function
def visualize_packing(packer, bins):
    # Create subplots dynamically based on the number of used bins
    num_bins = len(packer)  # Only visualize bins that are used
    fig, axes = plt.subplots(1, num_bins, figsize=(5 * num_bins, 5))

    # Ensure axes is iterable even if there's only one bin
    if num_bins == 1:
        axes = [axes]

    # Iterate over each bin
    for i, abin in enumerate(packer):
        ax = axes[i]
        ax.set_xlim(0, abin.width)
        ax.set_ylim(0, abin.height)
        ax.set_title(f"Box {i + 1}")
        ax.set_aspect('equal')
        ax.invert_yaxis()  # Align (0,0) to top-left as in most packing visualizations

        # Draw the bin
        ax.add_patch(patches.Rectangle((0, 0), abin.width, abin.height, edgecolor="black", fill=None))

        # Draw each rectangle in the bin
        for rect in abin:
            x, y = rect.x, rect.y
            w, h = rect.width, rect.height
            rid = rect.rid  # Retrieve the ID of the rectangle
            color = f"C{rid % 10}"  # Unique color for each rectangle
            ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor="black", facecolor=color, alpha=0.5))
            ax.text(x + w / 2, y + h / 2, f"{rid}", color="black", ha="center", va="center")

        ax.set_xlabel("Width (mm)")
        ax.set_ylabel("Height (mm)")

    plt.tight_layout()
    plt.show()


# Call the visualization function
visualize_packing(packer, bins)
