#!/usr/bin/env python3
"""
visual_redline.py — Convert tracked-change XML into visual formatting.

Takes a redline document.xml containing real <w:ins> and <w:del> tracked
changes and produces a clean document.xml where:
  - Deleted text → red, strikethrough
  - Inserted text → blue, double-underline

This eliminates all tracked-change markup so LibreOffice (or any converter)
renders the PDF identically to how Word shows "Final Showing Markup" —
without the numbering/list artifacts that LibreOffice introduces when it
encounters actual tracked-change elements around auto-numbered paragraphs.

Usage:
    python3 visual_redline.py input_document.xml output_document.xml
"""

import copy
import sys
import xml.etree.ElementTree as ET

NS = {
    'w':  'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r':  'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'a':  'http://schemas.openxmlformats.org/drawingml/2006/main',
    'v':  'urn:schemas-microsoft-com:vml',
    'o':  'urn:schemas-microsoft-com:office:office',
    'm':  'http://schemas.openxmlformats.org/officeDocument/2006/math',
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

W = NS['w']
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

# Colors
RED = "FF0000"
BLUE = "0000FF"


def make_rpr_with_del_style(existing_rpr=None):
    """Create or augment an rPr with red color + strikethrough."""
    if existing_rpr is not None:
        rpr = copy.deepcopy(existing_rpr)
    else:
        rpr = ET.Element(f'{{{W}}}rPr')

    # Set color to red (replace if exists)
    color = rpr.find(f'{{{W}}}color')
    if color is None:
        color = ET.SubElement(rpr, f'{{{W}}}color')
    color.set(f'{{{W}}}val', RED)

    # Add strikethrough
    strike = rpr.find(f'{{{W}}}strike')
    if strike is None:
        strike = ET.SubElement(rpr, f'{{{W}}}strike')
    strike.set(f'{{{W}}}val', 'true')

    return rpr


def make_rpr_with_ins_style(existing_rpr=None):
    """Create or augment an rPr with blue color + double-underline."""
    if existing_rpr is not None:
        rpr = copy.deepcopy(existing_rpr)
    else:
        rpr = ET.Element(f'{{{W}}}rPr')

    # Set color to blue (replace if exists)
    color = rpr.find(f'{{{W}}}color')
    if color is None:
        color = ET.SubElement(rpr, f'{{{W}}}color')
    color.set(f'{{{W}}}val', BLUE)

    # Add double-underline
    u = rpr.find(f'{{{W}}}u')
    if u is None:
        u = ET.SubElement(rpr, f'{{{W}}}u')
    u.set(f'{{{W}}}val', 'double')
    u.set(f'{{{W}}}color', BLUE)

    return rpr


def convert_del_element(del_elem):
    """Convert a <w:del> element into plain runs with red strikethrough.
    Returns a list of <w:r> elements."""
    runs = []
    for r in del_elem.findall(f'{{{W}}}r'):
        new_r = ET.Element(f'{{{W}}}r')

        # Get existing rPr or create new one
        existing_rpr = r.find(f'{{{W}}}rPr')
        new_rpr = make_rpr_with_del_style(existing_rpr)
        new_r.append(new_rpr)

        # Convert <w:delText> to <w:t>
        for dt in r.findall(f'{{{W}}}delText'):
            t = ET.SubElement(new_r, f'{{{W}}}t')
            t.set(XML_SPACE, 'preserve')
            t.text = dt.text or ''

        # Also keep any regular <w:t> elements (shouldn't be common in del)
        for t_elem in r.findall(f'{{{W}}}t'):
            new_t = ET.SubElement(new_r, f'{{{W}}}t')
            new_t.set(XML_SPACE, 'preserve')
            new_t.text = t_elem.text or ''

        runs.append(new_r)
    return runs


def convert_ins_element(ins_elem):
    """Convert a <w:ins> element into plain runs with blue double-underline.
    Returns a list of <w:r> elements."""
    runs = []
    for r in ins_elem.findall(f'{{{W}}}r'):
        new_r = ET.Element(f'{{{W}}}r')

        existing_rpr = r.find(f'{{{W}}}rPr')
        new_rpr = make_rpr_with_ins_style(existing_rpr)
        new_r.append(new_rpr)

        # Keep <w:t> elements as-is
        for t_elem in r.findall(f'{{{W}}}t'):
            new_t = ET.SubElement(new_r, f'{{{W}}}t')
            new_t.set(XML_SPACE, 'preserve')
            new_t.text = t_elem.text or ''

        runs.append(new_r)
    return runs


def clean_ppr_tracked_changes(ppr):
    """Remove tracked-change markers from paragraph properties.
    These are the <w:del> and <w:ins> elements inside <w:pPr><w:rPr>
    that mark the paragraph break itself as inserted/deleted."""
    if ppr is None:
        return
    rpr = ppr.find(f'{{{W}}}rPr')
    if rpr is None:
        return

    for del_mark in rpr.findall(f'{{{W}}}del'):
        rpr.remove(del_mark)
    for ins_mark in rpr.findall(f'{{{W}}}ins'):
        rpr.remove(ins_mark)

    # If rPr is now empty, remove it
    if len(rpr) == 0 and not rpr.attrib:
        ppr.remove(rpr)


def process_paragraph(para):
    """Process a single paragraph: replace tracked-change elements with
    visually-formatted runs."""
    # Clean tracked-change markers from paragraph properties
    ppr = para.find(f'{{{W}}}pPr')
    clean_ppr_tracked_changes(ppr)

    # Collect new children in order
    new_children = []
    for child in list(para):
        if child.tag == f'{{{W}}}pPr':
            new_children.append(child)
        elif child.tag == f'{{{W}}}del':
            new_children.extend(convert_del_element(child))
        elif child.tag == f'{{{W}}}ins':
            new_children.extend(convert_ins_element(child))
        elif child.tag == f'{{{W}}}r':
            new_children.append(child)
        else:
            # Bookmarks, hyperlinks, etc. — keep as-is
            new_children.append(child)

    # Replace paragraph's children
    for child in list(para):
        para.remove(child)
    for child in new_children:
        para.append(child)


def convert_visual_redline(input_path, output_path):
    """Main entry point: read tracked-change XML, write visual-format XML."""
    tree = ET.parse(input_path)
    root = tree.getroot()
    body = root.find(f'{{{W}}}body')

    if body is None:
        print("ERROR: No <w:body> found in input XML")
        sys.exit(1)

    # Count tracked changes before conversion
    ins_before = len(root.findall(f'.//{{{W}}}ins'))
    del_before = len(root.findall(f'.//{{{W}}}del'))

    # Process every paragraph
    for para in body.findall(f'.//{{{W}}}p'):
        process_paragraph(para)

    # Verify all tracked changes were removed
    ins_after = len(root.findall(f'.//{{{W}}}ins'))
    del_after = len(root.findall(f'.//{{{W}}}del'))

    print(f"Converted {ins_before} <w:ins> and {del_before} <w:del> to visual formatting")
    if ins_after > 0 or del_after > 0:
        print(f"WARNING: {ins_after} <w:ins> and {del_after} <w:del> remain (may be in tables or nested elements)")

    tree.write(output_path, xml_declaration=True, encoding='UTF-8')
    print(f"Visual redline written to {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input_document.xml output_document.xml")
        sys.exit(1)
    convert_visual_redline(sys.argv[1], sys.argv[2])
