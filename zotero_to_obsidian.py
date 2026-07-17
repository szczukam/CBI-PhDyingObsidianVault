#!/usr/bin/env python3
"""
zotero_to_obsidian.py
---------------------
Converts a BibTeX file exported from Zotero into one Markdown note per paper
in your Obsidian vault's Bibliography/ folder.

Optionally downloads PDF files into Bibliography/PDFs/ and links them in the note.

Two PDF sources (choose with --pdf):
  --pdf unpaywall   Legal open-access PDFs via Unpaywall API (requires --email)
  --pdf scihub      All papers via Sci-Hub mirrors (grey area — your responsibility)
  --pdf both        Tries Unpaywall first, falls back to Sci-Hub

Usage examples:
    # Notes only, no PDFs
    python3 zotero_to_obsidian.py my_library.bib ./Bibliography/

    # Notes + open-access PDFs from Unpaywall
    python3 zotero_to_obsidian.py my_library.bib ./Bibliography/ --pdf unpaywall --email you@institution.edu

    # Notes + PDFs from Sci-Hub
    python3 zotero_to_obsidian.py my_library.bib ./Bibliography/ --pdf scihub

    # Notes + PDFs, try Unpaywall first then Sci-Hub
    python3 zotero_to_obsidian.py my_library.bib ./Bibliography/ --pdf both --email you@institution.edu

    # Only download PDFs for existing notes (no new notes created)
    python3 zotero_to_obsidian.py my_library.bib ./Bibliography/ --pdf scihub --pdfs-only

    # Overwrite existing notes (warning: replaces your reading notes)
    python3 zotero_to_obsidian.py my_library.bib ./Bibliography/ --overwrite

Requirements: Python 3.8+  (no external libraries needed)
"""

import re
import sys
import os
import ssl
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path


# ---------------------------------------------------------------------------
# BibTeX parser (pure stdlib)
# ---------------------------------------------------------------------------

def parse_bib_file(bib_path: str) -> list:
    with open(bib_path, "r", encoding="utf-8") as f:
        raw = f.read()

    entries = []
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.+?)\n\}", re.DOTALL)

    for match in pattern.finditer(raw):
        entry_type = match.group(1).lower()
        if entry_type in ("comment", "string", "preamble"):
            continue
        cite_key = match.group(2).strip()
        body = match.group(3)

        entry = {"_type": entry_type, "_key": cite_key}

        field_pattern = re.compile(
            r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"((?:[^\"]*)*)\")",
            re.DOTALL,
        )
        for f in field_pattern.finditer(body):
            name = f.group(1).lower()
            val  = (f.group(2) if f.group(2) is not None else f.group(3)) or ""
            entry[name] = clean_latex(val.strip())

        entries.append(entry)

    return entries


def clean_latex(text: str) -> str:
    text = re.sub(r"\\(?:emph|textbf|textit|textrm|mathrm)\{([^}]*)\}", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    for latex, char in {
        "--": "–", "---": "—", "\\&": "&",
        "\\'e": "é", "\\'E": "É", '\\"o': "ö",
        '\\"u': "ü", '\\"a': "ä", "\\`e": "è",
        "\\^e": "ê", "\\~n": "ñ",
        "\\alpha": "α", "\\beta": "β", "\\gamma": "γ",
    }.items():
        text = text.replace(latex, char)
    return text.strip()


# ---------------------------------------------------------------------------
# Author formatting
# ---------------------------------------------------------------------------

def format_authors(raw: str) -> str:
    if not raw:
        return ""
    parts = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)
    fmt = []
    for p in parts:
        p = p.strip()
        if "," in p:
            last, first = p.split(",", 1)
            initials = "".join(w[0] + "." for w in first.split() if w)
            fmt.append(f"{last.strip()} {initials}")
        else:
            words = p.split()
            if len(words) >= 2:
                initials = "".join(w[0] + "." for w in words[:-1])
                fmt.append(f"{words[-1]} {initials}")
            else:
                fmt.append(p)
    if len(fmt) > 3:
        return ", ".join(fmt[:3]) + " et al."
    return ", ".join(fmt)


def first_author_lastname(raw: str) -> str:
    if not raw:
        return "Unknown"
    first = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    words = first.split()
    return words[-1] if words else "Unknown"


# ---------------------------------------------------------------------------
# Filenames
# ---------------------------------------------------------------------------

def make_note_filename(entry: dict) -> str:
    author = first_author_lastname(entry.get("author", ""))
    year   = entry.get("year", "")
    title  = entry.get("title", "Untitled")
    words  = title.split()
    short  = " ".join(words[:6]) + ("…" if len(words) > 6 else "")
    raw    = f"{author} {year} — {short}"
    safe   = re.sub(r'[\\/:*?"<>|]', "", raw)
    return re.sub(r"\s+", " ", safe).strip() + ".md"


def make_pdf_filename(entry: dict) -> str:
    """Lastname + Year, e.g. Forsythe1996.pdf"""
    last = re.sub(r"[^\w]", "", first_author_lastname(entry.get("author", "Unknown")))
    year = entry.get("year", "")
    return f"{last}{year}.pdf"


# ---------------------------------------------------------------------------
# Keywords → Obsidian links
# ---------------------------------------------------------------------------

def keywords_to_links(raw: str) -> list:
    if not raw:
        return []
    return [f"[[{p.strip()}]]" for p in re.split(r"[,;]", raw) if p.strip()]


# ---------------------------------------------------------------------------
# PDF download — Unpaywall
# ---------------------------------------------------------------------------

def fetch_unpaywall(doi: str, email: str, ctx) -> str | None:
    """
    Query Unpaywall API for an open-access PDF URL.
    Returns the URL string or None if not found / not open access.
    """
    if not doi or not email:
        return None
    try:
        url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='')}?email={urllib.parse.quote(email)}"
        req = urllib.request.Request(url, headers={"User-Agent": "zotero-to-obsidian/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        loc = data.get("best_oa_location")
        if loc:
            return loc.get("url_for_pdf") or loc.get("url")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# PDF download — Sci-Hub
# ---------------------------------------------------------------------------

SCIHUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.ren",
]


def fetch_scihub_pdf_url(doi: str, ctx) -> str | None:
    """
    Try each Sci-Hub mirror. Parses the HTML to extract the actual PDF URL.
    Returns a direct PDF URL or None.
    """
    if not doi:
        return None

    for mirror in SCIHUB_MIRRORS:
        try:
            page_url = f"{mirror}/{urllib.parse.quote(doi, safe='')}"
            req = urllib.request.Request(
                page_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; zotero-to-obsidian/1.0)",
                    "Accept": "text/html",
                },
            )
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Look for the embedded PDF location in the page
            # Sci-Hub typically has: <iframe src="//...pdf"> or location.href = "..."
            patterns = [
                r'<iframe[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']',
                r'<embed[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']',
                r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']',
                r'getElementById\(["\']pdf["\'][^>]*src=["\']([^"\']+)["\']',
                r'"download_url"\s*:\s*"([^"]+)"',
            ]
            for pat in patterns:
                m = re.search(pat, html, re.IGNORECASE)
                if m:
                    pdf_url = m.group(1)
                    # Fix protocol-relative URLs
                    if pdf_url.startswith("//"):
                        pdf_url = "https:" + pdf_url
                    elif pdf_url.startswith("/"):
                        pdf_url = mirror + pdf_url
                    return pdf_url

        except Exception:
            continue

    return None


# ---------------------------------------------------------------------------
# Download a PDF file to disk
# ---------------------------------------------------------------------------

def download_pdf(pdf_url: str, dest_path: Path, ctx) -> bool:
    """Download a PDF from url to dest_path. Returns True on success."""
    try:
        req = urllib.request.Request(
            pdf_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; zotero-to-obsidian/1.0)",
                "Accept": "application/pdf,*/*",
            },
        )
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read()

        # Sanity check: PDFs start with %PDF
        if not content.startswith(b"%PDF"):
            return False

        dest_path.write_bytes(content)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Markdown note builder
# ---------------------------------------------------------------------------

def entry_to_markdown(entry: dict, pdf_filename: str | None = None) -> str:
    title    = entry.get("title", "Untitled")
    authors  = format_authors(entry.get("author", ""))
    year     = entry.get("year", "")
    journal  = entry.get("journal", entry.get("booktitle", ""))
    doi      = entry.get("doi", "")
    volume   = entry.get("volume", "")
    number   = entry.get("number", "")
    pages    = entry.get("pages", "").replace("--", "–")
    abstract = entry.get("abstract", "")
    kw_links = keywords_to_links(entry.get("keywords", ""))

    # Citation string
    cit = []
    if journal:  cit.append(f"*{journal}*")
    if volume:
        vs = f"**{volume}**" + (f"({number})" if number else "")
        cit.append(vs)
    if pages:    cit.append(pages)

    kw_yaml = "\n".join(f"  - {k}" for k in kw_links) if kw_links else "  - "
    pdf_link = f"[[Bibliography/PDFs/{pdf_filename}]]" if pdf_filename else ""

    L = []
    # YAML front matter
    L += [
        "---",
        f'title: "{title}"',
        f'authors: "{authors}"',
        f"year: {year}",
        f'journal: "{journal}"',
        f'doi: "{doi}"',
        "tags:",
        kw_yaml,
        "project: ",
        "status: to read",
        "---", "",
    ]
    # Heading
    first_last = first_author_lastname(entry.get("author", ""))
    L.append(f"# {first_last} {year} — {title}")
    L.append("")
    L += [f"**Authors:** {authors}", f"**Year:** {year}"]
    if journal:  L.append(f"**Journal:** {journal}")
    if cit:      L.append(f"**Citation:** {', '.join(cit)}")
    if doi:      L.append(f"**DOI:** [{doi}](https://doi.org/{doi})")
    if pdf_link: L.append(f"**PDF:** {pdf_link}")
    else:        L.append(f"**PDF:** *(not downloaded)*")
    L.append(f"**Project:** [[Projects/]]")
    L.append("")
    if kw_links:
        L.append("**Keywords:** " + " · ".join(kw_links))
        L.append("")
    L += ["---", ""]
    L += ["## In one sentence", "", "> ", ""]
    if abstract:
        L += ["## Abstract", "", f"> {abstract}", ""]
    L += [
        "## Key findings", "", "- ", "- ", "",
        "## Methods used", "", "- ", "",
        "## Relevance to my work", "", "> ", "",
        "## Critical reading", "",
        "**Strengths:**", "- ", "",
        "**Limitations:**", "- ", "",
        "## Links to other notes", "",
        "- Related papers: [[Bibliography/]]",
        "- Related experiment: [[Experiments/]]",
        "- Related project: [[Projects/]]",
        "",
    ]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a Zotero BibTeX export into Obsidian literature notes, "
                    "with optional PDF download.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Notes only
  python3 zotero_to_obsidian.py library.bib ./Bibliography/

  # Notes + open-access PDFs (legal, via Unpaywall)
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf unpaywall --email you@lab.edu

  # Notes + PDFs via Sci-Hub
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf scihub

  # Try Unpaywall first, fall back to Sci-Hub
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf both --email you@lab.edu

  # Only download missing PDFs for already-existing notes
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf scihub --pdfs-only
        """,
    )
    parser.add_argument("bib_file",    help="Path to your .bib file exported from Zotero")
    parser.add_argument("output_dir",  help="Path to your vault's Bibliography/ folder")
    parser.add_argument(
        "--pdf",
        choices=["unpaywall", "scihub", "both"],
        default=None,
        help="PDF download source (default: no PDF download)",
    )
    parser.add_argument(
        "--email",
        default="",
        help="Your email address — required for Unpaywall API (not sent anywhere else)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing notes (default: skip — your reading notes are safe)",
    )
    parser.add_argument(
        "--pdfs-only",
        action="store_true",
        help="Only download PDFs for entries that already have a note; do not create new notes",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait between PDF requests (default: 2.0 — be polite to servers)",
    )
    args = parser.parse_args()

    # Validate
    if args.pdf in ("unpaywall", "both") and not args.email:
        print("❌  --email is required when using Unpaywall (e.g. --email you@lab.edu)")
        sys.exit(1)

    bib_path = Path(args.bib_file)
    out_dir  = Path(args.output_dir)
    pdf_dir  = out_dir / "PDFs"

    if not bib_path.exists():
        print(f"❌  File not found: {bib_path}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        pdf_dir.mkdir(parents=True, exist_ok=True)

    # SSL context (verify certs)
    ctx = ssl.create_default_context()

    print(f"📖  Reading {bib_path} …")
    entries = parse_bib_file(str(bib_path))
    print(f"    Found {len(entries)} entries.\n")

    if args.pdf:
        source_label = {"unpaywall": "Unpaywall", "scihub": "Sci-Hub", "both": "Unpaywall → Sci-Hub"}[args.pdf]
        print(f"📥  PDF source: {source_label}")
        if args.pdf == "scihub":
            print("    ⚠️  Sci-Hub access may be restricted depending on your country / institution network.\n")

    notes_created = notes_skipped = notes_errors = 0
    pdfs_downloaded = pdfs_failed = pdfs_skipped = 0

    for i, entry in enumerate(entries):
        key = entry.get("_key", "?")
        doi = entry.get("doi", "").strip()

        try:
            note_filename = make_note_filename(entry)
            note_path     = out_dir / note_filename
            pdf_filename  = make_pdf_filename(entry)
            pdf_path      = pdf_dir / pdf_filename

            # ── PDF download ──────────────────────────────────────────────
            pdf_downloaded = pdf_path.exists()  # already on disk
            if pdf_downloaded:
                pdf_skipped_reason = "already exists"

            if args.pdf and not pdf_downloaded:
                if not doi:
                    print(f"  ⚠️  [{key}] No DOI — cannot download PDF")
                    pdfs_failed += 1
                    pdf_filename = None
                else:
                    pdf_url = None

                    if args.pdf in ("unpaywall", "both"):
                        print(f"  🔍  [{key}] Trying Unpaywall …", end=" ", flush=True)
                        pdf_url = fetch_unpaywall(doi, args.email, ctx)
                        if pdf_url:
                            print("found ✓")
                        else:
                            print("not available")

                    if not pdf_url and args.pdf in ("scihub", "both"):
                        print(f"  🔍  [{key}] Trying Sci-Hub …", end=" ", flush=True)
                        pdf_url = fetch_scihub_pdf_url(doi, ctx)
                        if pdf_url:
                            print("found ✓")
                        else:
                            print("not found")

                    if pdf_url:
                        print(f"  ⬇️   [{key}] Downloading PDF …", end=" ", flush=True)
                        ok = download_pdf(pdf_url, pdf_path, ctx)
                        if ok:
                            size_kb = pdf_path.stat().st_size // 1024
                            print(f"✅  {pdf_filename} ({size_kb} KB)")
                            pdf_downloaded = True
                            pdfs_downloaded += 1
                        else:
                            print(f"❌  download failed (bad response)")
                            pdfs_failed += 1
                            pdf_filename = None
                    else:
                        pdfs_failed += 1
                        pdf_filename = None

                    # Be polite — don't hammer servers
                    if i < len(entries) - 1:
                        time.sleep(args.delay)

            elif pdf_downloaded and args.pdf:
                pdfs_skipped += 1
                # keep pdf_filename as-is (file exists)
            elif not args.pdf:
                # No PDF mode — only link if file already exists on disk
                pdf_filename = pdf_filename if pdf_path.exists() else None

            # ── Note creation ─────────────────────────────────────────────
            if args.pdfs_only:
                # Update existing note's PDF link if note exists and pdf was downloaded
                if note_path.exists() and pdf_downloaded and pdf_path.exists():
                    content = note_path.read_text(encoding="utf-8")
                    old = "**PDF:** *(not downloaded)*"
                    new = f"**PDF:** [[Bibliography/PDFs/{pdf_filename}]]"
                    if old in content:
                        note_path.write_text(content.replace(old, new, 1), encoding="utf-8")
                        print(f"  🔗  [{key}] Updated PDF link in existing note")
                continue

            if note_path.exists() and not args.overwrite:
                # If PDF was just downloaded, patch the link in the existing note
                if pdf_downloaded and pdf_path.exists():
                    content = note_path.read_text(encoding="utf-8")
                    old_link = "**PDF:** *(not downloaded)*"
                    new_link = f"**PDF:** [[Bibliography/PDFs/{pdf_filename}]]"
                    if old_link in content:
                        note_path.write_text(content.replace(old_link, new_link, 1), encoding="utf-8")
                        print(f"  🔗  [{key}] PDF link updated in existing note")
                    else:
                        print(f"  ⏭️   [{key}] Note exists — skipped")
                else:
                    print(f"  ⏭️   [{key}] Note exists — skipped")
                notes_skipped += 1
                continue

            # Write or overwrite note
            pdf_fn_for_note = pdf_filename if (pdf_path.exists() if pdf_filename else False) else None
            content = entry_to_markdown(entry, pdf_fn_for_note)
            note_path.write_text(content, encoding="utf-8")
            print(f"  ✅  [{key}] {note_filename}")
            notes_created += 1

        except Exception as e:
            print(f"  ❌  [{key}] Error: {e}")
            notes_errors += 1

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"  Notes  : {notes_created} created, {notes_skipped} skipped, {notes_errors} errors")
    if args.pdf:
        print(f"  PDFs   : {pdfs_downloaded} downloaded, {pdfs_skipped} already existed, {pdfs_failed} not found")
    print(f"{'─'*55}")

    if notes_skipped:
        print("\n  Tip: use --overwrite to replace existing notes (your reading notes will be lost).")
    if args.pdf and pdfs_failed:
        print(f"\n  {pdfs_failed} PDFs could not be found.")
        if args.pdf == "unpaywall":
            print("  Try --pdf both or --pdf scihub to reach more papers.")
        if args.pdf in ("scihub", "both"):
            print("  Sci-Hub may be blocked on your network — try from home or use a VPN.")


if __name__ == "__main__":
    main()
