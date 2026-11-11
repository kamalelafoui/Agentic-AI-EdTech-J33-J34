# -*- coding: utf-8 -*-
"""Helpers de design pour les présentations EduAgentic (python-pptx)."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

NAVY = RGBColor(0x0B, 0x23, 0x40)
NAVY2 = RGBColor(0x14, 0x36, 0x5C)
GOLD = RGBColor(0xF4, 0xB4, 0x00)
TEAL = RGBColor(0x16, 0xA6, 0xA1)
BLUE = RGBColor(0x3B, 0x82, 0xC4)
GREEN = RGBColor(0x2E, 0x8B, 0x72)
PURPLE = RGBColor(0x7A, 0x5A, 0xA6)
MUTED = RGBColor(0x6B, 0x7C, 0x93)
INK = RGBColor(0x12, 0x26, 0x3F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG = RGBColor(0xF5, 0xF8, 0xFC)
LIGHT = RGBColor(0xEA, 0xF2, 0xFA)
BORDER = RGBColor(0xDC, 0xE7, 0xF2)
SOFT_GOLD = RGBColor(0xFF, 0xF7, 0xE0)

TITLE_FONT = "Aptos Display"
BODY_FONT = "Aptos"


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(
    slide,
    x,
    y,
    w,
    h,
    fill,
    line=None,
    radius=None,
    shadow=False,
    shape=MSO_SHAPE.RECTANGLE,
):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.8)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    if not shadow:
        shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def line(slide, x1, y1, x2, y2, color=GOLD, width=1.5, dash=False):
    from pptx.enum.shapes import MSO_CONNECTOR

    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    if dash:
        from pptx.enum.dml import MSO_LINE_DASH_STYLE

        conn.line.dash_style = MSO_LINE_DASH_STYLE.DASH


def txt(
    slide,
    x,
    y,
    w,
    h,
    text,
    size=16,
    color=INK,
    bold=False,
    font=BODY_FONT,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    italic=False,
    line_spacing=1.0,
    margins=(0.02, 0.02, 0.02, 0.02),
    char_spacing=None,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margins[0])
    tf.margin_right = Inches(margins[1])
    tf.margin_top = Inches(margins[2])
    tf.margin_bottom = Inches(margins[3])
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    if char_spacing is not None:
        from pptx.oxml.ns import qn

        run._r.get_or_add_rPr().set("spc", str(int(char_spacing * 100)))
    return box


def rich(
    slide,
    x,
    y,
    w,
    h,
    segments: Sequence[tuple[str, dict]],
    size=16,
    color=INK,
    font=BODY_FONT,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing=1.0,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for text, opts in segments:
        run = p.add_run()
        run.text = text
        run.font.name = opts.get("font", font)
        run.font.size = Pt(opts.get("size", size))
        run.font.bold = opts.get("bold", False)
        run.font.italic = opts.get("italic", False)
        run.font.color.rgb = opts.get("color", color)
    return box


def paragraphs(
    slide,
    x,
    y,
    w,
    h,
    items: Sequence[tuple[str, str]],
    size=15,
    color=INK,
    bullet_color=GOLD,
    space_after=8,
    line_spacing=1.05,
    lead_color=NAVY,
):
    """items = [(texte_gras, texte_normal), ...]"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for i, (lead, body) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = "•  "
        r.font.name = BODY_FONT
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = bullet_color
        if lead:
            r = p.add_run()
            r.text = lead
            r.font.name = BODY_FONT
            r.font.size = Pt(size)
            r.font.bold = True
            r.font.color.rgb = lead_color
        if body:
            r = p.add_run()
            r.text = body
            r.font.name = BODY_FONT
            r.font.size = Pt(size)
            r.font.color.rgb = color
    return box


def bg(slide, color=BG):
    rect(slide, 0, 0, 13.333, 7.5, color, shape=MSO_SHAPE.RECTANGLE)
    # formes décoratives discrètes
    rect(slide, 12.35, -0.6, 1.8, 1.8, RGBColor(0xE7, 0xF0, 0xFA), shape=MSO_SHAPE.OVAL)
    rect(slide, -0.55, 6.75, 1.3, 1.3, RGBColor(0xFD, 0xF3, 0xD6), shape=MSO_SHAPE.OVAL)


def header(slide, kicker, title, day="", subtitle=""):
    bg(slide)
    rect(slide, 0, 0, 0.18, 7.5, GOLD)
    txt(slide, 0.65, 0.38, 10.5, 0.3, kicker.upper(), 9, GOLD, True, char_spacing=2)
    txt(slide, 0.65, 0.68, 11.6, 0.85, title, 27, NAVY, True, TITLE_FONT, line_spacing=0.95)
    if subtitle:
        txt(slide, 0.65, 1.55, 11.6, 0.45, subtitle, 12, MUTED)
    if day:
        pill(slide, 11.55, 0.38, 1.15, 0.32, day, NAVY, WHITE, 9, bold=True)


def footer(slide, number, total=None, label="EduAgentic · Agentic AI in Education Technology"):
    line(slide, 0.6, 7.02, 12.73, 7.02, BORDER, 0.8)
    txt(slide, 0.6, 7.08, 8.5, 0.25, label, 8, MUTED)
    page = f"{number:02d}" + (f" / {total:02d}" if total else "")
    txt(slide, 12.0, 7.08, 0.75, 0.25, page, 8, MUTED, align=PP_ALIGN.RIGHT)


def pill(slide, x, y, w, h, text, fill=NAVY, color=WHITE, size=9, bold=True, line_color=None):
    shp = rect(slide, x, y, w, h, fill, line=line_color, radius=0.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tf = shp.text_frame
    tf.clear()
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = BODY_FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return shp


def card(slide, x, y, w, h, title, body="", accent=GOLD, icon="", tag="", body_size=12.5, title_size=15):
    rect(slide, x, y, w, h, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, 0.08, h, accent)
    if icon:
        txt(slide, x + 0.18, y + 0.14, 0.55, 0.4, icon, 18, NAVY, True)
    txt(slide, x + (0.72 if icon else 0.24), y + 0.16, w - (0.95 if icon else 0.45), 0.55, title, title_size, NAVY, True, line_spacing=0.95)
    if body:
        txt(slide, x + 0.24, y + 0.75, w - 0.45, h - 0.95, body, body_size, MUTED, line_spacing=1.05)
    if tag:
        txt(slide, x + 0.24, y + h - 0.36, w - 0.45, 0.25, tag, 8.5, accent, True)


def stat(slide, x, y, w, h, value, label, accent=TEAL, sub="", value_size=30):
    rect(slide, x, y, w, h, WHITE, line=BORDER, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, w, 0.06, accent)
    txt(slide, x + 0.18, y + 0.18, w - 0.3, 0.6, value, value_size, NAVY, True, TITLE_FONT, line_spacing=0.9)
    txt(slide, x + 0.18, y + 0.78, w - 0.3, 0.35, label, 9.5, MUTED, True)
    if sub:
        txt(slide, x + 0.18, y + h - 0.35, w - 0.3, 0.25, sub, 8, accent, True)


def image(slide, path: Path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)


def code(slide, x, y, w, h, text, size=10, lang="python"):
    rect(slide, x, y, w, h, RGBColor(0x08, 0x1B, 0x30), radius=0.05, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, w, 0.28, RGBColor(0x10, 0x2A, 0x48), radius=0.05, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(slide, x + 0.15, y + 0.055, w - 0.3, 0.2, lang.upper(), 7.5, GOLD, True, char_spacing=1.5)
    txt(slide, x + 0.18, y + 0.38, w - 0.3, h - 0.45, text, size, RGBColor(0xE7, 0xEF, 0xF8), font="Consolas", line_spacing=0.95)


def table(slide, x, y, w, h, headers, rows, col_widths=None, font_size=10, header_fill=NAVY):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    if col_widths:
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Inches(cw)
    for i, head in enumerate(headers):
        cell = tbl.cell(0, i)
        cell.text = ""
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        p = cell.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = head
        r.font.name = BODY_FONT
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = WHITE
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.06)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
    for ri, row in enumerate(rows, 1):
        for ci, value in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.text = ""
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if ri % 2 else RGBColor(0xF4, 0xF7, 0xFB)
            p = cell.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(value)
            r.font.name = BODY_FONT
            r.font.size = Pt(font_size)
            r.font.color.rgb = INK
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
    return tbl


def notes(slide, text: str):
    slide.notes_slide.notes_text_frame.text = text


def cover(
    prs,
    kicker,
    title,
    subtitle,
    meta,
    chips,
    image_path: Path | None = None,
    dark=True,
):
    slide = blank(prs)
    if dark:
        rect(slide, 0, 0, 13.333, 7.5, NAVY)
        rect(slide, 9.2, -1.6, 5.6, 5.6, RGBColor(0x12, 0x3A, 0x60), shape=MSO_SHAPE.OVAL)
        rect(slide, 10.9, 3.9, 2.9, 2.9, RGBColor(0x0F, 0x31, 0x55), shape=MSO_SHAPE.OVAL)
        rect(slide, 9.9, 0.2, 3.2, 3.2, RGBColor(0xF4, 0xB4, 0x00), shape=MSO_SHAPE.OVAL)
        # masque pour créer un croissant
        rect(slide, 8.7, -0.35, 3.4, 3.4, NAVY, shape=MSO_SHAPE.OVAL)
        image(slide, ASSETS / "logo.png", 0.6, 0.45, w=3.55)
        txt(slide, 0.65, 2.25, 8.8, 0.3, kicker.upper(), 10, GOLD, True, char_spacing=3)
        txt(slide, 0.65, 2.65, 8.8, 1.55, title, 34, WHITE, True, TITLE_FONT, line_spacing=0.92)
        txt(slide, 0.65, 4.35, 8.5, 0.8, subtitle, 14, RGBColor(0xC9, 0xD8, 0xE8), line_spacing=1.1)
        for i, chip in enumerate(chips):
            pill(slide, 0.65 + i * 2.35, 5.5, 2.15, 0.34, chip, RGBColor(0x16, 0x3A, 0x5D), WHITE, 9, line_color=RGBColor(0x2A, 0x52, 0x77))
        line(slide, 0.65, 6.55, 8.6, 6.55, RGBColor(0x2A, 0x52, 0x77), 0.8)
        txt(slide, 0.65, 6.68, 8.6, 0.4, meta, 9.5, RGBColor(0x9F, 0xB8, 0xD0))
    return slide


def section(prs, kicker, title, subtitle="", day="", number=0):
    slide = blank(prs)
    bg(slide)
    rect(slide, 0, 0, 0.18, 7.5, GOLD)
    txt(slide, 0.65, 1.1, 11.5, 0.35, kicker.upper(), 10, GOLD, True, char_spacing=2)
    txt(slide, 0.65, 1.55, 11.5, 1.5, title, 32, NAVY, True, TITLE_FONT, line_spacing=0.95)
    if subtitle:
        txt(slide, 0.65, 3.2, 10.5, 0.8, subtitle, 14, MUTED, line_spacing=1.15)
    if day:
        pill(slide, 11.55, 0.38, 1.15, 0.32, day, NAVY, WHITE, 9)
    footer(slide, number)
    return slide
