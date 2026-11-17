"""
Interactive lesion-level annotation tool for hyperspectral image 3079.

This script enables polygon-based annotation to segment the lesion-bearing
stem of image 3079 into:
1. Visible necrotic lesion (ROI 1).
2. Visually unaffected adjacent stem tissue on the same stem (ROI 2).
3. Preserves the comparison stem (ROI 3) from 3079_roi_annotations.npz.

Both new regions are restricted strictly to the pre-existing lesion-bearing
stem mask. All operations enforce non-overlapping boundaries, non-empty masks,
and strict preservation of original stem boundaries.
"""

from pathlib import Path
import argparse
import json
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.path import Path as PolygonPath


ROOT = Path(__file__).resolve().parents[2]

PREVIEW_PATH = ROOT / "outputs/figures/3079_pseudo_rgb_preview.png"
SOURCE_MASK_PATH = ROOT / "data/processed/segmentation/3079_roi_annotations.npz"

OUTPUT_DIR = ROOT / "data/processed/segmentation"
FIGURE_DIR = ROOT / "outputs/figures"

OUTPUT_MASK = OUTPUT_DIR / "3079_lesion_level_annotations.npz"
OUTPUT_SUMMARY = OUTPUT_DIR / "3079_lesion_level_summary.json"
OUTPUT_FIGURE = FIGURE_DIR / "3079_lesion_level_annotation.png"


def polygon_to_mask(points, shape):
    """Convert polygon vertices into a boolean binary mask of given shape."""
    if len(points) < 3:
        return np.zeros(shape, dtype=bool)

    height, width = shape
    y, x = np.mgrid[0:height, 0:width]
    coordinates = np.column_stack((x.ravel(), y.ravel()))

    polygon = PolygonPath(points)
    mask = polygon.contains_points(coordinates)
    return mask.reshape(height, width)


def validate_saved_annotations(
    output_mask_path=OUTPUT_MASK,
    output_summary_path=OUTPUT_SUMMARY,
    output_figure_path=OUTPUT_FIGURE,
    source_mask_path=SOURCE_MASK_PATH,
    verbose=True
):
    """
    Validate saved lesion-level annotations without opening an interactive GUI.

    Returns:
        tuple (bool, dict): (True if all checks pass else False, results_dict)
    """
    results = {
        "files_exist": False,
        "keys_valid": False,
        "spatial_shape_valid": False,
        "source_preservation_valid": False,
        "lesion_mask_valid": False,
        "unaffected_mask_valid": False,
        "zero_overlap_valid": False,
        "vertices_valid": False,
        "summary_matches_data": False,
        "overall_pass": False,
        "errors": []
    }

    if verbose:
        print("=" * 70)
        print("TERRASPECTRA: 3079 LESION-LEVEL ANNOTATION VALIDATION")
        print("=" * 70)

    # Check file existence
    if not output_mask_path.exists():
        results["errors"].append(f"Missing NPZ mask file: {output_mask_path}")
    if not output_summary_path.exists():
        results["errors"].append(f"Missing summary JSON file: {output_summary_path}")
    if not output_figure_path.exists():
        results["errors"].append(f"Missing figure overlay: {output_figure_path}")
    if not source_mask_path.exists():
        results["errors"].append(f"Missing source mask file: {source_mask_path}")

    if results["errors"]:
        if verbose:
            for err in results["errors"]:
                print(f"FAIL: {err}")
        return False, results

    results["files_exist"] = True

    # Load arrays
    with np.load(source_mask_path) as src_data:
        expected_stem = src_data["lesion_bearing_stem_mask"].astype(bool)
        expected_comp = src_data["comparison_stem_mask"].astype(bool)
        expected_bands = src_data["band_indices_zero_based"]

    with np.load(output_mask_path) as out_data:
        keys = set(out_data.keys())
        expected_keys = {
            "image_id",
            "visible_lesion_mask",
            "adjacent_non_lesioned_stem_mask",
            "lesion_bearing_stem_mask",
            "comparison_stem_mask",
            "band_indices_zero_based",
            "lesion_polygon_vertices",
            "adjacent_unaffected_polygon_vertices"
        }
        missing_keys = expected_keys - keys
        if missing_keys:
            results["errors"].append(f"Missing required keys in NPZ: {missing_keys}")
            return False, results
        results["keys_valid"] = True

        image_id = str(out_data["image_id"])
        lesion_mask = out_data["visible_lesion_mask"].astype(bool)
        unaffected_mask = out_data["adjacent_non_lesioned_stem_mask"].astype(bool)
        saved_stem = out_data["lesion_bearing_stem_mask"].astype(bool)
        saved_comp = out_data["comparison_stem_mask"].astype(bool)
        saved_bands = out_data["band_indices_zero_based"]
        lesion_verts = out_data["lesion_polygon_vertices"]
        unaffected_verts = out_data["adjacent_unaffected_polygon_vertices"]

    # Load summary JSON
    with open(output_summary_path, "r", encoding="utf-8") as file:
        summary = json.load(file)

    # 1. Spatial shape and dtypes
    if lesion_mask.shape != (512, 512) or unaffected_mask.shape != (512, 512):
        results["errors"].append(
            f"Invalid mask dimensions: lesion={lesion_mask.shape}, "
            f"unaffected={unaffected_mask.shape}"
        )
    else:
        results["spatial_shape_valid"] = True

    # 2. Source mask preservation
    stem_matches = np.array_equal(saved_stem, expected_stem)
    comp_matches = np.array_equal(saved_comp, expected_comp)
    bands_match = np.array_equal(saved_bands, expected_bands)

    if not stem_matches or not comp_matches or not bands_match:
        results["errors"].append(
            f"Source stem preservation mismatch: stem={stem_matches}, "
            f"comp={comp_matches}, bands={bands_match}"
        )
    else:
        results["source_preservation_valid"] = True

    # 3. Lesion mask validity (non-empty & strictly inside stem mask)
    lesion_pixels = int(lesion_mask.sum())
    lesion_outside = int((lesion_mask & ~expected_stem).sum())
    if lesion_pixels <= 0:
        results["errors"].append("Visible lesion mask is empty.")
    elif lesion_outside > 0:
        results["errors"].append(
            f"Lesion mask extends outside stem mask by {lesion_outside} pixels."
        )
    else:
        results["lesion_mask_valid"] = True

    # 4. Unaffected mask validity (non-empty & strictly inside stem mask)
    unaffected_pixels = int(unaffected_mask.sum())
    unaffected_outside = int((unaffected_mask & ~expected_stem).sum())
    if unaffected_pixels <= 0:
        results["errors"].append(
            "Visually unaffected adjacent stem tissue mask is empty."
        )
    elif unaffected_outside > 0:
        results["errors"].append(
            f"Unaffected mask extends outside stem mask by {unaffected_outside} pixels."
        )
    else:
        results["unaffected_mask_valid"] = True

    # 5. Zero overlap check
    overlap_pixels = int((lesion_mask & unaffected_mask).sum())
    if overlap_pixels != 0:
        results["errors"].append(
            f"Non-zero overlap between lesion and unaffected masks: {overlap_pixels} pixels."
        )
    else:
        results["zero_overlap_valid"] = True

    # 6. Vertices validity
    if len(lesion_verts) < 3 or len(unaffected_verts) < 3:
        results["errors"].append(
            f"Insufficient polygon vertices: lesion={len(lesion_verts)}, "
            f"unaffected={len(unaffected_verts)}"
        )
    else:
        results["vertices_valid"] = True

    # 7. Summary JSON consistency
    json_lesion = summary.get("roi_pixel_counts", {}).get("visible_lesion")
    json_unaffected = summary.get("roi_pixel_counts", {}).get(
        "visually_unaffected_adjacent_stem"
    )
    json_overlap = summary.get("overlap_pixels")

    if (
        json_lesion != lesion_pixels
        or json_unaffected != unaffected_pixels
        or json_overlap != overlap_pixels
    ):
        results["errors"].append(
            f"Summary JSON counts mismatch: JSON=({json_lesion}, {json_unaffected}, {json_overlap}) "
            f"vs Arrays=({lesion_pixels}, {unaffected_pixels}, {overlap_pixels})"
        )
    else:
        results["summary_matches_data"] = True

    # Overall outcome
    results["overall_pass"] = (
        results["files_exist"]
        and results["keys_valid"]
        and results["spatial_shape_valid"]
        and results["source_preservation_valid"]
        and results["lesion_mask_valid"]
        and results["unaffected_mask_valid"]
        and results["zero_overlap_valid"]
        and results["vertices_valid"]
        and results["summary_matches_data"]
    )

    if verbose:
        print(f"Image ID:                                      {image_id}")
        print(f"Mask Dimensions:                               {lesion_mask.shape}")
        print(f"Lesion-Bearing Stem Total (Preserved):         {int(saved_stem.sum()):,} px")
        print(f"Comparison Stem Total (Preserved):             {int(saved_comp.sum()):,} px")
        print(f"ROI 1: Visible Necrotic Lesion:                {lesion_pixels:,} px")
        print(f"ROI 2: Visually Unaffected Adjacent Stem:      {unaffected_pixels:,} px")
        print(f"Unannotated Stem Margin:                       {int(saved_stem.sum()) - lesion_pixels - unaffected_pixels:,} px")
        print(f"Overlap (Lesion vs Unaffected):                {overlap_pixels} px (PASS: 0 px)")
        print(f"Lesion Polygon Vertices Count:                 {len(lesion_verts)}")
        print(f"Unaffected Polygon Vertices Count:             {len(unaffected_verts)}")
        print(f"Summary JSON File:                             {output_summary_path.name}")
        print(f"Figure Overlay File:                           {output_figure_path.name}")
        print("-" * 70)
        if results["overall_pass"]:
            print("STATUS: ALL 10 INTEGRITY CHECKS PASSED.")
        else:
            print("STATUS: VALIDATION FAILED. Errors detected:")
            for err in results["errors"]:
                print(f"  - {err}")
        print("=" * 70)

    return results["overall_pass"], results


class LesionLevelAnnotator:
    """Event-driven interactive Matplotlib annotator for image 3079."""

    STAGE_LESION = 1
    STAGE_UNAFFECTED = 2
    STAGE_REVIEW = 3

    def __init__(self, preview_path, source_mask_path, overwrite=False):
        self.preview_path = preview_path
        self.source_mask_path = source_mask_path
        self.overwrite = overwrite

        # Load image and source annotations (read-only)
        self.image = plt.imread(self.preview_path)

        with np.load(self.source_mask_path) as data:
            self.stem_mask = data["lesion_bearing_stem_mask"].astype(bool).copy()
            self.comparison_mask = data["comparison_stem_mask"].astype(bool).copy()
            self.band_indices = data["band_indices_zero_based"].copy()

        if self.image.shape[:2] != self.stem_mask.shape:
            raise ValueError("Preview image and source mask spatial dimensions mismatch.")

        self.shape = self.stem_mask.shape

        # Annotation state
        self.stage = self.STAGE_LESION
        self.lesion_vertices = []
        self.unaffected_vertices = []

        self.lesion_mask = None
        self.unaffected_mask = None
        self.overlap_mask = None

        self.lesion_outside_count = 0
        self.unaffected_outside_count = 0

        self.status_message = "Click boundary points for ROI 1 (Visible Necrotic Lesion)."
        self.saved = False

        # GUI elements
        self.fig = None
        self.ax = None
        self.progress_line = None
        self.start_marker = None
        self.lesion_overlay = None
        self.unaffected_overlay = None
        self.lesion_patch = None
        self.unaffected_patch = None

    def is_toolbar_active(self):
        """Check if Matplotlib zoom or pan tool is currently engaged."""
        if self.fig is None:
            return False
        toolbar = getattr(self.fig.canvas, "toolbar", None) or getattr(
            self.fig.canvas.manager, "toolbar", None
        )
        if toolbar is None:
            return False
        mode = getattr(toolbar, "mode", "")
        return mode != ""

    def update_title(self):
        """Update figure title and status banner based on current stage."""
        if self.stage == self.STAGE_LESION:
            n = len(self.lesion_vertices)
            title = (
                f"[STAGE 1/2] ROI 1: Visible Necrotic Lesion (RED)\n"
                f"Vertices: {n} | Click: add | Backspace: undo point | "
                f"Esc: clear | Enter: complete ROI 1 | Q: quit"
            )
        elif self.stage == self.STAGE_UNAFFECTED:
            n = len(self.unaffected_vertices)
            title = (
                f"[STAGE 2/2] ROI 2: Visually Unaffected Adjacent Stem (BLUE)\n"
                f"Vertices: {n} | Click: add | Backspace: undo point | "
                f"Esc: clear | U: undo to ROI 1 | Enter: complete ROI 2 | Q: quit"
            )
        else:
            lesion_count = int(self.lesion_mask.sum())
            unaffected_count = int(self.unaffected_mask.sum())
            title = (
                f"[REVIEW & CONFIRMATION]\n"
                f"Lesion: {lesion_count:,} px | Unaffected: {unaffected_count:,} px | Overlap: 0 px\n"
                f"Press 'S' to save annotations | Press 'U' to undo ROI 2 | Press 'Q' to quit"
            )

        self.ax.set_title(title, fontsize=10, pad=8)
        self.fig.canvas.draw_idle()

    def redraw_overlays(self):
        """Redraw completed mask overlays, active progress lines, and vertices."""
        # 1. Update in-progress line & start marker
        if self.stage == self.STAGE_LESION:
            pts = np.asarray(self.lesion_vertices, dtype=float)
            line_color = "red"
        elif self.stage == self.STAGE_UNAFFECTED:
            pts = np.asarray(self.unaffected_vertices, dtype=float)
            line_color = "deepskyblue"
        else:
            pts = np.empty((0, 2), dtype=float)
            line_color = "gray"

        if len(pts) > 0:
            self.progress_line.set_data(pts[:, 0], pts[:, 1])
            self.progress_line.set_color(line_color)
            self.start_marker.set_data([pts[0, 0]], [pts[0, 1]])
            self.start_marker.set_color("yellow")
        else:
            self.progress_line.set_data([], [])
            self.start_marker.set_data([], [])

        # 2. Update lesion overlay and patch
        if self.lesion_overlay is not None:
            self.lesion_overlay.remove()
            self.lesion_overlay = None
        if self.lesion_patch is not None:
            self.lesion_patch.remove()
            self.lesion_patch = None

        if self.lesion_mask is not None:
            self.lesion_overlay = self.ax.imshow(
                np.ma.masked_where(~self.lesion_mask, self.lesion_mask),
                cmap="Reds",
                alpha=0.50,
                vmin=0,
                vmax=1
            )
            if len(self.lesion_vertices) >= 3:
                self.lesion_patch = MplPolygon(
                    self.lesion_vertices,
                    closed=True,
                    fill=False,
                    edgecolor="red",
                    linewidth=1.5,
                    linestyle="--"
                )
                self.ax.add_patch(self.lesion_patch)

        # 3. Update unaffected overlay and patch
        if self.unaffected_overlay is not None:
            self.unaffected_overlay.remove()
            self.unaffected_overlay = None
        if self.unaffected_patch is not None:
            self.unaffected_patch.remove()
            self.unaffected_patch = None

        if self.unaffected_mask is not None:
            self.unaffected_overlay = self.ax.imshow(
                np.ma.masked_where(~self.unaffected_mask, self.unaffected_mask),
                cmap="Blues",
                alpha=0.50,
                vmin=0,
                vmax=1
            )
            if len(self.unaffected_vertices) >= 3:
                self.unaffected_patch = MplPolygon(
                    self.unaffected_vertices,
                    closed=True,
                    fill=False,
                    edgecolor="deepskyblue",
                    linewidth=1.5,
                    linestyle="--"
                )
                self.ax.add_patch(self.unaffected_patch)

        self.update_title()

    def on_click(self, event):
        """Handle mouse click events to add polygon vertices."""
        if event.inaxes != self.ax or event.button != 1:
            return
        if self.is_toolbar_active():
            return
        if event.xdata is None or event.ydata is None:
            return

        x, y = float(event.xdata), float(event.ydata)

        if self.stage == self.STAGE_LESION:
            self.lesion_vertices.append([x, y])
            self.redraw_overlays()
        elif self.stage == self.STAGE_UNAFFECTED:
            self.unaffected_vertices.append([x, y])
            self.redraw_overlays()

    def finish_current_polygon(self):
        """Finish and validate the current polygon stage."""
        if self.stage == self.STAGE_LESION:
            if len(self.lesion_vertices) < 3:
                print(
                    f"\n[WARNING] ROI 1 requires at least 3 vertices (received {len(self.lesion_vertices)}). "
                    "Keep clicking boundary points or press ESC to reset."
                )
                return

            raw_mask = polygon_to_mask(self.lesion_vertices, self.shape)
            restricted = raw_mask & self.stem_mask

            if not restricted.any():
                print(
                    "\n[ERROR] Lesion polygon has NO pixels inside the lesion-bearing stem mask. "
                    "Please press ESC and redraw over the center-right stem."
                )
                return

            self.lesion_mask = restricted
            self.lesion_outside_count = int((raw_mask & ~self.stem_mask).sum())
            self.stage = self.STAGE_UNAFFECTED

            print("\n" + "-" * 55)
            print(f"ROI 1 (Visible Necrotic Lesion) completed:")
            print(f"  - Pixels inside stem: {int(self.lesion_mask.sum()):,} px")
            print(f"  - Pixels excluded outside stem: {self.lesion_outside_count:,} px")
            print(f"Now draw ROI 2: Visually unaffected adjacent stem tissue on the SAME stem.")
            print("-" * 55)

            self.redraw_overlays()

        elif self.stage == self.STAGE_UNAFFECTED:
            if len(self.unaffected_vertices) < 3:
                print(
                    f"\n[WARNING] ROI 2 requires at least 3 vertices (received {len(self.unaffected_vertices)}). "
                    "Keep clicking boundary points or press ESC to reset."
                )
                return

            raw_mask = polygon_to_mask(self.unaffected_vertices, self.shape)
            restricted = raw_mask & self.stem_mask

            if not restricted.any():
                print(
                    "\n[ERROR] Unaffected tissue polygon has NO pixels inside the lesion-bearing stem mask. "
                    "Please press ESC and redraw."
                )
                return

            overlap = restricted & self.lesion_mask
            if overlap.any():
                overlap_count = int(overlap.sum())
                print(
                    f"\n[ERROR] Overlap detected: {overlap_count} pixels overlap with ROI 1. "
                    "The two regions must be strictly non-overlapping. "
                    "Press BACKSPACE to adjust vertices, or ESC to redraw ROI 2."
                )
                return

            self.unaffected_mask = restricted
            self.unaffected_outside_count = int((raw_mask & ~self.stem_mask).sum())
            self.overlap_mask = overlap
            self.stage = self.STAGE_REVIEW

            lesion_px = int(self.lesion_mask.sum())
            unaff_px = int(self.unaffected_mask.sum())
            stem_px = int(self.stem_mask.sum())
            comp_px = int(self.comparison_mask.sum())
            unannotated_px = stem_px - lesion_px - unaff_px

            print("\n" + "=" * 65)
            print("BOTH REGIONS VALIDATED SUCCESSFULLY (ZERO OVERLAP)")
            print("=" * 65)
            print(f"ROI 1: Visible necrotic lesion:             {lesion_px:,} px")
            print(f"       (Excluded outside stem mask:         {self.lesion_outside_count:,} px)")
            print(f"ROI 2: Visually unaffected adjacent tissue: {unaff_px:,} px")
            print(f"       (Excluded outside stem mask:         {self.unaffected_outside_count:,} px)")
            print(f"Overlap between ROI 1 and ROI 2:            0 px (PASS)")
            print(f"Unannotated lesion-bearing stem margin:     {unannotated_px:,} px")
            print(f"Preserved comparison stem (cyan):           {comp_px:,} px")
            print("-" * 65)
            print("Action controls:")
            print("  - Press 'S' to SAVE annotations and generate figure/summary.")
            print("  - Press 'U' to UNDO ROI 2 and redraw.")
            print("  - Press 'Q' to QUIT without saving.")
            print("=" * 65)

            self.redraw_overlays()

    def on_key(self, event):
        """Handle keyboard shortcuts."""
        key = (event.key or "").lower()

        if key in ("enter", "return"):
            self.finish_current_polygon()

        elif key == "backspace":
            if self.stage == self.STAGE_LESION and self.lesion_vertices:
                self.lesion_vertices.pop()
                self.redraw_overlays()
            elif self.stage == self.STAGE_UNAFFECTED and self.unaffected_vertices:
                self.unaffected_vertices.pop()
                self.redraw_overlays()

        elif key == "escape":
            if self.stage == self.STAGE_LESION:
                self.lesion_vertices.clear()
                print("\n[INFO] Cleared current vertices for ROI 1.")
                self.redraw_overlays()
            elif self.stage == self.STAGE_UNAFFECTED:
                self.unaffected_vertices.clear()
                print("\n[INFO] Cleared current vertices for ROI 2.")
                self.redraw_overlays()

        elif key == "u":
            if self.stage == self.STAGE_REVIEW:
                self.stage = self.STAGE_UNAFFECTED
                self.unaffected_mask = None
                self.unaffected_vertices.clear()
                print("\n[INFO] Returned to Stage 2: Redraw ROI 2 (Visually unaffected adjacent tissue).")
                self.redraw_overlays()
            elif self.stage == self.STAGE_UNAFFECTED:
                self.stage = self.STAGE_LESION
                self.lesion_mask = None
                self.lesion_vertices.clear()
                self.unaffected_vertices.clear()
                print("\n[INFO] Returned to Stage 1: Redraw ROI 1 (Visible necrotic lesion).")
                self.redraw_overlays()

        elif key == "s":
            if self.stage == self.STAGE_REVIEW:
                self.save_and_exit()
            else:
                print(
                    "\n[INFO] Cannot save yet: Both ROI 1 and ROI 2 must be completed "
                    "and validated first."
                )

        elif key == "q":
            print("\n[INFO] User chose to quit. Annotations were NOT saved.")
            self.saved = False
            plt.close(self.fig)

    def on_close(self, event):
        """Handle window close event safely."""
        if not self.saved:
            print("\n[INFO] Window closed without saving.")

    def save_and_exit(self):
        """Save validated arrays, JSON summary, and high-resolution figure."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        FIGURE_DIR.mkdir(parents=True, exist_ok=True)

        # Overwrite confirmation check
        if OUTPUT_MASK.exists() and not self.overwrite:
            print(f"\n[PROMPT] Target file exists: {OUTPUT_MASK}")
            response = input("Overwrite existing annotations? (y/N): ").strip().lower()
            if response not in ("y", "yes"):
                print("[INFO] Save cancelled. Existing annotations preserved.")
                return

        # 1. Save NPZ arrays
        np.savez_compressed(
            OUTPUT_MASK,
            image_id=np.array("3079"),
            visible_lesion_mask=self.lesion_mask,
            adjacent_non_lesioned_stem_mask=self.unaffected_mask,
            lesion_bearing_stem_mask=self.stem_mask,
            comparison_stem_mask=self.comparison_mask,
            band_indices_zero_based=self.band_indices,
            lesion_polygon_vertices=np.asarray(self.lesion_vertices, dtype=np.float32),
            adjacent_unaffected_polygon_vertices=np.asarray(self.unaffected_vertices, dtype=np.float32)
        )

        # 2. Save JSON summary with explicit scientific terminology
        summary = {
            "image_id": "3079",
            "annotation_method": "manual_polygon_restricted_to_stem",
            "spatial_shape": list(self.shape),
            "spectral_axis": "zero_based_band_indices",
            "wavelength_calibration": "Unavailable for image 3079; band indices only.",
            "roi_pixel_counts": {
                "visible_lesion": int(self.lesion_mask.sum()),
                "visually_unaffected_adjacent_stem": int(self.unaffected_mask.sum()),
                "lesion_bearing_stem_total": int(self.stem_mask.sum()),
                "comparison_stem_total": int(self.comparison_mask.sum()),
                "unannotated_stem_margin": int(self.stem_mask.sum()) - int(self.lesion_mask.sum()) - int(self.unaffected_mask.sum())
            },
            "excluded_polygon_pixels_outside_stem": {
                "visible_lesion_polygon_excluded": self.lesion_outside_count,
                "visually_unaffected_polygon_excluded": self.unaffected_outside_count
            },
            "overlap_pixels": 0,
            "polygon_vertices_count": {
                "visible_lesion": len(self.lesion_vertices),
                "visually_unaffected_adjacent_stem": len(self.unaffected_vertices)
            },
            "scientific_interpretation_notes": [
                "ROI 1 corresponds to visually brown necrotic lesion tissue on the stem.",
                "ROI 2 corresponds to visually unaffected adjacent stem tissue on the SAME stem; it is NOT confirmed healthy.",
                "ROI 3 corresponds to the pre-existing comparison stem and lateral branch from 3079_roi_annotations.npz.",
                "Both ROI 1 and ROI 2 were strictly restricted to lesion_bearing_stem_mask and have zero overlap.",
                "All spectral analyses of image 3079 must use zero-based band indices without assuming wavelength calibration."
            ]
        }

        with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as file:
            json.dump(summary, file, indent=4)

        # 3. Save publication-quality figure
        save_fig, save_ax = plt.subplots(figsize=(10, 10))
        save_ax.imshow(self.image)

        # Contour lines
        save_ax.contour(
            self.stem_mask.astype(float),
            levels=[0.5],
            colors=["lime"],
            linewidths=1.5
        )
        save_ax.contour(
            self.comparison_mask.astype(float),
            levels=[0.5],
            colors=["cyan"],
            linewidths=1.0,
            linestyles=["dashed"]
        )

        # Mask fills
        save_ax.imshow(
            np.ma.masked_where(~self.lesion_mask, self.lesion_mask),
            cmap="Reds",
            alpha=0.55,
            vmin=0,
            vmax=1
        )
        save_ax.imshow(
            np.ma.masked_where(~self.unaffected_mask, self.unaffected_mask),
            cmap="Blues",
            alpha=0.55,
            vmin=0,
            vmax=1
        )

        # Legend handles
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color="lime", lw=2, label=f"Lesion stem boundary ({int(self.stem_mask.sum()):,} px)"),
            Line2D([0], [0], color="cyan", lw=1.5, ls="--", label=f"Comparison stem boundary ({int(self.comparison_mask.sum()):,} px)"),
            Patch(facecolor="red", edgecolor="red", alpha=0.55, label=f"ROI 1: Visible lesion ({int(self.lesion_mask.sum()):,} px)"),
            Patch(facecolor="#1E88E5", edgecolor="blue", alpha=0.55, label=f"ROI 2: Visually unaffected stem ({int(self.unaffected_mask.sum()):,} px)")
        ]
        save_ax.legend(handles=legend_elements, loc="upper right", framealpha=0.9, fontsize=9)
        save_ax.set_title("Image 3079: Lesion-Level Regions of Interest", fontsize=12, pad=10)
        save_ax.set_axis_off()

        save_fig.savefig(OUTPUT_FIGURE, dpi=200, bbox_inches="tight")
        plt.close(save_fig)

        self.saved = True
        print("\n" + "=" * 70)
        print("ANNOTATION SUCCESSFULLY SAVED")
        print("=" * 70)
        print(f"Mask NPZ:       {OUTPUT_MASK}")
        print(f"Summary JSON:   {OUTPUT_SUMMARY}")
        print(f"Overlay Figure: {OUTPUT_FIGURE}")
        print("=" * 70)

        plt.close(self.fig)

    def run(self):
        """Launch the interactive Matplotlib annotation interface."""
        print("=" * 70)
        print("TERRASPECTRA: INTERACTIVE LESION-LEVEL ANNOTATOR (IMAGE 3079)")
        print("=" * 70)
        print("Objective:")
        print("  Annotate 2 sub-regions within the center-right stem (green boundary):")
        print("  1. ROI 1: Visible brown necrotic lesion.")
        print("  2. ROI 2: Visually unaffected adjacent stem tissue on the same stem.")
        print("\nControls:")
        print("  - Left Mouse Click : Add polygon vertex")
        print("  - Backspace        : Undo / remove last clicked vertex")
        print("  - Escape           : Clear current polygon vertices")
        print("  - Enter            : Complete current polygon (requires >= 3 points)")
        print("  - U                : Undo previous completed ROI stage")
        print("  - S                : Save completed and validated annotations")
        print("  - Q                : Quit without saving")
        print("  - Toolbar Zoom/Pan : Standard Matplotlib tools are fully functional")
        print("=" * 70)

        # Pre-check existing file
        if OUTPUT_MASK.exists() and not self.overwrite:
            print(f"\n[NOTE] Annotation file already exists: {OUTPUT_MASK}")
            print("You can run with --validate to inspect it, or --overwrite to replace it.")
            response = input("Continue and re-annotate? (y/N): ").strip().lower()
            if response not in ("y", "yes"):
                print("Exiting without modifying existing files.")
                return

        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.imshow(self.image)

        # Draw reference boundaries
        self.ax.contour(
            self.stem_mask.astype(float),
            levels=[0.5],
            colors=["lime"],
            linewidths=1.4
        )
        self.ax.contour(
            self.comparison_mask.astype(float),
            levels=[0.5],
            colors=["cyan"],
            linewidths=0.9,
            linestyles=["dashed"]
        )

        self.ax.set_axis_off()

        # In-progress line & marker
        self.progress_line, = self.ax.plot([], [], "-o", linewidth=1.5, markersize=4)
        self.start_marker, = self.ax.plot([], [], "o", markersize=7)

        # Event listeners
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.fig.canvas.mpl_connect("close_event", self.on_close)

        self.redraw_overlays()
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive lesion-level annotation tool for image 3079."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run non-interactive validation checks on existing saved annotations."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing annotation files without prompting."
    )

    args = parser.parse_args()

    if args.validate:
        passed, _ = validate_saved_annotations()
        sys.exit(0 if passed else 1)

    annotator = LesionLevelAnnotator(
        preview_path=PREVIEW_PATH,
        source_mask_path=SOURCE_MASK_PATH,
        overwrite=args.overwrite
    )
    annotator.run()


if __name__ == "__main__":
    main()
