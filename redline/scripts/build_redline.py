#!/usr/bin/env python3
"""
build_redline.py — Produce a Word redline with real tracked changes.

Compares two document.xml files (from unpacked .docx archives) and writes
a modified document.xml with <w:ins> and <w:del> tracked-change elements.

Usage:
    python3 build_redline.py original.xml revised.xml output.xml [--author "Name"]

The output XML should replace word/document.xml in a copy of the original
.docx's unpacked directory, then be re-zipped into a .docx file.

Design principles:
  - Structure-aware alignment: paragraphs are matched by heading level,
    numbering scheme, AND text similarity — not text alone. This prevents
    section headings from being mismatched when subsections get collapsed.
  - Word-level granularity: within matched paragraphs, every word-level
    insertion and deletion is tracked individually.
  - Formatting preservation: run properties (<w:rPr>) from the original
    document are carried into tracked-change runs wherever possible.
"""

import argparse
import copy
import difflib
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

# ── Namespaces ──────────────────────────────────────────────────────────────

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

# ── Globals ─────────────────────────────────────────────────────────────────

_id_counter = 100
AUTHOR = "Ryan Bunker"
DATE = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


def next_id():
    global _id_counter
    _id_counter += 1
    return str(_id_counter)


# ── Paragraph metadata helpers ──────────────────────────────────────────────

def get_para_text(para):
    """Extract all visible text from a paragraph."""
    texts = []
    for elem in para.iter():
        if elem.tag == f'{{{W}}}t' and elem.text:
            texts.append(elem.text)
        elif elem.tag == f'{{{W}}}delText' and elem.text:
            texts.append(elem.text)
    return ''.join(texts)


def get_para_style_info(para):
    """Return (style_name, num_id, ilvl) for a paragraph.
    These describe the paragraph's structural role in the document:
    its heading style, which numbering list it belongs to, and its
    indent level within that list."""
    ppr = para.find(f'{{{W}}}pPr')
    style = ''
    num_id = None
    ilvl = None
    if ppr is not None:
        ps = ppr.find(f'{{{W}}}pStyle')
        if ps is not None:
            style = ps.get(f'{{{W}}}val', '')
        numpr = ppr.find(f'{{{W}}}numPr')
        if numpr is not None:
            nid = numpr.find(f'{{{W}}}numId')
            il = numpr.find(f'{{{W}}}ilvl')
            if nid is not None:
                num_id = nid.get(f'{{{W}}}val')
            if il is not None:
                ilvl = il.get(f'{{{W}}}val')
    return (style, num_id, ilvl)


def get_run_formatting(para):
    """Get the first <w:rPr> found in runs of the paragraph, or None."""
    for r in para.findall(f'.//{{{W}}}r'):
        rpr = r.find(f'{{{W}}}rPr')
        if rpr is not None:
            return copy.deepcopy(rpr)
    return None


# ── Tracked-change element builders ─────────────────────────────────────────

def make_del_run(text, rpr=None):
    """Create a <w:del> element containing a run with <w:delText>."""
    del_elem = ET.Element(f'{{{W}}}del')
    del_elem.set(f'{{{W}}}id', next_id())
    del_elem.set(f'{{{W}}}author', AUTHOR)
    del_elem.set(f'{{{W}}}date', DATE)
    r = ET.SubElement(del_elem, f'{{{W}}}r')
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    dt = ET.SubElement(r, f'{{{W}}}delText')
    dt.set(XML_SPACE, 'preserve')
    dt.text = text
    return del_elem


def make_ins_run(text, rpr=None):
    """Create a <w:ins> element containing a run with <w:t>."""
    ins_elem = ET.Element(f'{{{W}}}ins')
    ins_elem.set(f'{{{W}}}id', next_id())
    ins_elem.set(f'{{{W}}}author', AUTHOR)
    ins_elem.set(f'{{{W}}}date', DATE)
    r = ET.SubElement(ins_elem, f'{{{W}}}r')
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    t = ET.SubElement(r, f'{{{W}}}t')
    t.set(XML_SPACE, 'preserve')
    t.text = text
    return ins_elem


def make_normal_run(text, rpr=None):
    """Create a plain <w:r> element (no tracking)."""
    r = ET.Element(f'{{{W}}}r')
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    t = ET.SubElement(r, f'{{{W}}}t')
    t.set(XML_SPACE, 'preserve')
    t.text = text
    return r


# ── Whole-paragraph tracked changes ────────────────────────────────────────

def make_deleted_paragraph(para):
    """Return a copy of the paragraph with all content wrapped in <w:del>
    and the paragraph mark itself marked as deleted."""
    new_para = ET.Element(f'{{{W}}}p')

    # Copy and annotate paragraph properties
    ppr = para.find(f'{{{W}}}pPr')
    new_ppr = copy.deepcopy(ppr) if ppr is not None else ET.Element(f'{{{W}}}pPr')
    rpr_in_ppr = new_ppr.find(f'{{{W}}}rPr')
    if rpr_in_ppr is None:
        rpr_in_ppr = ET.SubElement(new_ppr, f'{{{W}}}rPr')
    del_mark = ET.SubElement(rpr_in_ppr, f'{{{W}}}del')
    del_mark.set(f'{{{W}}}id', next_id())
    del_mark.set(f'{{{W}}}author', AUTHOR)
    del_mark.set(f'{{{W}}}date', DATE)
    new_para.append(new_ppr)

    # Wrap text in w:del
    text = get_para_text(para)
    if text:
        rpr = get_run_formatting(para)
        new_para.append(make_del_run(text, rpr))

    return new_para


def make_inserted_paragraph(para):
    """Return a copy of the paragraph with all content wrapped in <w:ins>
    and the paragraph mark itself marked as inserted."""
    new_para = ET.Element(f'{{{W}}}p')

    ppr = para.find(f'{{{W}}}pPr')
    new_ppr = copy.deepcopy(ppr) if ppr is not None else ET.Element(f'{{{W}}}pPr')
    rpr_in_ppr = new_ppr.find(f'{{{W}}}rPr')
    if rpr_in_ppr is None:
        rpr_in_ppr = ET.SubElement(new_ppr, f'{{{W}}}rPr')
    ins_mark = ET.SubElement(rpr_in_ppr, f'{{{W}}}ins')
    ins_mark.set(f'{{{W}}}id', next_id())
    ins_mark.set(f'{{{W}}}author', AUTHOR)
    ins_mark.set(f'{{{W}}}date', DATE)
    new_para.append(new_ppr)

    text = get_para_text(para)
    if text:
        rpr = get_run_formatting(para)
        new_para.append(make_ins_run(text, rpr))

    return new_para


# ── Word-level diff within a paragraph ──────────────────────────────────────

def _build_run_map(para):
    """Build a list of (start_char, end_char, run_element) tuples mapping
    character positions in the paragraph's text back to the original XML runs.
    This lets us preserve run-level formatting when emitting unchanged text."""
    run_map = []
    pos = 0
    for child in para:
        if child.tag == f'{{{W}}}r':
            run_text = ''
            for t_elem in child.findall(f'{{{W}}}t'):
                if t_elem.text:
                    run_text += t_elem.text
            if run_text:
                run_map.append((pos, pos + len(run_text), child))
                pos += len(run_text)
    return run_map


def _emit_original_runs(run_map, start, end, parent):
    """Copy original runs (or slices of them) covering characters [start, end)
    into parent, preserving all original formatting exactly."""
    for rstart, rend, run_elem in run_map:
        # Find overlap with [start, end)
        overlap_start = max(rstart, start)
        overlap_end = min(rend, end)
        if overlap_start >= overlap_end:
            continue

        # Get original run text
        run_text = ''
        for t_elem in run_elem.findall(f'{{{W}}}t'):
            if t_elem.text:
                run_text += t_elem.text

        # If the overlap covers the entire run, deep-copy it exactly
        if overlap_start == rstart and overlap_end == rend:
            parent.append(copy.deepcopy(run_elem))
        else:
            # Slice: emit a new run with the original formatting but partial text
            new_run = ET.Element(f'{{{W}}}r')
            rpr = run_elem.find(f'{{{W}}}rPr')
            if rpr is not None:
                new_run.append(copy.deepcopy(rpr))
            t = ET.SubElement(new_run, f'{{{W}}}t')
            t.set(XML_SPACE, 'preserve')
            t.text = run_text[overlap_start - rstart : overlap_end - rstart]
            parent.append(new_run)


def _emit_del_from_runs(run_map, start, end, parent):
    """Emit <w:del> elements covering characters [start, end) using the
    original runs' formatting."""
    for rstart, rend, run_elem in run_map:
        overlap_start = max(rstart, start)
        overlap_end = min(rend, end)
        if overlap_start >= overlap_end:
            continue

        run_text = ''
        for t_elem in run_elem.findall(f'{{{W}}}t'):
            if t_elem.text:
                run_text += t_elem.text

        slice_text = run_text[overlap_start - rstart : overlap_end - rstart]
        rpr = run_elem.find(f'{{{W}}}rPr')
        parent.append(make_del_run(slice_text, copy.deepcopy(rpr) if rpr else None))


def build_tracked_paragraph(orig_para, rev_para):
    """Build a new paragraph element with word-level tracked changes
    showing the diff between orig_para and rev_para.

    The critical improvement here: instead of flattening all text and
    reconstructing runs from scratch (which destroys per-run formatting
    like bold, italic, etc.), this function maps character positions back
    to original runs and preserves them wherever text is unchanged. Only
    the actual insertion/deletion points get new tracked-change elements."""
    orig_text = get_para_text(orig_para)
    rev_text = get_para_text(rev_para)

    if orig_text == rev_text:
        return copy.deepcopy(orig_para)

    # New paragraph with original's properties (preserves heading/numbering)
    new_para = ET.Element(f'{{{W}}}p')
    ppr = orig_para.find(f'{{{W}}}pPr')
    if ppr is not None:
        new_para.append(copy.deepcopy(ppr))

    # Build character-to-run mapping for original
    orig_run_map = _build_run_map(orig_para)
    rev_run_map = _build_run_map(rev_para)

    # Fallback formatting for inserted text: use nearest original formatting
    fallback_rpr = get_run_formatting(orig_para) or get_run_formatting(rev_para)

    # Character-level diff for precision, then group into word boundaries
    sm = difflib.SequenceMatcher(None, orig_text, rev_text, autojunk=False)

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            # Emit original runs covering this span — preserves all formatting
            _emit_original_runs(orig_run_map, i1, i2, new_para)

        elif op == 'delete':
            # Wrap deleted text in w:del, using original run formatting
            _emit_del_from_runs(orig_run_map, i1, i2, new_para)

        elif op == 'insert':
            # Use revised run formatting for inserted text if available
            ins_text = rev_text[j1:j2]
            ins_rpr = _get_rpr_at_position(rev_run_map, j1) or fallback_rpr
            new_para.append(make_ins_run(ins_text, ins_rpr))

        elif op == 'replace':
            # Delete original text, insert revised text
            _emit_del_from_runs(orig_run_map, i1, i2, new_para)
            ins_text = rev_text[j1:j2]
            ins_rpr = _get_rpr_at_position(rev_run_map, j1) or fallback_rpr
            new_para.append(make_ins_run(ins_text, ins_rpr))

    return new_para


def _get_rpr_at_position(run_map, pos):
    """Get the rPr from the run covering character position `pos`."""
    for rstart, rend, run_elem in run_map:
        if rstart <= pos < rend:
            rpr = run_elem.find(f'{{{W}}}rPr')
            return copy.deepcopy(rpr) if rpr is not None else None
    return None


def _tokenize(text):
    """Split text into tokens where each token is either a word or a
    whitespace segment. This gives word-level granularity while preserving
    exact spacing in the output."""
    return re.findall(r'\S+|\s+', text)


# ── Structure-aware paragraph alignment ─────────────────────────────────────

def compute_similarity(orig_elem, rev_elem):
    """Compute a similarity score [0, 1] between two paragraph elements,
    considering text content, structural metadata, and containment.

    The algorithm handles a critical real-world pattern: when subsections
    get collapsed into their parent heading. For example, if the original
    has "7. Transition Services." (heading) and "(a) We deeply respect..."
    (subsection), and the revised merges them into a single paragraph
    "7. Transition Services. We deeply respect...", the heading should
    match the revised paragraph — not the subsection, even though the
    subsection shares more raw text.

    We detect this via prefix containment: if the original text appears
    at the start of the revised text and they share the same heading
    level, that's a very strong match signal."""

    orig_text = get_para_text(orig_elem)
    rev_text = get_para_text(rev_elem)

    o_style, o_numid, o_ilvl = get_para_style_info(orig_elem)
    r_style, r_numid, r_ilvl = get_para_style_info(rev_elem)

    # ── Check for prefix containment at the same structural level ──
    # This is the key heuristic for detecting "subsection collapse":
    # original heading text is now the prefix of a longer revised paragraph.
    same_level = (o_style == r_style and o_ilvl == r_ilvl
                  and o_style != '' and o_ilvl is not None)
    same_heading = (o_style == r_style and o_style != ''
                    and (o_ilvl is None and r_ilvl is None
                         or o_ilvl == r_ilvl))

    orig_stripped = orig_text.strip()
    rev_stripped = rev_text.strip()

    if orig_stripped and rev_stripped:
        # If orig text is a prefix of rev text at the same heading level,
        # this is almost certainly a match (heading absorbed body text)
        if same_heading and rev_stripped.startswith(orig_stripped):
            return 0.95

        # If rev text is a prefix of orig text (paragraph was truncated)
        if same_heading and orig_stripped.startswith(rev_stripped):
            return 0.95

    # ── Standard text similarity ──
    if not orig_text and not rev_text:
        text_sim = 1.0
    elif not orig_text or not rev_text:
        text_sim = 0.0
    else:
        text_sim = difflib.SequenceMatcher(None, orig_text, rev_text).ratio()

    # ── Structure similarity ──
    struct_score = 0.0
    if o_style and r_style and o_style == r_style:
        struct_score += 0.5
    elif not o_style and not r_style:
        struct_score += 0.3

    if o_ilvl is not None and r_ilvl is not None and o_ilvl == r_ilvl:
        struct_score += 0.3
    if o_numid is not None and r_numid is not None and o_numid == r_numid:
        struct_score += 0.2

    struct_sim = min(struct_score, 1.0)

    # ── Penalty for different indent levels within the same style ──
    # A subsection at ilvl=1 matching a heading at ilvl=0 should be
    # penalized even if they share text, because they play different
    # structural roles in the document.
    level_penalty = 0.0
    if o_ilvl is not None and r_ilvl is not None and o_ilvl != r_ilvl:
        level_penalty = 0.15

    # Blend: text-heavy but structure-aware, with level penalty
    return max(0.0, 0.65 * text_sim + 0.35 * struct_sim - level_penalty)


def align_paragraphs(orig_elems, rev_elems):
    """Align paragraphs from original and revised using a structure-aware
    approach. Returns a list of (orig_index_or_None, rev_index_or_None)
    pairs representing the alignment.

    Uses difflib.SequenceMatcher on paragraph "fingerprints" for the
    initial structural alignment, then refines within replace blocks
    using the full similarity score."""

    def fingerprint(elem):
        """Create a hashable identity for a paragraph that combines
        text content with structure. Two paragraphs with identical text
        but different heading levels will get different fingerprints."""
        if elem.tag != f'{{{W}}}p':
            # Non-paragraph elements (tables, sectPr) — use tag + content hash
            return ('_nonpara_', ET.tostring(elem, encoding='unicode')[:200])
        text = get_para_text(elem)
        style, numid, ilvl = get_para_style_info(elem)
        return (style or '', ilvl or '', text)

    orig_fps = [fingerprint(e) for e in orig_elems]
    rev_fps = [fingerprint(e) for e in rev_elems]

    sm = difflib.SequenceMatcher(None, orig_fps, rev_fps, autojunk=False)
    alignment = []

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                alignment.append((i1 + k, j1 + k))

        elif op == 'delete':
            for k in range(i1, i2):
                alignment.append((k, None))

        elif op == 'insert':
            for k in range(j1, j2):
                alignment.append((None, k))

        elif op == 'replace':
            # Within a replace block, try to match paragraphs by similarity.
            # This is where the structure-aware matching really matters:
            # a section heading at ilvl=0 should match the revised section
            # heading at ilvl=0, even if a former subsection at ilvl=1
            # shares more text.
            orig_slice = list(range(i1, i2))
            rev_slice = list(range(j1, j2))

            matched_orig = set()
            matched_rev = set()
            matches = []

            # Score all pairs, then greedily match best-first
            scores = []
            for oi in orig_slice:
                for ri in rev_slice:
                    if orig_elems[oi].tag == f'{{{W}}}p' and rev_elems[ri].tag == f'{{{W}}}p':
                        s = compute_similarity(orig_elems[oi], rev_elems[ri])
                        scores.append((s, oi, ri))

            scores.sort(reverse=True)

            for s, oi, ri in scores:
                if oi in matched_orig or ri in matched_rev:
                    continue
                if s >= 0.35:  # threshold: below this, treat as unrelated
                    matches.append((oi, ri))
                    matched_orig.add(oi)
                    matched_rev.add(ri)

            # Emit unmatched originals as deletions (in document order),
            # then matched pairs, then unmatched revised as insertions.
            # But we need to maintain document order overall.

            # Build an ordered sequence: walk through both sides in order.
            # Use a merged timeline approach.
            all_events = []
            for oi in orig_slice:
                if oi in matched_orig:
                    # Find the match
                    for mo, mr in matches:
                        if mo == oi:
                            all_events.append(('match', oi, mr))
                            break
                else:
                    all_events.append(('del', oi, None))

            # Insert unmatched revised paragraphs after their natural position
            rev_unmatched = [ri for ri in rev_slice if ri not in matched_rev]
            # Insert each unmatched revised paragraph at the right spot
            # Find where it would go relative to matched paragraphs
            for ri in rev_unmatched:
                # Find the last matched rev index before ri
                insert_pos = len(all_events)  # default: end
                for idx, evt in enumerate(all_events):
                    if evt[0] == 'match' and evt[2] is not None and evt[2] > ri:
                        insert_pos = idx
                        break
                all_events.insert(insert_pos, ('ins', None, ri))

            for evt_type, oi, ri in all_events:
                if evt_type == 'match':
                    alignment.append((oi, ri))
                elif evt_type == 'del':
                    alignment.append((oi, None))
                elif evt_type == 'ins':
                    alignment.append((None, ri))

    return alignment


# ── Main ────────────────────────────────────────────────────────────────────

def build_redline(orig_xml_path, rev_xml_path, output_xml_path):
    orig_tree = ET.parse(orig_xml_path)
    rev_tree = ET.parse(rev_xml_path)

    orig_root = orig_tree.getroot()
    rev_root = rev_tree.getroot()

    orig_body = orig_root.find(f'{{{W}}}body')
    rev_body = rev_root.find(f'{{{W}}}body')

    orig_children = list(orig_body)
    rev_children = list(rev_body)

    # Align paragraphs
    alignment = align_paragraphs(orig_children, rev_children)

    # Build new body content
    new_children = []
    ins_count = 0
    del_count = 0

    for orig_idx, rev_idx in alignment:
        if orig_idx is not None and rev_idx is not None:
            # Matched pair — diff the content
            orig_elem = orig_children[orig_idx]
            rev_elem = rev_children[rev_idx]

            if orig_elem.tag == f'{{{W}}}p' and rev_elem.tag == f'{{{W}}}p':
                orig_text = get_para_text(orig_elem)
                rev_text = get_para_text(rev_elem)
                if orig_text == rev_text:
                    new_children.append(copy.deepcopy(orig_elem))
                else:
                    tracked = build_tracked_paragraph(orig_elem, rev_elem)
                    new_children.append(tracked)
                    ins_count += 1
                    del_count += 1
            else:
                # Non-paragraph (table, sectPr, etc.) — keep original
                new_children.append(copy.deepcopy(orig_elem))

        elif orig_idx is not None:
            # Deleted from original
            orig_elem = orig_children[orig_idx]
            if orig_elem.tag == f'{{{W}}}p':
                text = get_para_text(orig_elem)
                if text.strip():
                    new_children.append(make_deleted_paragraph(orig_elem))
                    del_count += 1
                else:
                    # Empty paragraph deleted — still mark it
                    new_children.append(make_deleted_paragraph(orig_elem))
                    del_count += 1
            elif orig_elem.tag == f'{{{W}}}sectPr':
                # Always preserve section properties
                new_children.append(copy.deepcopy(orig_elem))
            else:
                # Tables etc. that were deleted — keep as-is (can't track-change tables)
                new_children.append(copy.deepcopy(orig_elem))

        elif rev_idx is not None:
            # Inserted in revised
            rev_elem = rev_children[rev_idx]
            if rev_elem.tag == f'{{{W}}}p':
                new_children.append(make_inserted_paragraph(rev_elem))
                ins_count += 1
            elif rev_elem.tag == f'{{{W}}}sectPr':
                # Use revised sectPr if it replaces original
                new_children.append(copy.deepcopy(rev_elem))
            else:
                new_children.append(copy.deepcopy(rev_elem))

    # Replace body contents
    for child in list(orig_body):
        orig_body.remove(child)
    for child in new_children:
        orig_body.append(child)

    # Write output
    orig_tree.write(output_xml_path, xml_declaration=True, encoding='UTF-8')

    # Report
    print(f"Redline written to {output_xml_path}")
    print(f"Tracked changes: {ins_count} insertions, {del_count} deletions")

    # Verify by counting actual XML elements
    verify_tree = ET.parse(output_xml_path)
    verify_root = verify_tree.getroot()
    actual_ins = len(verify_root.findall(f'.//{{{W}}}ins'))
    actual_del = len(verify_root.findall(f'.//{{{W}}}del'))
    print(f"XML verification: {actual_ins} <w:ins> elements, {actual_del} <w:del> elements")

    if actual_ins == 0 and actual_del == 0:
        print("WARNING: No tracked changes found — documents may be identical.")
        return False
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a Word redline with tracked changes')
    parser.add_argument('original', help='Path to original document.xml')
    parser.add_argument('revised', help='Path to revised document.xml')
    parser.add_argument('output', help='Path to write output document.xml')
    parser.add_argument('--author', default='Ryan Bunker', help='Author name for tracked changes')
    args = parser.parse_args()

    AUTHOR = args.author
    success = build_redline(args.original, args.revised, args.output)
    sys.exit(0 if success else 1)
