#!/usr/bin/env python3
"""
Fix spacing in an Acute legal document to match the ABP Capital template.

This script processes a working directory (unpacked .docx) and inserts the
spacing patterns that match the template:

1. Empty BodyText paragraph before each ARTICLE heading
2. Empty Section101Heading paragraph (numbering suppressed) after each ARTICLE title
3. Empty Section101Heading paragraph (numbering suppressed, indent left=720) after each SECTIONHEADING
4. Adds w:spacing w:after="240" w:line="242" w:lineRule="auto" to each aText paragraph
5. Adds w:spacing w:after="240" w:line="242" w:lineRule="auto" to each iText paragraph

Usage:
    python fix_spacing.py <working_dir> <output.docx> --template <template.docx>

Arguments:
    working_dir   Path to the unpacked .docx working directory (will be modified in place)
    output.docx   Path for the final packed .docx output
    --template    Path to the original template .docx (used by pack.py for relationship/media inheritance)
"""

import re
import argparse
import subprocess
import os
import sys


def find_pack_script():
    """Locate the pack.py script from the docx skill."""
    candidates = [
        os.path.join(os.getcwd(), "mnt", ".claude", "skills", "docx", "scripts", "office", "pack.py"),
        # Absolute fallback paths for different session structures
    ]
    # Also search relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up from acute/skills/acute-legal-format/scripts/ to the workspace root
    for levels_up in range(1, 8):
        base = script_dir
        for _ in range(levels_up):
            base = os.path.dirname(base)
        candidate = os.path.join(base, ".claude", "skills", "docx", "scripts", "office", "pack.py")
        candidates.append(candidate)
        # Also try mnt/.claude path
        candidate2 = os.path.join(base, "mnt", ".claude", "skills", "docx", "scripts", "office", "pack.py")
        candidates.append(candidate2)

    for c in candidates:
        if os.path.exists(c):
            return c
    return None


# -- Empty paragraph templates --

EMPTY_BODYTEXT = (
    '<w:p><w:pPr><w:pStyle w:val="BodyText"/>'
    '<w:spacing w:line="242" w:lineRule="auto"/>'
    '</w:pPr></w:p>'
)

EMPTY_SECTION101_NO_NUM = (
    '<w:p><w:pPr><w:pStyle w:val="Section101Heading"/>'
    '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
    '</w:pPr></w:p>'
)

EMPTY_SECTION101_NO_NUM_INDENT = (
    '<w:p><w:pPr><w:pStyle w:val="Section101Heading"/>'
    '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
    '<w:ind w:left="720"/>'
    '</w:pPr></w:p>'
)


def get_style(elem_xml):
    """Extract the paragraph style from XML."""
    m = re.search(r'<w:pStyle w:val="([^"]+)"', elem_xml)
    return m.group(1) if m else None


def is_empty_para(elem_xml):
    """Check if paragraph has no text content."""
    return '<w:t' not in elem_xml


def has_spacing_after(elem_xml):
    """Check if paragraph already has w:spacing with w:after."""
    return 'w:after=' in elem_xml


def parse_body_elements(body_content):
    """Parse body content into a list of (type, xml) tuples."""
    elements = []
    pos = 0
    while pos < len(body_content):
        # Skip whitespace
        ws_match = re.match(r'\s+', body_content[pos:])
        if ws_match:
            pos += ws_match.end()
            continue

        # Table
        if body_content[pos:].startswith('<w:tbl'):
            tbl_end = body_content.find('</w:tbl>', pos)
            if tbl_end == -1:
                break
            tbl_end += len('</w:tbl>')
            elements.append(('tbl', body_content[pos:tbl_end]))
            pos = tbl_end
            continue

        # Paragraph
        if body_content[pos:].startswith('<w:p'):
            p_end = body_content.find('</w:p>', pos)
            if p_end == -1:
                p_end = body_content.find('/>', pos)
                if p_end == -1:
                    break
                p_end += 2
            else:
                p_end += len('</w:p>')
            elements.append(('p', body_content[pos:p_end]))
            pos = p_end
            continue

        # Section properties
        if body_content[pos:].startswith('<w:sectPr'):
            sect_end = body_content.find('</w:sectPr>', pos)
            if sect_end == -1:
                break
            sect_end += len('</w:sectPr>')
            elements.append(('sectPr', body_content[pos:sect_end]))
            pos = sect_end
            continue

        pos += 1

    return elements


def apply_spacing_rules(elements):
    """Apply all spacing rules and return new element list."""
    new_elements = []
    i = 0
    while i < len(elements):
        etype, exml = elements[i]
        style = get_style(exml) if etype == 'p' else None

        # --- Rule 1: Insert empty BodyText before ARTICLE paragraphs ---
        if style == 'ARTICLE' and '<w:numId w:val="0"/>' not in exml:
            # Auto-numbered ARTICLE paragraph
            if new_elements:
                prev_type, prev_xml = new_elements[-1]
                prev_style = get_style(prev_xml) if prev_type == 'p' else None
                if not (prev_style == 'BodyText' and is_empty_para(prev_xml)):
                    new_elements.append(('p', EMPTY_BODYTEXT))

            new_elements.append((etype, exml))
            i += 1

            # Next should be the ARTICLE title paragraph (with numId=0)
            if i < len(elements):
                etype2, exml2 = elements[i]
                style2 = get_style(exml2) if etype2 == 'p' else None
                if style2 == 'ARTICLE' and '<w:numId w:val="0"/>' in exml2:
                    new_elements.append((etype2, exml2))
                    i += 1
                    # --- Rule 2: Insert empty Section101Heading after ARTICLE title ---
                    new_elements.append(('p', EMPTY_SECTION101_NO_NUM))
                    continue
            continue

        # --- Rule 3: Insert empty Section101Heading after SECTIONHEADING ---
        if style == 'SECTIONHEADING' and not is_empty_para(exml):
            new_elements.append((etype, exml))
            i += 1
            if i < len(elements):
                next_type, next_xml = elements[i]
                next_style = get_style(next_xml) if next_type == 'p' else None
                if not (next_style == 'Section101Heading' and is_empty_para(next_xml)):
                    new_elements.append(('p', EMPTY_SECTION101_NO_NUM_INDENT))
            continue

        # --- Rule 4 & 5: Add spacing to aText and iText paragraphs ---
        if style in ('aText', 'iText') and not is_empty_para(exml):
            if not has_spacing_after(exml):
                spacing_xml = '<w:spacing w:after="240" w:line="242" w:lineRule="auto"/>'
                if '<w:pPr>' in exml:
                    pstyle_end = re.search(r'<w:pStyle[^/]*/>', exml)
                    if pstyle_end:
                        insert_pos = pstyle_end.end()
                        exml = exml[:insert_pos] + spacing_xml + exml[insert_pos:]
                    else:
                        ppr_pos = exml.find('<w:pPr>') + len('<w:pPr>')
                        exml = exml[:ppr_pos] + spacing_xml + exml[ppr_pos:]
                else:
                    p_tag_end = exml.find('>') + 1
                    exml = (
                        exml[:p_tag_end]
                        + '<w:pPr><w:pStyle w:val="' + style + '"/>'
                        + spacing_xml + '</w:pPr>'
                        + exml[p_tag_end:]
                    )
            new_elements.append((etype, exml))
            i += 1
            continue

        # Default: pass through
        new_elements.append((etype, exml))
        i += 1

    return new_elements


def process_document(doc_path):
    """Read, process, and write back the document.xml with spacing fixes."""
    with open(doc_path, "r", encoding="utf-8") as f:
        xml = f.read()

    # Split into before-body, body-content, after-body
    body_match = re.search(r'(<w:body[^>]*>)(.*?)(</w:body>)', xml, re.DOTALL)
    if not body_match:
        raise ValueError("Could not find w:body in document.xml")

    before_body = xml[:body_match.start()] + body_match.group(1)
    body_content = body_match.group(2)
    after_body = body_match.group(3) + xml[body_match.end():]

    # Extract final sectPr (must be preserved at end of body)
    sect_pr_match = re.search(
        r'(<w:sectPr[^/]*/>|<w:sectPr[^>]*>.*?</w:sectPr>)\s*$',
        body_content, re.DOTALL
    )
    final_sect_pr = ""
    if sect_pr_match:
        final_sect_pr = sect_pr_match.group(0)
        body_content = body_content[:sect_pr_match.start()]

    # Parse and process
    elements = parse_body_elements(body_content)
    new_elements = apply_spacing_rules(elements)

    # Reassemble
    new_body = "\n    ".join(exml for _, exml in new_elements)
    new_xml = before_body + "\n    " + new_body + "\n    " + final_sect_pr + "\n  " + after_body

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(new_xml)

    print(f"Processed {len(elements)} elements -> {len(new_elements)} elements")
    print(f"Added {len(new_elements) - len(elements)} spacing elements")


def main():
    parser = argparse.ArgumentParser(
        description="Fix spacing in an Acute legal document to match the ABP Capital template."
    )
    parser.add_argument("working_dir", help="Path to the unpacked .docx working directory")
    parser.add_argument("output", help="Path for the final packed .docx output")
    parser.add_argument("--template", required=True, help="Path to the original template .docx")
    args = parser.parse_args()

    doc_path = os.path.join(args.working_dir, "word", "document.xml")
    if not os.path.exists(doc_path):
        print(f"ERROR: {doc_path} not found", file=sys.stderr)
        sys.exit(1)

    # Apply spacing fixes
    process_document(doc_path)

    # Find and run pack.py
    pack_script = find_pack_script()
    if not pack_script:
        print("WARNING: Could not find pack.py. Document XML has been fixed but not packed.", file=sys.stderr)
        print("Run pack.py manually to create the final .docx", file=sys.stderr)
        sys.exit(0)

    print(f"Packing with: {pack_script}")
    result = subprocess.run(
        ["python3", pack_script, args.working_dir, args.output, "--original", args.template],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)

    print(f"Done! Output: {args.output}")


if __name__ == "__main__":
    main()
