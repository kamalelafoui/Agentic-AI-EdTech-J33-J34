# -*- coding: utf-8 -*-
"""Helpers de mise en page python-docx pour les livrables EduAgentic."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from docx.enum.text import WD_LINE_SPACING

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

NAVY = RGBColor(0x0B, 0x23, 0x40)
NAVY_HEX = "0B2340"
GOLD = RGBColor(0xF4, 0xB4, 0x00)
GOLD_HEX = "F4B400"
TEAL = RGBColor(0x16, 0xA6, 0xA1)
TEAL_HEX = "16A6A1"
BLUE = RGBColor(0x3B, 0x82, 0xC4)
MUTED = RGBColor(0x6B, 0x7C, 0x93)
INK = RGBColor(0x12, 0x26, 0x3F)
LIGHT_HEX = "F4F7FB"
BORDER_HEX = "DCE7F2"
FONT = "Aptos"
FONT_LIGHT = "Aptos Display"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=60, start=90, bottom=60, end=90) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=BORDER_HEX, size=4) -> None:
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tbl_pr.append(borders)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_row_together(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)
    run._r.append(instr)
    run._r.append(fld_char2)


def add_toc(paragraph) -> None:
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "separate")
    fld_char3 = OxmlElement("w:fldChar")
    fld_char3.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)
    run._r.append(instr)
    run._r.append(fld_char2)
    run._r.append(fld_char3)


def set_character_spacing(run, twips: int = 20) -> None:
    r_pr = run._r.get_or_add_rPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:val"), str(twips))
    r_pr.append(spacing)


def set_paragraph_border(paragraph, color=GOLD_HEX, size=12, position="bottom") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    border = OxmlElement(f"w:{position}")
    border.set(qn("w:val"), "single")
    border.set(qn("w:sz"), str(size))
    border.set(qn("w:space"), "6")
    border.set(qn("w:color"), color)
    p_bdr.append(border)
    p_pr.append(p_bdr)


def new_document(
    title: str,
    kicker: str,
    subtitle: str,
    header_label: str,
    subject: str,
    author: str = "Kamal El Afoui",
    version: str = "1.0.0 — Correction finale",
    date: str = "11 novembre 2026",
) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.8)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    for name, size, color, before, after in (
        ("Heading 1", 17, NAVY, 14, 7),
        ("Heading 2", 13, NAVY, 10, 5),
        ("Heading 3", 11.5, BLUE, 8, 4),
    ):
        style = styles[name]
        style.font.name = FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for name in ("List Bullet", "List Number"):
        style = styles[name]
        style.font.name = FONT
        style.font.size = Pt(10.5)
        style.paragraph_format.space_after = Pt(3)

    # En-tête
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.paragraph_format.tab_stops.clear_all()
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(17), WD_TAB_ALIGNMENT.RIGHT)
    if (ASSETS / "logo_mark.png").exists():
        run = hp.add_run()
        run.add_picture(str(ASSETS / "logo_mark.png"), width=Cm(0.55))
        hp.add_run("  ")
    run = hp.add_run("EduAgentic")
    run.font.name = FONT
    run.font.size = Pt(8.5)
    run.font.bold = True
    run.font.color.rgb = NAVY
    run = hp.add_run("  ·  Agentic AI in Education Technology")
    run.font.size = Pt(8)
    run.font.color.rgb = MUTED
    hp.add_run("\t")
    run = hp.add_run(header_label)
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = GOLD
    set_paragraph_border(hp, color=BORDER_HEX, size=6)

    # Pied de page
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.paragraph_format.tab_stops.clear_all()
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(17), WD_TAB_ALIGNMENT.RIGHT)
    run = fp.add_run("EduAgentic v1.0 · données synthétiques · 11/11/2026")
    run.font.size = Pt(7.5)
    run.font.color.rgb = MUTED
    fp.add_run("\t")
    run = fp.add_run("page ")
    run.font.size = Pt(7.5)
    run.font.color.rgb = MUTED
    add_page_number(fp)
    for r in fp.runs:
        r.font.name = FONT

    props = doc.core_properties
    props.title = title
    props.subject = subject
    props.author = author
    props.keywords = "Agentic AI, EdTech, MCP, A2A, Langflow, Streamlit"
    props.comments = "Mini-projets J33/J34 — documentation générée par EduAgentic."
    return doc


def cover(
    doc: Document,
    kicker: str,
    title: str,
    subtitle: str,
    meta_rows: Sequence[tuple[str, str]],
    highlights: Sequence[str],
    accent=GOLD,
) -> None:
    if (ASSETS / "logo_light.png").exists():
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.add_run().add_picture(str(ASSETS / "logo_light.png"), width=Cm(11.5))
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(26)
    run = p.add_run(kicker.upper())
    run.font.name = FONT
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = accent
    set_character_spacing(run, 30)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(title)
    run.font.name = FONT_LIGHT
    run.font.size = Pt(31)
    run.font.bold = True
    run.font.color.rgb = NAVY

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run(subtitle)
    run.font.name = FONT
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(0x44, 0x56, 0x6E)

    p = doc.add_paragraph()
    set_paragraph_border(p, color=GOLD_HEX, size=16)
    p.paragraph_format.space_after = Pt(16)

    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(4.2)
    table.columns[1].width = Cm(12.2)
    for key, value in meta_rows:
        row = table.add_row()
        c0, c1 = row.cells
        c0.width = Cm(4.2)
        c1.width = Cm(12.2)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(key.upper())
        r0.font.size = Pt(7.5)
        r0.font.bold = True
        r0.font.color.rgb = MUTED
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(value)
        r1.font.size = Pt(10)
        r1.font.color.rgb = INK
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    box = doc.add_table(rows=1, cols=1)
    box.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = box.cell(0, 0)
    set_cell_shading(cell, NAVY_HEX)
    set_cell_margins(cell, top=150, start=180, bottom=140, end=180)
    p = cell.paragraphs[0]
    r = p.add_run("CE QUE COUVRE CE DOCUMENT")
    r.font.size = Pt(7.5)
    r.font.bold = True
    r.font.color.rgb = GOLD
    set_character_spacing(r, 24)
    for item in highlights:
        p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run("•  " + item)
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0xE8, 0xF0, 0xF9)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("Données 100 % synthétiques · aucun apprenant réel · dépôt reproductible")
    r.font.size = Pt(7.5)
    r.font.color.rgb = MUTED
    doc.add_page_break()


def h1(doc: Document, text: str, page_break: bool = True):
    p = doc.add_paragraph(style="Heading 1")
    if page_break:
        p.paragraph_format.page_break_before = True
    p.add_run(text)
    return p


def h2(doc: Document, text: str):
    return doc.add_paragraph(text, style="Heading 2")


def h3(doc: Document, text: str):
    return doc.add_paragraph(text, style="Heading 3")


def para(doc: Document, text: str, bold_lead: str = "", size: float = 10.5, space_after: float = 5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead)
        r.bold = True
        r.font.color.rgb = NAVY
        r.font.size = Pt(size)
        text = text[len(bold_lead):]
    r = p.add_run(text)
    r.font.size = Pt(size)
    return p


def bullets(doc: Document, items: Iterable[str], style: str = "List Bullet"):
    for item in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(3)
        # gras avant les deux-points
        if " : " in item and len(item.split(" : ")[0]) < 60:
            lead, rest = item.split(" : ", 1)
            r = p.add_run(lead + " : ")
            r.bold = True
            r.font.color.rgb = NAVY
            p.add_run(rest)
        else:
            p.add_run(item)


def table(
    doc: Document,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    widths: Sequence[float] | None = None,
    font_size: float = 8.8,
    header_fill: str = NAVY_HEX,
    zebra: bool = True,
    caption: str = "",
):
    if caption:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(caption)
        r.font.size = Pt(8)
        r.font.italic = True
        r.font.color.rgb = MUTED
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_table_borders(t)
    if widths:
        for i, width in enumerate(widths):
            t.columns[i].width = Cm(width)
    hdr = t.rows[0]
    set_repeat_table_header(hdr)
    keep_row_together(hdr)
    for i, head in enumerate(headers):
        cell = hdr.cells[i]
        if widths:
            cell.width = Cm(widths[i])
        set_cell_shading(cell, header_fill)
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(str(head))
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for idx, row_data in enumerate(rows):
        row = t.add_row()
        keep_row_together(row)
        for i, value in enumerate(row_data):
            cell = row.cells[i]
            if widths:
                cell.width = Cm(widths[i])
            set_cell_margins(cell)
            if zebra and idx % 2 == 1:
                set_cell_shading(cell, LIGHT_HEX)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(value))
            r.font.size = Pt(font_size)
            r.font.color.rgb = INK
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(doc: Document, path: Path, caption: str, width_cm: float = 16.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(9)
    r = cap.add_run(caption)
    r.font.size = Pt(8)
    r.font.italic = True
    r.font.color.rgb = MUTED
    return p


def code_block(doc: Document, code: str, language: str = "python", font_size: float = 8.0):
    t = doc.add_table(rows=2, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.columns[0].width = Cm(16.2)
    keep_row_together(t.rows[0])
    keep_row_together(t.rows[1])
    top = t.cell(0, 0)
    set_cell_shading(top, "10263F")
    set_cell_margins(top, top=40, start=110, bottom=30, end=90)
    p = top.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(language.upper())
    r.font.name = "Consolas"
    r.font.size = Pt(6.8)
    r.font.bold = True
    r.font.color.rgb = GOLD
    set_character_spacing(r, 20)
    body = t.cell(1, 0)
    set_cell_shading(body, "0B2340")
    set_cell_margins(body, top=80, start=110, bottom=100, end=110)
    p = body.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    lines = code.strip("\n").splitlines()
    for i, line in enumerate(lines):
        run = p.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xE7, 0xEF, 0xF8)
        if i < len(lines) - 1:
            run.add_break()
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def callout(doc: Document, title: str, text: str, kind: str = "info"):
    palette = {
        "info": ("EEF7FF", "1F5FA8", "EAF2FB"),
        "success": ("EAF8F4", "0C7B67", "D8F0E8"),
        "warning": ("FFF8E1", "8A6100", "F7E7B0"),
        "danger": ("FDECEA", "B23B2E", "F5CFC9"),
    }
    bg, fg, border = palette.get(kind, palette["info"])
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    set_cell_shading(cell, bg)
    set_cell_margins(cell, top=100, start=150, bottom=100, end=150)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = RGBColor.from_string(fg)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(text)
    r2.font.size = Pt(9)
    r2.font.color.rgb = INK
    # bord gauche
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:color"), border)
    borders.append(left)
    tc_pr.append(borders)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def kv_grid(doc: Document, rows: Sequence[tuple[str, str]], cols: int = 2):
    t = doc.add_table(rows=0, cols=cols * 2)
    t.autofit = False
    for row_data in rows:
        row = t.add_row()
        for i in range(cols):
            key, value = row_data[i] if i < len(row_data) else ("", "")
            kc = row.cells[i * 2]
            vc = row.cells[i * 2 + 1]
            set_cell_shading(kc, LIGHT_HEX)
            set_cell_margins(kc)
            set_cell_margins(vc)
            p = kc.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(key)
            r.font.size = Pt(8)
            r.font.bold = True
            r.font.color.rgb = MUTED
            p = vc.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(value)
            r.font.size = Pt(8.8)
            r.font.color.rgb = INK
    set_table_borders(t, color=BORDER_HEX)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
