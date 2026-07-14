from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent
IMG = ROOT / "images"
OUT = ROOT / "exports" / "screen_normalize_final_6min_en.pptx"

W = 13.333
H = 7.5

BLUE = "1F57C4"
BLUE_DARK = "17479E"
BLUE_SOFT = "E8EFFB"
BLUE_PALE = "F4F6FA"
INK = "1A1A1A"
MUTED = "555B66"
LINE = "D3DAE6"
RED = "C43D2E"
RED_SOFT = "FCEDEA"
ORANGE = "E97822"
TEAL = "2E8579"
TEAL_SOFT = "E6F3F1"
WHITE = "FFFFFF"

FONT_CN = "Aptos"
FONT_LATIN = "Aptos"


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.replace("#", ""))


def set_run_font(run, size: float, color: str = INK, bold: bool = False,
                 italic: bool = False, font: str = FONT_CN) -> None:
    run.font.name = font
    run.font.size = Pt(size)
    run.font.color.rgb = rgb(color)
    run.font.bold = bold
    run.font.italic = italic

    r_pr = run._r.get_or_add_rPr()
    ea = r_pr.find(qn("a:ea"))
    if ea is None:
        ea = OxmlElement("a:ea")
        r_pr.append(ea)
    ea.set("typeface", FONT_CN)


def set_text_margins(shape, left=0.08, right=0.08, top=0.04, bottom=0.04):
    tf = shape.text_frame
    tf.margin_left = Inches(left)
    tf.margin_right = Inches(right)
    tf.margin_top = Inches(top)
    tf.margin_bottom = Inches(bottom)


def add_text(slide, text: str, x: float, y: float, w: float, h: float,
             size: float = 16, color: str = INK, bold: bool = False,
             italic: bool = False, align=PP_ALIGN.LEFT,
             valign=MSO_ANCHOR.TOP, font: str = FONT_CN,
             margin: float = 0.0, line_spacing: float = 1.08):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    set_text_margins(shape, margin, margin, margin, margin)
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = valign
    lines = text.split("\n")
    for idx, line in enumerate(lines):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(0)
        p.space_before = Pt(0)
        r = p.add_run()
        r.text = line
        set_run_font(r, size, color, bold, italic, font)
    return shape


def add_rich_line(slide, parts, x, y, w, h, size=16, align=PP_ALIGN.LEFT,
                  valign=MSO_ANCHOR.TOP, margin=0.0):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    set_text_margins(shape, margin, margin, margin, margin)
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_after = Pt(0)
    p.space_before = Pt(0)
    for part in parts:
        if isinstance(part, str):
            text = part
            kwargs = {}
        else:
            text = part[0]
            kwargs = part[1] if len(part) > 1 and isinstance(part[1], dict) else {}
        r = p.add_run()
        r.text = text
        set_run_font(
            r,
            kwargs.get("size", size),
            kwargs.get("color", INK),
            kwargs.get("bold", False),
            kwargs.get("italic", False),
            kwargs.get("font", FONT_CN),
        )
    return shape


def add_rect(slide, x, y, w, h, fill=WHITE, line=LINE, radius=True,
             line_width=0.8, transparency=0):
    kind = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.fill.transparency = transparency
    shape.line.color.rgb = rgb(line)
    shape.line.width = Pt(line_width)
    if radius:
        try:
            shape.adjustments[0] = 0.08
        except Exception:
            pass
    return shape


def add_line(slide, x1, y1, x2, y2, color=BLUE, width=2.0):
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2),
    )
    line.line.color.rgb = rgb(color)
    line.line.width = Pt(width)
    return line


def add_arrow(slide, x1, y1, x2, y2, color=LINE, width=2.0):
    line = add_line(slide, x1, y1, x2, y2, color, width)
    line.line.end_arrowhead = True
    return line


def add_circle(slide, cx, cy, d, fill=BLUE, line=BLUE):
    return add_rect(slide, cx - d / 2, cy - d / 2, d, d, fill, line, radius=True, line_width=0.8)


def image_size(path: Path):
    with Image.open(path) as im:
        return im.size


def add_picture_contain(slide, path: Path, x: float, y: float, w: float, h: float,
                        border: str | None = None, border_width: float = 0.8):
    px_w, px_h = image_size(path)
    scale = min(w / px_w, h / px_h)
    draw_w = px_w * scale
    draw_h = px_h * scale
    pic = slide.shapes.add_picture(
        str(path),
        Inches(x + (w - draw_w) / 2),
        Inches(y + (h - draw_h) / 2),
        width=Inches(draw_w),
        height=Inches(draw_h),
    )
    if border:
        pic.line.color.rgb = rgb(border)
        pic.line.width = Pt(border_width)
    return pic


def add_picture_crop(slide, path: Path, x: float, y: float, w: float, h: float,
                     crop_left=0.0, crop_top=0.0, crop_right=0.0, crop_bottom=0.0,
                     border: str | None = None):
    pic = slide.shapes.add_picture(
        str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h)
    )
    pic.crop_left = crop_left
    pic.crop_top = crop_top
    pic.crop_right = crop_right
    pic.crop_bottom = crop_bottom
    if border:
        pic.line.color.rgb = rgb(border)
        pic.line.width = Pt(0.8)
    return pic


def add_footer(slide, page: int, source: str = ""):
    add_line(slide, 0.62, 7.02, 12.70, 7.02, color=LINE, width=0.5)
    add_text(slide, "ECE4512 Final Project · 2026", 0.62, 7.08, 1.75, 0.19,
             size=7.2, color=MUTED)
    if source:
        add_text(slide, f"Source: {source}", 2.18, 7.05, 10.05, 0.27,
                 size=6.4, color=MUTED)
    add_text(slide, str(page), 12.45, 7.08, 0.25, 0.19, size=7.6, color=MUTED,
             align=PP_ALIGN.RIGHT)


def add_header(slide, kicker: str, title: str, page: int, source: str = "",
               title_size: float = 29):
    add_text(slide, kicker.upper(), 0.62, 0.32, 8.6, 0.28, size=11.5, color=BLUE, bold=True)
    add_text(slide, title, 0.62, 0.67, 12.0, 0.58, size=title_size, bold=True,
             valign=MSO_ANCHOR.MIDDLE)
    add_line(slide, 0.64, 1.26, 1.55, 1.26, color=BLUE, width=2.4)
    add_footer(slide, page, source)


def add_notes(slide, text: str):
    notes_tf = slide.notes_slide.notes_text_frame
    notes_tf.text = text


def style_cell(cell, text, fill, color=INK, bold=False, size=11.5,
               align=PP_ALIGN.CENTER):
    cell.fill.solid()
    cell.fill.fore_color.rgb = rgb(fill)
    cell.margin_left = Inches(0.06)
    cell.margin_right = Inches(0.06)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    tf = cell.text_frame
    tf.clear()
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    set_run_font(r, size, color, bold)


def build_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    blank = prs.slide_layouts[6]

    # Slide 1 — Cover
    slide = prs.slides.add_slide(blank)
    add_text(slide, "ECE4512 FINAL PROJECT · 2026", 0.70, 0.48, 6.7, 0.30,
             size=12.2, color=BLUE, bold=True)
    add_text(slide, "Border-Guided Geometric\nNormalization of Captured-Screen Video", 0.70, 0.92, 6.95, 1.35,
             size=25.5, bold=True, line_spacing=1.03)
    add_text(slide, "Physical screen boundaries as the primary homography cue", 0.72, 2.36, 6.5, 0.34,
             size=14.2, color=MUTED, italic=True, font=FONT_LATIN)
    add_rich_line(
        slide,
        [
            ("Rongshuo Wen", {"bold": True}), ("  124020369      ", {"color": MUTED}),
            ("Bihua Wen", {"bold": True}), ("  124090670", {"color": MUTED}),
        ],
        0.72, 2.85, 6.6, 0.30, size=11.8,
    )
    add_rich_line(
        slide,
        [("Mingrui Liu", {"bold": True}), ("  124090375", {"color": MUTED})],
        0.72, 3.18, 6.6, 0.30, size=11.8,
    )

    add_rect(slide, 0.70, 3.72, 6.85, 2.35, fill=BLUE_SOFT, line=BLUE_SOFT)
    add_rich_line(slide, [("Core problem. ", {"color": BLUE, "bold": True}),
                          ("Page scrolling, in-screen video, and camera motion are not the same motion.")],
                  0.96, 4.00, 6.25, 0.50, size=14.0)
    add_text(slide,
             "We let the physical screen border directly determine the homography. Internal LK/RANSAC tracks are used only for consistency diagnostics, so true content motion is preserved while the screen plane remains stable.",
             0.96, 4.55, 6.18, 1.10, size=13.7, color=INK, line_spacing=1.12)

    add_rect(slide, 8.04, 1.40, 4.67, 1.88, fill=WHITE, line=LINE)
    add_picture_contain(slide, IMG / "figure_01_pipeline.png", 8.12, 1.49, 4.51, 1.69)
    add_text(slide, "Repository method figure: border-guided normalization", 8.15, 3.08, 4.45, 0.20,
             size=8.2, color=MUTED, italic=True, align=PP_ALIGN.CENTER)

    add_rect(slide, 8.04, 3.58, 4.67, 2.48, fill=WHITE, line=LINE)
    add_picture_crop(slide, IMG / "annotated_dataset_mosaic.jpg", 8.12, 3.66, 4.51, 2.20,
                     crop_top=0.00, crop_bottom=0.48)
    add_text(slide, "Self-collected captures with manual corner annotations", 8.15, 5.84, 4.45, 0.20,
             size=8.2, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    add_footer(slide, 1, "figure_01_pipeline.png; annotated_dataset_mosaic.jpg")
    add_notes(slide,
              "[About 25 seconds] This project studies the geometric front end for captured-screen video. The input is a full handheld video containing background clutter, perspective distortion, camera shake, and dynamic content inside the display. The output is a stable, front-facing screen video. The key idea is to let the physical screen border determine the homography instead of allowing page scrolling or in-screen video to move the estimated screen plane.")

    # Slide 2 — Problem and insight
    slide = prs.slides.add_slide(blank)
    add_header(slide, "WHY BORDER EVIDENCE", "The Core Problem: Content Motion ≠ Screen Motion", 2,
               "project outline; figure_05_qualitative.png", title_size=27)
    cards = [
        (0.65, "Frame-wise detection", "Trusts the current frame", "Detection noise → jitter\nWeak borders → localization bias", RED, RED_SOFT),
        (4.45, "Adjacent optical flow", "Trusts internal texture", "Page scrolling → content-driven motion\nFrame propagation → accumulated drift", ORANGE, "FFF3E8"),
        (8.25, "Border-guided (ours)", "Trusts the physical boundary", "Border defines the quadrilateral\nInternal flow is diagnostic only", BLUE, BLUE_SOFT),
    ]
    for x, name, belief, weakness, accent, soft in cards:
        add_rect(slide, x, 1.56, 3.46, 2.23, fill=soft, line=accent, line_width=1.1)
        add_text(slide, name, x + 0.22, 1.78, 2.98, 0.36, size=17, color=accent, bold=True)
        add_text(slide, belief, x + 0.22, 2.23, 2.98, 0.30, size=12.5, color=MUTED, bold=True)
        add_line(slide, x + 0.22, 2.64, x + 3.18, 2.64, color=LINE, width=0.8)
        add_text(slide, weakness, x + 0.22, 2.80, 2.98, 0.72, size=13.2, color=INK,
                 line_spacing=1.14)

    add_text(slide, "Same moment on a scrolling page: input + three methods", 0.70, 4.08, 6.2, 0.28,
             size=11.4, color=BLUE, bold=True)
    add_rect(slide, 0.65, 4.40, 12.03, 2.18, fill=WHITE, line=LINE)
    add_picture_crop(slide, IMG / "figure_05_qualitative.png", 0.76, 4.51, 11.81, 1.92,
                     crop_top=0.205, crop_bottom=0.615)
    add_text(slide, "Check whether the full screen is preserved, the border drifts, and the scrolling content remains intact.",
             0.77, 6.56, 11.78, 0.26, size=10.0, color=MUTED, italic=True,
             align=PP_ALIGN.CENTER)
    add_notes(slide,
              "[About 45 seconds] The problem is not merely cropping the image into a rectangle; it is separating screen motion from content motion. Frame-wise detection trusts each current frame, so weak borders cause localization bias and jitter. Adjacent-frame optical flow trusts internal texture, so page scrolling can be mistaken for screen motion and accumulate drift. Our method prioritizes the physical screen boundary. The comparison below shows the same scrolling moment: we must check the complete screen extent, border stability, and whether true scrolling is retained.")

    # Slide 3 — Pipeline
    slide = prs.slides.add_slide(blank)
    add_header(slide, "METHOD", "The Current Border-Guided Pipeline", 3,
               "figure_01_pipeline.png")
    add_rect(slide, 0.62, 1.50, 12.08, 3.63, fill=WHITE, line=LINE)
    add_picture_contain(slide, IMG / "figure_01_pipeline.png", 0.74, 1.60, 11.84, 3.42)

    method_cards = [
        (0.66, "01", "Physical borders define H", "Sample profiles near predicted borders, fit four lines, and intersect them."),
        (4.55, "02", "LK/RANSAC is diagnostic", "Detect internal-motion conflict without letting scrolling content control the plane."),
        (8.44, "03", "Gating, redetection, smoothing", "Reject invalid quadrilaterals, redetect when needed, and smooth the final trajectory."),
    ]
    for x, idx, title, body in method_cards:
        add_rect(slide, x, 5.40, 3.60, 1.28, fill=BLUE_PALE, line=LINE)
        add_text(slide, idx, x + 0.18, 5.61, 0.50, 0.30, size=11.2, color=BLUE, bold=True)
        add_text(slide, title, x + 0.66, 5.56, 2.68, 0.34, size=13.1, color=INK, bold=True)
        add_text(slide, body, x + 0.18, 6.02, 3.12, 0.44, size=10.5, color=MUTED,
                 line_spacing=1.08)
    add_notes(slide,
              "[About 55 seconds] The pipeline begins with four-corner initialization on the first frame. The previous quadrilateral predicts local search bands for all four sides. We sample gradient profiles along inward normals, select strong candidates close to each predicted border, and robustly fit four lines. Their intersections form the current quadrilateral, which is checked for convexity, side geometry, and plausible frame-to-frame change. LK/RANSAC only diagnoses disagreement between internal texture and border motion. If the border is valid, the physical boundary still wins. Finally, the trajectory is interpolated, smoothed, and warped to a fixed canvas.")

    # Slide 4 — Dataset
    slide = prs.slides.add_slide(blank)
    add_header(slide, "EVALUATION", "Dataset & Experimental Setup", 4,
               "project outline; annotated_dataset_mosaic.jpg")

    stat_specs = [
        (0.68, "50", "self-collected clips"),
        (2.77, "14,985", "total frames"),
        (5.16, "10", "annotated evaluation clips"),
    ]
    for x, number, label in stat_specs:
        add_rect(slide, x, 1.55, 1.87 if x != 2.77 else 2.13, 1.20,
                 fill=BLUE_SOFT, line=BLUE_SOFT)
        add_text(slide, number, x + 0.14, 1.72, (1.59 if x != 2.77 else 1.85), 0.48,
                 size=24, color=BLUE, bold=True, align=PP_ALIGN.CENTER,
                 valign=MSO_ANCHOR.MIDDLE)
        add_text(slide, label, x + 0.10, 2.24, (1.67 if x != 2.77 else 1.93), 0.24,
                 size=10.2, color=MUTED, align=PP_ALIGN.CENTER)

    add_text(slide, "Five capture conditions", 0.69, 3.02, 2.8, 0.28, size=13.5, color=BLUE, bold=True)
    classes = ["Static page", "Scrolling", "In-screen video", "Weak border", "Challenging"]
    class_colors = [BLUE_SOFT, BLUE_SOFT, BLUE_SOFT, BLUE_SOFT, RED_SOFT]
    class_lines = [LINE, LINE, LINE, LINE, RED]
    for i, label in enumerate(classes):
        x = 0.68 + i * 1.36
        add_rect(slide, x, 3.43, 1.18, 1.22, fill=class_colors[i], line=class_lines[i],
                 line_width=1.0)
        add_text(slide, f"CLASS {i + 1}", x + 0.08, 3.61, 1.02, 0.20,
                 size=7.8, color=(RED if i == 4 else BLUE), bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide, label, x + 0.08, 3.95, 1.02, 0.42, size=9.7, bold=True,
                 align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    add_rect(slide, 0.68, 4.94, 6.58, 1.56, fill=BLUE_PALE, line=LINE)
    add_rich_line(slide, [("Fair comparison. ", {"color": BLUE, "bold": True}),
                          ("All three methods share the same input, initialization, canvas, annotations, and metric code.")],
                  0.92, 5.15, 6.05, 0.45, size=11.7)
    add_text(slide, "Geometry excludes initialization frame 0. We take medians within each clip, then aggregate across clips.",
             0.92, 5.72, 5.98, 0.44, size=10.6, color=MUTED)

    add_rect(slide, 7.63, 1.55, 5.05, 4.95, fill=INK, line=INK)
    add_picture_contain(slide, IMG / "annotated_dataset_mosaic.jpg", 7.73, 1.65, 4.85, 4.70)
    add_text(slide, "Repository dataset mosaic; green quadrilaterals mark manual screen boundaries.",
             7.83, 6.28, 4.65, 0.24, size=8.5, color=LINE, italic=True,
             align=PP_ALIGN.CENTER)
    add_notes(slide,
              "[About 40 seconds] The complete dataset contains fifty self-collected captured-screen videos and 14,985 frames, with ten clips in each of five capture conditions. The current formal quantitative evaluation uses ten annotated clips, two per condition. All methods share the same input, first-frame initialization, output canvas, corner annotations, and metric implementation. Geometry excludes frame zero; metrics are summarized by the median within each clip and then by the median across clips.")

    # Slide 5 — Overall results
    slide = prs.slides.add_slide(blank)
    add_header(slide, "MAIN RESULTS", "Overall Results: More Accurate and More Stable", 5,
               "figure_02_overall_results.png", title_size=27)
    add_rect(slide, 0.64, 1.53, 8.42, 4.98, fill=WHITE, line=LINE)
    add_picture_contain(slide, IMG / "figure_02_overall_results.png", 0.75, 1.65, 8.20, 4.72)

    add_rect(slide, 9.32, 1.53, 3.37, 4.98, fill=BLUE_SOFT, line=BLUE_SOFT)
    metrics = [
        ("3.87 px", "Corner RMSE", "LOWEST", BLUE),
        ("0.996", "Quadrilateral IoU", "HIGHEST", TEAL),
        ("2.45", "px/frame translation variation", "LOWEST", BLUE),
    ]
    y = 1.86
    for value, label, tag, c in metrics:
        add_text(slide, value, 9.65, y, 2.72, 0.48, size=23.0, color=c, bold=True)
        add_text(slide, label, 9.65, y + 0.49, 2.20, 0.25, size=10.8, color=INK, bold=True)
        add_rect(slide, 11.68, y + 0.46, 0.78, 0.25, fill=WHITE, line=LINE)
        add_text(slide, tag, 11.70, y + 0.50, 0.74, 0.16, size=6.6, color=c, bold=True,
                 align=PP_ALIGN.CENTER)
        y += 1.08
    add_line(slide, 9.65, 5.06, 12.38, 5.06, color=LINE, width=0.8)
    add_text(slide, "TAKEAWAY", 9.65, 5.30, 1.10, 0.24, size=9.4, color=BLUE, bold=True)
    add_text(slide, "The result is not merely smoother—the estimated quadrilateral is also much closer to the annotation.",
             9.65, 5.63, 2.72, 0.66, size=10.8, color=INK, line_spacing=1.08)
    add_notes(slide,
              "[About 55 seconds] These three metrics come directly from the repository's overall-results figure. The border-guided method reaches a corner RMSE of 3.87 pixels, compared with 30.37 for frame-wise detection and 31.40 for optical flow. IoU rises to 0.996, while translation variation falls to 2.45 pixels per frame. Crucially, this is not superficial stability created by freezing the trajectory. Geometry and temporal stability improve together, supporting the physical screen border as a better primary homography cue than internal content motion.")

    # Slide 6 — Category results
    slide = prs.slides.add_slide(blank)
    add_header(slide, "WHERE IT HELPS", "Largest Gains on Scrolling and Weak-Border Scenes", 6,
               "figure_03_category_results.png", title_size=26.5)
    add_rect(slide, 0.64, 1.53, 8.83, 4.98, fill=WHITE, line=LINE)
    add_picture_contain(slide, IMG / "figure_03_category_results.png", 0.76, 1.65, 8.59, 4.72)

    add_rect(slide, 9.72, 1.53, 2.97, 1.58, fill=BLUE_SOFT, line=BLUE)
    add_text(slide, "SCROLLING PAGE", 9.98, 1.78, 2.40, 0.28, size=12.8, color=BLUE, bold=True)
    add_text(slide, "RMSE  2.87 px", 9.98, 2.18, 2.40, 0.31, size=16.4, color=INK, bold=True)
    add_text(slide, "Frame-wise 31.76 · Flow 81.67", 9.98, 2.60, 2.40, 0.22,
             size=8.8, color=MUTED)

    add_rect(slide, 9.72, 3.30, 2.97, 1.58, fill=TEAL_SOFT, line=TEAL)
    add_text(slide, "WEAK BORDER", 9.98, 3.55, 2.40, 0.28, size=12.8, color=TEAL, bold=True)
    add_text(slide, "RMSE  9.35 px", 9.98, 3.95, 2.40, 0.31, size=16.4, color=INK, bold=True)
    add_text(slide, "Both comparison methods >155 px", 9.98, 4.37, 2.40, 0.22,
             size=8.8, color=MUTED)

    add_rect(slide, 9.72, 5.07, 2.97, 1.44, fill=BLUE_PALE, line=LINE)
    add_text(slide, "CHALLENGING SCENES REMAIN A LIMIT", 9.98, 5.27, 2.40, 0.38, size=9.8, color=RED, bold=True)
    add_text(slide, "Geometry is slightly worse than frame-wise detection, but translation variation is 3.74 versus 5.19 / 8.56.",
             9.98, 5.74, 2.40, 0.58, size=9.1, color=MUTED, line_spacing=1.06)
    add_notes(slide,
              "[About 50 seconds] The category results show where the improvement comes from. On scrolling pages, optical flow follows the moving content and RMSE rises to 81.67 pixels. The border-guided method stays on the physical screen and reaches 2.87 pixels. In weak-border scenes, the local search band predicted from the previous frame is far more stable than independent full-frame detection: our RMSE is 9.35, while both comparison methods exceed 155. Challenging scenes remain the main limitation. Frame-wise detection has slightly lower geometry error there, but our trajectory is still more stable, so future work should focus on glare, occlusion, and very low contrast.")

    # Slide 7 — Ablation
    slide = prs.slides.add_slide(blank)
    add_header(slide, "ABLATION", "Filtering Adds Stability; Other Modules Form a Safety Net", 7,
               "proposal_border_ablation_2026-07-14.md", title_size=24.5)
    rows = 6
    cols = 4
    table_shape = slide.shapes.add_table(rows, cols, Inches(0.66), Inches(1.62), Inches(8.25), Inches(4.62))
    table = table_shape.table
    widths = [3.10, 1.54, 1.54, 2.07]
    for idx, width in enumerate(widths):
        table.columns[idx].width = Inches(width)
    for row_idx in range(rows):
        table.rows[row_idx].height = Inches(0.77)

    headers = ["Variant", "RMSE ↓", "IoU ↑", "Translation ↓"]
    for j, h_text in enumerate(headers):
        style_cell(table.cell(0, j), h_text, BLUE_DARK, color=WHITE, bold=True, size=11.3)

    data = [
        ("Full method: Profile border", "3.253", "0.996038", "0.752"),
        ("No trajectory smoothing", "2.932", "0.996585", "1.430"),
        ("No LK consistency diagnostic", "3.253", "0.996038", "0.752"),
        ("No redetection fallback", "3.253", "0.996038", "0.752"),
        ("Loose edge gates", "3.253", "0.996038", "0.752"),
    ]
    for i, row in enumerate(data, start=1):
        fill = BLUE_SOFT if i == 1 else (RED_SOFT if i == 2 else "F6F8FB")
        for j, value in enumerate(row):
            style_cell(table.cell(i, j), value, fill,
                       color=(BLUE if i == 1 and j > 0 else INK),
                       bold=(i in (1, 2)), size=(11.2 if j == 0 else 11.0),
                       align=(PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER))

    add_rect(slide, 9.20, 1.62, 3.48, 2.05, fill=BLUE_SOFT, line=BLUE)
    add_text(slide, "0.752  →  1.430", 9.48, 1.96, 2.91, 0.44,
             size=22.0, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Translation variation nearly doubles without smoothing", 9.49, 2.50, 2.89, 0.56,
             size=10.4, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Trade-off: sparse-frame RMSE improves slightly, but frame-to-frame jitter increases.",
             9.48, 3.07, 2.91, 0.42, size=8.4, color=MUTED, align=PP_ALIGN.CENTER)

    add_rect(slide, 9.20, 3.93, 3.48, 2.31, fill=BLUE_PALE, line=LINE)
    add_text(slide, "LK / REDETECTION / GATING", 9.48, 4.24, 2.91, 0.34,
             size=15.0, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "No metric change on this scrolling clip", 9.48, 4.73, 2.91, 0.34,
             size=10.0, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Profile border evidence succeeds on every frame here. These modules mainly handle abnormal detection and recovery rather than normal-frame estimation.",
             9.50, 5.18, 2.87, 0.75, size=9.3, color=MUTED,
             align=PP_ALIGN.CENTER, line_spacing=1.10)
    add_text(slide, "All values are transcribed directly from the repository's Proposal Border Ablation document.",
             0.69, 6.47, 8.15, 0.24, size=8.6, color=MUTED, italic=True)
    add_notes(slide,
              "[About 55 seconds] This ablation uses a representative scrolling clip. The full method reaches an RMSE of 3.253 and translation variation of 0.752. Without trajectory smoothing, RMSE on sparse annotated frames improves slightly to 2.932, but translation variation rises to 1.430, almost doubling. This shows that smoothing primarily improves temporal stability rather than single-frame accuracy. Removing the LK diagnostic, redetection, or edge gating does not change this clip because Profile border evidence succeeds on every frame. These components are a safety net for abnormal cases and do not interfere with the normal main chain.")

    # Slide 8 — Limitations and conclusion
    slide = prs.slides.add_slide(blank)
    add_header(slide, "LIMITS & TAKEAWAY", "Boundary Evidence Is Still the Limitation—but the Conclusion Is Clear", 8,
               "project outline §§4–5", title_size=23.5)

    add_rect(slide, 0.66, 1.58, 5.82, 2.03, fill=RED_SOFT, line=RED)
    add_text(slide, "MAIN LIMITATIONS", 0.94, 1.87, 2.15, 0.31, size=13.5, color=RED, bold=True)
    add_text(slide, "• Weak edges / very low contrast: true gradients fade and background texture may become the stronger candidate\n"
                    "• Strong glare / occlusion: false gradients can shift a fitted line or trigger redetection and hold",
             0.94, 2.30, 5.16, 1.05, size=10.6, color=INK, line_spacing=1.10)

    add_rect(slide, 6.77, 1.58, 5.91, 2.03, fill=BLUE_SOFT, line=BLUE)
    add_text(slide, "FINAL CONCLUSION", 7.07, 1.87, 2.15, 0.31, size=13.5, color=BLUE, bold=True)
    add_text(slide,
             "The physical screen border is a better primary cue for the screen plane than independent frame detection or internal-content optical flow.",
             7.07, 2.28, 5.28, 1.00, size=14.1, color=INK, bold=True,
             align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, line_spacing=1.10)

    add_text(slide, "NEXT STEPS", 0.69, 4.00, 1.35, 0.28, size=13.5, color=BLUE, bold=True)
    next_steps = [
        (0.68, "01", "Multi-cue boundary fusion", "Combine profiles, long line segments, color differences, and rectangular constraints."),
        (4.57, "02", "Per-edge confidence", "Estimate confidence for each side and complete low-confidence edges across frames."),
        (8.46, "03", "Stronger failure recovery", "Actively reinitialize after repeated failures and expand glare/occlusion annotations."),
    ]
    for x, idx, title, body in next_steps:
        add_rect(slide, x, 4.42, 3.58, 1.62, fill=BLUE_PALE, line=LINE)
        add_text(slide, idx, x + 0.18, 4.65, 0.48, 0.26, size=10.5, color=BLUE, bold=True)
        add_text(slide, title, x + 0.65, 4.61, 2.65, 0.32, size=13.2, color=INK, bold=True)
        add_text(slide, body, x + 0.18, 5.14, 3.12, 0.54, size=10.5, color=MUTED,
                 line_spacing=1.10)

    add_text(slide, "3.87 px RMSE   ·   0.996 IoU   ·   2.45 px/frame",
             0.69, 6.35, 11.92, 0.42, size=16.4, color=BLUE, bold=True,
             align=PP_ALIGN.CENTER)
    add_notes(slide,
              "[About 35 seconds] The current method still depends on a visible and distinguishable screen boundary. Very low contrast, strong glare, and occlusion can weaken the true gradient and create stronger false edges. Future work should fuse multiple boundary cues, estimate confidence for each side, and actively reinitialize after consecutive failures. However, the experimental conclusion is already clear: allowing the physical screen border to drive the homography improves both geometric accuracy and temporal stability. This brings the full presentation to approximately six minutes.")

    return prs


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs = build_deck()
    prs.save(OUT)
    print(f"Saved {len(prs.slides)} slides to {OUT}")


if __name__ == "__main__":
    main()
