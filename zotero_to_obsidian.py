#!/usr/bin/env python3
"""
zotero_to_obsidian.py
---------------------
Converts a BibTeX file exported from Zotero into one Markdown note per paper,
ready to drop into your Obsidian vault's Bibliography/ folder.

Usage:
    python3 zotero_to_obsidian.py my_library.bib ./vault/Bibliography/

Requirements: Python 3.8+  (no external libraries needed)

See README-Extended.md for full instructions on exporting from Zotero.
"""

import re
import sys
import os
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# BibTeX parser (pure stdlib)
# ---------------------------------------------------------------------------

def parse_bib_file(bib_path: str) -> list[dict]:
    """Parse a .bib file and return a list of entry dicts."""
    with open(bib_path, "r", encoding="utf-8") as f:
        raw = f.read()

    entries = []
    # Match each @type{key, ...} block
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.+?)\n\}", re.DOTALL)

    for match in pattern.finditer(raw):
        entry_type = match.group(1).lower()
        if entry_type in ("comment", "string", "preamble"):
            continue

        cite_key = match.group(2).strip()
        body = match.group(3)

        entry = {
            "_type": entry_type,
            "_key": cite_key,
        }

        # Parse individual fields: field = {value} or field = "value"
        field_pattern = re.compile(
            r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"((?:[^\"]*)*)\")",
            re.DOTALL,
        )
        for f in field_pattern.finditer(body):
            field_name = f.group(1).lower()
            field_val = (f.group(2) if f.group(2) is not None else f.group(3)) or ""
            # Clean up LaTeX artefacts and extra whitespace
            field_val = clean_latex(field_val.strip())
            entry[field_name] = field_val

        entries.append(entry)

    return entries


def clean_latex(text: str) -> str:
    """Remove common LaTeX commands and braces from a string."""
    # Remove \emph{}, \textbf{}, \textit{} etc.
    text = re.sub(r"\\(?:emph|textbf|textit|textrm|mathrm)\{([^}]*)\}", r"\1", text)
    # Remove remaining curly braces used for case protection
    text = text.replace("{", "").replace("}", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Common LaTeX characters
    replacements = {
        "--": "–", "---": "—",
        "\\&": "&", "\\'e": "é", "\\'E": "É",
        '\\"o': "ö", '\\"u': "ü", '\\"a': "ä",
        "\\`e": "è", "\\^e": "ê", "\\~n": "ñ",
        "\\alpha": "α", "\\beta": "β", "\\gamma": "γ",
    }
    for latex, char in replacements.items():
        text = text.replace(latex, char)
    return text.strip()


# ---------------------------------------------------------------------------
# Author formatting
# ---------------------------------------------------------------------------

def format_authors(authors_raw: str) -> str:
    """
    Convert BibTeX author string to a readable list.
    'Lastname, Firstname and Lastname2, Firstname2' → 'Lastname F, Lastname2 F2'
    """
    if not authors_raw:
        return ""
    parts = re.split(r"\s+and\s+", authors_raw, flags=re.IGNORECASE)
    formatted = []
    for part in parts:
        part = part.strip()
        if "," in part:
            last, first = part.split(",", 1)
            initials = "".join(w[0] + "." for w in first.split() if w)
            formatted.append(f"{last.strip()} {initials}")
        else:
            # "Firstname Lastname" order
            words = part.split()
            if len(words) >= 2:
                initials = "".join(w[0] + "." for w in words[:-1])
                formatted.append(f"{words[-1]} {initials}")
            else:
                formatted.append(part)
    # Show first 3 authors then et al.
    if len(formatted) > 3:
        return ", ".join(formatted[:3]) + " et al."
    return ", ".join(formatted)


def first_author_lastname(authors_raw: str) -> str:
    """Extract the first author's last name for use in the filename."""
    if not authors_raw:
        return "Unknown"
    first = re.split(r"\s+and\s+", authors_raw, flags=re.IGNORECASE)[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    words = first.split()
    return words[-1] if words else "Unknown"


# ---------------------------------------------------------------------------
# Filename generation
# ---------------------------------------------------------------------------

def make_filename(entry: dict) -> str:
    """
    Build a clean, human-readable filename:
    'Lastname YYYY — Title truncated.md'
    """
    author = first_author_lastname(entry.get("author", ""))
    year = entry.get("year", "")
    title = entry.get("title", "Untitled")

    # Truncate title to first 6 words max
    title_words = title.split()
    short_title = " ".join(title_words[:6])
    if len(title_words) > 6:
        short_title += "…"

    # Remove characters that are invalid in filenames
    raw = f"{author} {year} — {short_title}"
    safe = re.sub(r'[\\/:*?"<>|]', "", raw)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe + ".md"


# ---------------------------------------------------------------------------
# Keywords → Obsidian links
# ---------------------------------------------------------------------------

def keywords_to_links(keywords_raw: str) -> list[str]:
    """
    Split keyword string on commas or semicolons,
    return each keyword as an Obsidian [[link]].
    """
    if not keywords_raw:
        return []
    parts = re.split(r"[,;]", keywords_raw)
    links = []
    for p in parts:
        p = p.strip()
        if p:
            links.append(f"[[{p}]]")
    return links


# ---------------------------------------------------------------------------
# Markdown note builder
# ---------------------------------------------------------------------------

def entry_to_markdown(entry: dict) -> str:
    """Generate a full Markdown note from a parsed BibTeX entry."""
    title   = entry.get("title", "Untitled")
    authors = format_authors(entry.get("author", ""))
    year    = entry.get("year", "")
    journal = entry.get("journal", entry.get("booktitle", ""))
    doi     = entry.get("doi", "")
    volume  = entry.get("volume", "")
    number  = entry.get("number", "")
    pages   = entry.get("pages", "").replace("--", "–")
    abstract= entry.get("abstract", "")
    file_   = entry.get("file", "").strip()
    kw_links= keywords_to_links(entry.get("keywords", ""))

    # Build citation string
    citation_parts = []
    if journal:
        citation_parts.append(f"*{journal}*")
    if volume:
        vol_str = f"**{volume}**"
        if number:
            vol_str += f"({number})"
        citation_parts.append(vol_str)
    if pages:
        citation_parts.append(pages)
    citation = ", ".join(citation_parts)

    # YAML front matter
    yaml_keywords = "\n".join(f"  - {kw}" for kw in kw_links) if kw_links else "  - "
    pdf_field = f"[[Bibliography/PDFs/{file_}]]" if file_ else ""

    lines = []
    lines.append("---")
    lines.append(f"title: \"{title}\"")
    lines.append(f"authors: \"{authors}\"")
    lines.append(f"year: {year}")
    lines.append(f"journal: \"{journal}\"")
    lines.append(f"doi: \"{doi}\"")
    lines.append("tags:")
    lines.append(yaml_keywords)
    lines.append("project: ")
    lines.append("status: to read")
    lines.append("---")
    lines.append("")

    # Title heading: "Lastname YEAR — Short title"
    first_last = first_author_lastname(entry.get("author", ""))
    lines.append(f"# {first_last} {year} — {title}")
    lines.append("")
    lines.append(f"**Authors:** {authors}")
    lines.append(f"**Year:** {year}")
    if journal:
        lines.append(f"**Journal:** {journal}")
    if citation_parts:
        lines.append(f"**Citation:** {citation}")
    if doi:
        lines.append(f"**DOI:** [{doi}](https://doi.org/{doi})")
    if pdf_field:
        lines.append(f"**PDF:** {pdf_field}")
    lines.append(f"**Project:** [[Projects/]]")
    lines.append("")

    if kw_links:
        lines.append("**Keywords:** " + " · ".join(kw_links))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## In one sentence")
    lines.append("")
    lines.append("> ")
    lines.append("")

    if abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(f"> {abstract}")
        lines.append("")

    lines.append("## Key findings")
    lines.append("")
    lines.append("- ")
    lines.append("- ")
    lines.append("")
    lines.append("## Methods used")
    lines.append("")
    lines.append("- ")
    lines.append("")
    lines.append("## Relevance to my work")
    lines.append("")
    lines.append("> ")
    lines.append("")
    lines.append("## Critical reading")
    lines.append("")
    lines.append("**Strengths:**")
    lines.append("- ")
    lines.append("")
    lines.append("**Limitations:**")
    lines.append("- ")
    lines.append("")
    lines.append("## Links to other notes")
    lines.append("")
    lines.append("- Related papers: [[Bibliography/]]")
    lines.append("- Related experiment: [[Experiments/]]")
    lines.append("- Related project: [[Projects/]]")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a Zotero BibTeX export into Obsidian literature notes."
    )
    parser.add_argument(
        "bib_file",
        help="Path to your exported .bib file (e.g. my_library.bib)"
    )
    parser.add_argument(
        "output_dir",
        help="Path to your vault's Bibliography/ folder (e.g. ./vault/Bibliography/)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing notes (default: skip existing files)"
    )
    args = parser.parse_args()

    bib_path = Path(args.bib_file)
    out_dir  = Path(args.output_dir)

    if not bib_path.exists():
        print(f"❌  File not found: {bib_path}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"📖  Reading {bib_path} …")
    entries = parse_bib_file(str(bib_path))
    print(f"    Found {len(entries)} entries.\n")

    created = skipped = errors = 0

    for entry in entries:
        try:
            filename = make_filename(entry)
            out_path = out_dir / filename

            if out_path.exists() and not args.overwrite:
                print(f"  ⏭  Skipped (already exists): {filename}")
                skipped += 1
                continue

            content = entry_to_markdown(entry)
            out_path.write_text(content, encoding="utf-8")
            print(f"  ✅  Created: {filename}")
            created += 1

        except Exception as e:
            key = entry.get("_key", "?")
            print(f"  ❌  Error on entry '{key}': {e}")
            errors += 1

    print(f"\n🎉  Done — {created} created, {skipped} skipped, {errors} errors.")
    if skipped:
        print("     Run with --overwrite to replace existing notes.")


if __name__ == "__main__":
    main()
