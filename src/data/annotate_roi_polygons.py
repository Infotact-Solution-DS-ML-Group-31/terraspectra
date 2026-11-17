
from pathlib import Path
import json
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.path import Path as PolygonPath


DATA_DIR = Path("data/raw/tomato_botrytis")
OUTPUT_DIR = Path("data/processed/segmentation")
FIGURE_DIR = Path("outputs/figures")

BANDS = [69, 52, 18]

CLASS_CONFIG = {
    "2973": {1: "main_leaf"},
    "3079": {
        1: "lesion_bearing_stem",
        2: "comparison_stem"
    }
}

COLORS = {
    1: "lime",
    2: "cyan"
}


def load_rgb(image_id):
    file_path = DATA_DIR / f"{image_id}.npz"

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    with np.load(file_path) as data:
        cube = data["arr_0"].astype(np.float32)

    if cube.ndim != 3 or cube.shape[2] <= max(BANDS):
        raise ValueError(f"Unexpected cube shape: {cube.shape}")

    channels = []

    for band in BANDS:
        channel = cube[:, :, band]
        low, high = np.nanpercentile(channel, [2, 98])

        if high <= low:
            scaled = np.zeros_like(channel)
        else:
            scaled = np.clip(
                (channel - low) / (high - low), 0, 1
            )

        channels.append(scaled)

    return cube.shape[:2], np.stack(channels, axis=-1)


def annotate(image_id):
    class_names = CLASS_CONFIG[image_id]
    spatial_shape, rgb = load_rgb(image_id)

    operations = []
    vertices = []

    state = {
        "class_id": 1,
        "mode": "add",
        "finished": False
    }

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.imshow(rgb)
    ax.set_axis_off()

    completed_patches = []
    current_line = None

    def update_title():
        class_name = class_names[state["class_id"]]

        ax.set_title(
            f"Image {image_id} | Class: {class_name} | "
            f"Mode: {state['mode'].upper()}\n"
            "Click points | ENTER: finish polygon | "
            "U: undo | BACKSPACE: remove point | "
            "ESC: cancel | Q: save"
        )

        fig.canvas.draw_idle()

    def redraw():
        nonlocal current_line

        for patch in completed_patches:
            patch.remove()

        completed_patches.clear()

        if current_line is not None:
            current_line.remove()
            current_line = None

        for class_id, mode, polygon_vertices in operations:
            color = (
                COLORS[class_id]
                if mode == "add"
                else "red"
            )

            patch = Polygon(
                polygon_vertices,
                closed=True,
                facecolor=color,
                edgecolor=color,
                alpha=0.30,
                linewidth=2
            )

            ax.add_patch(patch)
            completed_patches.append(patch)

        if vertices:
            points = np.asarray(vertices)

            current_line, = ax.plot(
                points[:, 0],
                points[:, 1],
                "y-o",
                linewidth=2,
                markersize=5
            )

        update_title()

    def finish_polygon():
        if len(vertices) < 3:
            print("At least 3 points are required.")
            return

        operations.append((
            state["class_id"],
            state["mode"],
            np.asarray(vertices, dtype=np.float32).copy()
        ))

        print(
            f"Polygon completed: "
            f"{class_names[state['class_id']]}, "
            f"mode={state['mode']}, "
            f"vertices={len(vertices)}"
        )

        vertices.clear()
        redraw()

    def on_click(event):
        if event.inaxes != ax or event.button != 1:
            return

        if event.xdata is None or event.ydata is None:
            return

        vertices.append([event.xdata, event.ydata])

        redraw()

    def on_key(event):
        key = event.key

        if key in ("1", "2"):
            class_id = int(key)

            if class_id not in class_names:
                return

            if vertices:
                print(
                    "Finish the current polygon with ENTER "
                    "or cancel it with ESC before switching."
                )
                return

            state["class_id"] = class_id
            state["mode"] = "add"

            print(
                f"Selected class: {class_names[class_id]}"
            )

        elif key == "a":
            state["mode"] = "add"

        elif key == "e":
            state["mode"] = "erase"

        elif key in ("enter", "return"):
            finish_polygon()
            return

        elif key == "backspace":
            if vertices:
                vertices.pop()
                redraw()

        elif key == "escape":
            vertices.clear()
            redraw()
            print("Current polygon cancelled.")

        elif key == "u":
            if operations:
                operations.pop()
                redraw()
                print("Last completed polygon undone.")

        elif key == "q":
            if vertices:
                print(
                    "Finish the current polygon with ENTER "
                    "or cancel it with ESC before saving."
                )
                return

            state["finished"] = True
            plt.close(fig)
            return

        update_title()

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)

    print("\nANNOTATION INSTRUCTIONS")
    print("-----------------------")
    print("1 = Select class 1")
    if 2 in class_names:
        print("2 = Select class 2")
    print("Left mouse click = Add polygon point")
    print("ENTER = Finish current polygon")
    print("A = Add mode")
    print("E = Erase mode")
    print("U = Undo last completed polygon")
    print("BACKSPACE = Remove last point")
    print("ESC = Cancel current polygon")
    print("Q = Finish and save")
    print("\nClick points around the tissue boundary.")
    print("Press ENTER after placing the final point.\n")

    update_title()
    plt.show()

    if not operations:
        raise RuntimeError("No polygons were annotated.")

    rows, cols = spatial_shape
    yy, xx = np.mgrid[0:rows, 0:cols]

    points = np.column_stack((
        xx.ravel() + 0.5,
        yy.ravel() + 0.5
    ))

    raw_masks = {
        class_id: np.zeros(spatial_shape, dtype=bool)
        for class_id in class_names
    }

    for class_id, mode, polygon_vertices in operations:
        polygon = PolygonPath(polygon_vertices)

        polygon_mask = polygon.contains_points(
            points
        ).reshape(spatial_shape)

        if mode == "add":
            raw_masks[class_id] |= polygon_mask
        else:
            raw_masks[class_id] &= ~polygon_mask

    empty_classes = [
        class_names[class_id]
        for class_id, mask in raw_masks.items()
        if not mask.any()
    ]

    if empty_classes:
        raise RuntimeError(
            f"Empty ROI masks: {empty_classes}"
        )

    class_ids = list(class_names)

    overlap = np.zeros(spatial_shape, dtype=bool)

    if len(class_ids) == 2:
        overlap = (
            raw_masks[class_ids[0]]
            & raw_masks[class_ids[1]]
        )

    # Exclude ambiguous pixels from both usable masks.
    masks = {
        class_id: raw_masks[class_id] & ~overlap
        for class_id in class_ids
    }

    class_map = np.zeros(spatial_shape, dtype=np.uint8)

    for class_id, mask in masks.items():
        class_map[mask] = class_id

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        OUTPUT_DIR / f"{image_id}_roi_annotations.npz"
    )

    save_data = {
        "image_id": np.array(image_id),
        "class_map": class_map,
        "overlap_mask": overlap,
        "band_indices_zero_based": np.array(BANDS)
    }

    for class_id, mask in masks.items():
        name = class_names[class_id]
        save_data[f"{name}_mask"] = mask

    np.savez_compressed(output_path, **save_data)

    # Generate diagnostic overlay.
    overlay = rgb.copy()

    color_values = {
        1: np.array([0.0, 1.0, 0.0]),
        2: np.array([0.0, 0.8, 1.0])
    }

    for class_id, mask in masks.items():
        overlay[mask] = (
            0.45 * rgb[mask]
            + 0.55 * color_values[class_id]
        )

    overlay[overlap] = [1.0, 0.0, 0.0]

    figure_path = (
        FIGURE_DIR / f"{image_id}_roi_annotation.png"
    )

    plt.figure(figsize=(10, 9))
    plt.imshow(overlay)
    plt.title(f"Image {image_id} - Manual ROI Annotation")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight"
    )
    plt.close()

    summary = {
        "image_id": image_id,
        "annotation_method": "manual_polygon",
        "spatial_shape": list(spatial_shape),
        "visualization_band_indices_zero_based": BANDS,
        "roi_pixel_counts": {
            class_names[class_id]: int(mask.sum())
            for class_id, mask in masks.items()
        },
        "raw_roi_pixel_counts_before_overlap_removal": {
            class_names[class_id]: int(mask.sum())
            for class_id, mask in raw_masks.items()
        },
        "overlap_pixels": int(overlap.sum()),
        "ambiguous_overlap_excluded_from_both_classes": True,
        "polygon_count": len(operations),
        "class_map_values": {
            "0": "background_or_unassigned",
            **{
                str(class_id): name
                for class_id, name in class_names.items()
            }
        }
    }

    summary_path = (
        OUTPUT_DIR / f"{image_id}_roi_annotation_summary.json"
    )

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\nANNOTATION COMPLETED")
    print("--------------------")

    for name, count in summary["roi_pixel_counts"].items():
        print(f"{name}: {count:,} usable pixels")

    print(f"Overlapping pixels excluded: {overlap.sum():,}")
    print(f"Saved masks: {output_path}")
    print(f"Saved diagnostic: {figure_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python src/data/annotate_roi_polygons.py "
            "<2973 or 3079>"
        )
        sys.exit(1)

    image_id = sys.argv[1]

    if image_id not in CLASS_CONFIG:
        raise ValueError("Supported image IDs: 2973, 3079")

    annotate(image_id)
