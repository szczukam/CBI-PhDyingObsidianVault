"""
zotero_to_obsidian.py
---------------------
Converts a BibTeX file exported from Zotero into one Markdown note per paper
in your Obsidian vault's Bibliography/ folder.

Features:
  - One note per paper, named "Lastname YEAR — Short title.md"
  - Keywords from Zotero converted to Obsidian [[links]]
  - Asks whether to keep ALL keywords or only the 15 most frequent in the library
  - Detects PDFs already in Bibliography/PDFs/ (any Zotero naming style)
  - Optionally downloads missing PDFs via Unpaywall (legal) or Sci-Hub

Usage:
  python3 zotero_to_obsidian.py library.bib ./Bibliography/
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf unpaywall --email you@lab.edu
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf scihub
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf both --email you@lab.edu
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf scihub --pdfs-only
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --overwrite

Requirements: Python 3.8+  (no external libraries)
"""

import re, sys, os, ssl, json, time, argparse, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from collections import Counter


# ═══════════════════════════════════════════════════════════════════
# BibTeX parser
# ═══════════════════════════════════════════════════════════════════

def parse_bib_file(bib_path):
    with open(bib_path, "r", encoding="utf-8") as f:
        raw = f.read()
    entries = []
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.+?)\n\}", re.DOTALL)
    for m in pattern.finditer(raw):
        etype = m.group(1).lower()
        if etype in ("comment", "string", "preamble"):
            continue
        entry = {"_type": etype, "_key": m.group(2).strip()}
        fp = re.compile(
            r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"((?:[^\"]*)*)\")", re.DOTALL
        )
        for f in fp.finditer(m.group(3)):
            val = (f.group(2) if f.group(2) is not None else f.group(3)) or ""
            entry[f.group(1).lower()] = clean_latex(val.strip())
        entries.append(entry)
    return entries


def clean_latex(text):
    text = re.sub(r"\\(?:emph|textbf|textit|textrm|mathrm)\{([^}]*)\}", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    for src, dst in {
        "--": "–", "---": "—", "\\&": "&",
        "\\'e": "é", "\\'E": "É", '\\"o': "ö", '\\"u': "ü", '\\"a': "ä",
        "\\`e": "è", "\\^e": "ê", "\\~n": "ñ",
        "\\alpha": "α", "\\beta": "β", "\\gamma": "γ",
    }.items():
        text = text.replace(src, dst)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════
# Authors
# ═══════════════════════════════════════════════════════════════════

def format_authors(raw):
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
                fmt.append(f"{words[-1]} {''.join(w[0]+'.' for w in words[:-1])}")
            else:
                fmt.append(p)
    if len(fmt) > 3:
        return ", ".join(fmt[:3]) + " et al."
    return ", ".join(fmt)


def first_author_lastname(raw):
    if not raw:
        return "Unknown"
    first = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    words = first.split()
    return words[-1] if words else "Unknown"


# ═══════════════════════════════════════════════════════════════════
# Filenames
# ═══════════════════════════════════════════════════════════════════

def make_note_filename(entry):
    author = first_author_lastname(entry.get("author", ""))
    year   = entry.get("year", "")
    title  = entry.get("title", "Untitled")
    words  = title.split()
    short  = " ".join(words[:6]) + ("…" if len(words) > 6 else "")
    raw    = f"{author} {year} — {short}"
    safe   = re.sub(r'[\\/:*?"<>|]', "", raw)
    return re.sub(r"\s+", " ", safe).strip() + ".md"


def make_our_pdf_filename(entry):
    """Our canonical PDF name: LastnameYear.pdf"""
    last = re.sub(r"[^\w]", "", first_author_lastname(entry.get("author", "Unknown")))
    return f"{last}{entry.get('year', '')}.pdf"


# ═══════════════════════════════════════════════════════════════════
# Keywords
# ═══════════════════════════════════════════════════════════════════

def parse_keywords(raw):
    if not raw:
        return []
    return [p.strip() for p in re.split(r"[,;]", raw) if p.strip()]


def build_top_keywords(entries, n=15):
    """Return the set of the n most frequent keywords across all entries."""
    counter = Counter()
    for e in entries:
        counter.update(parse_keywords(e.get("keywords", "")))
    return {kw for kw, _ in counter.most_common(n)}


def ask_keyword_mode(entries):
    """
    Interactively ask the user whether to keep all keywords or top 15.
    Returns either 'all' or the set of top-15 keywords.
    """
    all_kw = Counter()
    for e in entries:
        all_kw.update(parse_keywords(e.get("keywords", "")))

    total_unique = len(all_kw)
    top15 = {kw for kw, _ in all_kw.most_common(15)}

    print()
    print("┌─────────────────────────────────────────────────────┐")
    print("│              Keyword / tag options                  │")
    print("├─────────────────────────────────────────────────────┤")
    print(f"│  Your library has {total_unique:>4} unique keywords.              │")
    print("│                                                     │")
    print("│  [all]  Keep every keyword — richest graph,         │")
    print("│         but many one-off tags.                      │")
    print("│                                                     │")
    print("│  [top]  Keep only the 15 most frequent keywords —   │")
    print("│         cleaner graph, focuses on your main topics. │")
    print("└─────────────────────────────────────────────────────┘")

    if total_unique <= 15:
        print(f"  (Your library has only {total_unique} unique keywords — 'all' and 'top' are equivalent.)")

    print()
    print("  Top 15 keywords in this library:")
    for kw, count in all_kw.most_common(15):
        print(f"    · {kw}  ({count} papers)")
    print()

    while True:
        answer = input("  Keep [all] keywords or [top] 15? Type 'all' or 'top': ").strip().lower()
        if answer in ("all", "top"):
            break
        print("  Please type 'all' or 'top'.")

    print()
    if answer == "top":
        print("  → Using top 15 keywords only.")
        return top15
    else:
        print("  → Using all keywords.")
        return "all"


def filter_keywords(raw, mode):
    """Return [[linked]] keyword list, filtered by mode ('all' or a set of allowed kws)."""
    kws = parse_keywords(raw)
    if mode != "all":
        kws = [k for k in kws if k in mode]
    return [f"[[{k}]]" for k in kws]


# ═══════════════════════════════════════════════════════════════════
# PDF matching — fuzzy, handles all Zotero naming styles
# ═══════════════════════════════════════════════════════════════════

def _norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def find_existing_pdf(entry, pdf_dir):
    """
    Look for a PDF already in pdf_dir that matches this entry.
    Handles all common Zotero export / ZotFile naming styles:
      - Forsythe1996.pdf                              (our own format)
      - Forsythe - 1996 - Title.pdf                   (Zotero built-in)
      - Forsythe_1996_Title.pdf                        (ZotFile)
      - Forsythe (1996) Title.pdf                      (ZotFile alt)
      - 10.1128-MCB.16.9.4604.pdf                      (DOI-based)
      - MCB.16.9.4604.pdf                              (publisher ref)

    Returns a Path object if found, or None.
    """
    if not pdf_dir.exists():
        return None

    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        return None

    lastname = _norm(first_author_lastname(entry.get("author", "")))
    year     = entry.get("year", "")
    doi      = entry.get("doi", "")

    # 1. Exact match on our canonical name
    our_name = make_our_pdf_filename(entry)
    for pdf in pdfs:
        if pdf.name == our_name:
            return pdf

    # 2. Filename contains both lastname AND year
    if lastname and year:
        for pdf in pdfs:
            n = _norm(pdf.stem)
            if lastname in n and year in n:
                return pdf

    # 3. DOI embedded in filename (e.g. 10.1128-MCB.16.9.4604.pdf)
    if doi:
        doi_parts = [p for p in _norm(doi.replace("/", " ").replace(".", " ")).split()
                     if len(p) > 3]
        for pdf in pdfs:
            n = _norm(pdf.stem)
            if doi_parts and sum(1 for p in doi_parts if p in n) >= min(2, len(doi_parts)):
                return pdf

    # 4. Lastname only — only if a single unambiguous match
    if lastname:
        matches = [pdf for pdf in pdfs if lastname in _norm(pdf.stem)]
        if len(matches) == 1:
            return matches[0]

    return None


# ═══════════════════════════════════════════════════════════════════
# PDF download — Unpaywall
# ═══════════════════════════════════════════════════════════════════

def fetch_unpaywall(doi, email, ctx):
    if not doi or not email:
        return None
    try:
        url = (f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='')}"
               f"?email={urllib.parse.quote(email)}")
        req = urllib.request.Request(url, headers={"User-Agent": "zotero-to-obsidian/2.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        loc = data.get("best_oa_location")
        if loc:
            return loc.get("url_for_pdf") or loc.get("url")
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════
# PDF download — Sci-Hub
# ═══════════════════════════════════════════════════════════════════

SCIHUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.ren",
]


def fetch_scihub_pdf_url(doi, ctx):
    if not doi:
        return None
    for mirror in SCIHUB_MIRRORS:
        try:
            page_url = f"{mirror}/{urllib.parse.quote(doi, safe='')}"
            req = urllib.request.Request(
                page_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; zotero-to-obsidian/2.0)",
                    "Accept": "text/html",
                },
            )
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            for pat in [
                r'<iframe[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']',
                r'<embed[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']',
                r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']',
                r'"download_url"\s*:\s*"([^"]+)"',
            ]:
                m = re.search(pat, html, re.IGNORECASE)
                if m:
                    url = m.group(1)
                    if url.startswith("//"):
                        url = "https:" + url
                    elif url.startswith("/"):
                        url = mirror + url
                    return url
        except Exception:
            continue
    return None


def download_pdf(pdf_url, dest_path, ctx):
    try:
        req = urllib.request.Request(
            pdf_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; zotero-to-obsidian/2.0)",
                "Accept": "application/pdf,*/*",
            },
        )
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read()
        if not content.startswith(b"%PDF"):
            return False
        dest_path.write_bytes(content)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════
# Markdown note builder
# ═══════════════════════════════════════════════════════════════════

def entry_to_markdown(entry, kw_links, pdf_filename=None):
    title    = entry.get("title", "Untitled")
    authors  = format_authors(entry.get("author", ""))
    year     = entry.get("year", "")
    journal  = entry.get("journal", entry.get("booktitle", ""))
    doi      = entry.get("doi", "")
    volume   = entry.get("volume", "")
    number   = entry.get("number", "")
    pages    = entry.get("pages", "").replace("--", "–")
    abstract = entry.get("abstract", "")

    cit = []
    if journal: cit.append(f"*{journal}*")
    if volume:  cit.append(f"**{volume}**" + (f"({number})" if number else ""))
    if pages:   cit.append(pages)

    pdf_link = f"[[Bibliography/PDFs/{pdf_filename}]]" if pdf_filename else "*(not downloaded)*"

    L = ["---",
         f'title: "{title}"',
         f'authors: "{authors}"',
         f"year: {year}",
         f'journal: "{journal}"',
         f'doi: "{doi}"',
         "keywords:",
         *([f"  - {k}" for k in kw_links] if kw_links else ["  - "]),
         "project: ",
         "status: to read",
         "---", ""]

    first_last = first_author_lastname(entry.get("author", ""))
    L += [f"# {first_last} {year} — {title}", "",
          f"**Authors:** {authors}",
          f"**Year:** {year}"]
    if journal:  L.append(f"**Journal:** {journal}")
    if cit:      L.append(f"**Citation:** {', '.join(cit)}")
    if doi:      L.append(f"**DOI:** [{doi}](https://doi.org/{doi})")
    L.append(f"**PDF:** {pdf_link}")
    L.append(f"**Project:** [[Projects/]]")
    L.append("")

    if kw_links:
        L.append("**Keywords:** " + " · ".join(kw_links))
        L.append("")

    L += ["---", "",
          "## In one sentence", "", "> ", ""]
    if abstract:
        L += ["## Abstract", "", f"> {abstract}", ""]
    L += ["## Key findings", "", "- ", "- ", "",
          "## Methods used", "", "- ", "",
          "## Relevance to my work", "", "> ", "",
          "## Critical reading", "",
          "**Strengths:**", "- ", "",
          "**Limitations:**", "- ", "",
          "## Links to other notes", "",
          "- Related papers: [[Bibliography/]]",
          "- Related experiment: [[Experiments/]]",
          "- Related project: [[Projects/]]", ""]
    return "\n".join(L)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Convert a Zotero BibTeX export into Obsidian literature notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 zotero_to_obsidian.py library.bib ./Bibliography/
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf unpaywall --email you@lab.edu
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf scihub
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf both --email you@lab.edu
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --pdf scihub --pdfs-only
  python3 zotero_to_obsidian.py library.bib ./Bibliography/ --overwrite
        """,
    )
    parser.add_argument("bib_file",   help="Path to your .bib file from Zotero")
    parser.add_argument("output_dir", help="Path to your vault's Bibliography/ folder")
    parser.add_argument("--pdf", choices=["unpaywall", "scihub", "both"], default=None,
                        help="PDF download source (default: no download, but links existing files)")
    parser.add_argument("--email", default="",
                        help="Your email — required for Unpaywall")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing notes (warning: erases your reading notes)")
    parser.add_argument("--pdfs-only", action="store_true",
                        help="Only download / link PDFs; do not create new notes")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between PDF download requests (default: 2.0)")
    args = parser.parse_args()

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
    pdf_dir.mkdir(parents=True, exist_ok=True)

    ctx = ssl.create_default_context()

    print(f"\n📖  Reading {bib_path} …")
    entries = parse_bib_file(str(bib_path))
    print(f"    Found {len(entries)} entries.")

    # ── Keyword mode question ────────────────────────────────────────
    kw_mode = ask_keyword_mode(entries)   # "all" or a set of top-15 kws

    # ── Pre-scan existing PDFs ───────────────────────────────────────
    existing_pdfs = list(pdf_dir.glob("*.pdf"))
    print(f"\n📂  Found {len(existing_pdfs)} PDF(s) already in {pdf_dir}")

    if args.pdf:
        label = {"unpaywall": "Unpaywall", "scihub": "Sci-Hub",
                 "both": "Unpaywall → Sci-Hub"}[args.pdf]
        print(f"📥  PDF download source: {label}")
        if "scihub" in (args.pdf or ""):
            print("    ⚠️  Sci-Hub may be blocked on institutional networks.")
    print()

    notes_created = notes_skipped = notes_errors = 0
    pdfs_linked   = pdfs_downloaded = pdfs_failed = pdfs_skipped_dl = 0

    for i, entry in enumerate(entries):
        key = entry.get("_key", "?")
        doi = entry.get("doi", "").strip()

        try:
            note_filename = make_note_filename(entry)
            note_path     = out_dir / note_filename
            our_pdf_name  = make_our_pdf_filename(entry)
            our_pdf_path  = pdf_dir / our_pdf_name

            kw_links = filter_keywords(entry.get("keywords", ""), kw_mode)

            # ── Step 1: find or download PDF ─────────────────────────
            matched_pdf = find_existing_pdf(entry, pdf_dir)

            if matched_pdf:
                # Rename to our canonical name if it differs
                if matched_pdf.name != our_pdf_name:
                    matched_pdf.rename(our_pdf_path)
                    print(f"  🔗  [{key}] Linked existing PDF: {matched_pdf.name} → {our_pdf_name}")
                else:
                    print(f"  🔗  [{key}] Linked existing PDF: {our_pdf_name}")
                pdf_to_link = our_pdf_name
                pdfs_linked += 1

            elif args.pdf and doi:
                # Try to download
                pdf_url = None

                if args.pdf in ("unpaywall", "both"):
                    print(f"  🔍  [{key}] Unpaywall …", end=" ", flush=True)
                    pdf_url = fetch_unpaywall(doi, args.email, ctx)
                    print("found ✓" if pdf_url else "not available")

                if not pdf_url and args.pdf in ("scihub", "both"):
                    print(f"  🔍  [{key}] Sci-Hub …", end=" ", flush=True)
                    pdf_url = fetch_scihub_pdf_url(doi, ctx)
                    print("found ✓" if pdf_url else "not found")

                if pdf_url:
                    print(f"  ⬇️   [{key}] Downloading …", end=" ", flush=True)
                    ok = download_pdf(pdf_url, our_pdf_path, ctx)
                    if ok:
                        size_kb = our_pdf_path.stat().st_size // 1024
                        print(f"✅  {our_pdf_name} ({size_kb} KB)")
                        pdf_to_link = our_pdf_name
                        pdfs_downloaded += 1
                    else:
                        print("❌  bad response")
                        pdf_to_link = None
                        pdfs_failed += 1
                else:
                    pdf_to_link = None
                    pdfs_failed += 1

                if i < len(entries) - 1:
                    time.sleep(args.delay)

            elif args.pdf and not doi:
                print(f"  ⚠️  [{key}] No DOI — cannot download PDF")
                pdf_to_link = None
                pdfs_failed += 1
            else:
                pdf_to_link = None

            # ── Step 2: create or update note ────────────────────────
            if args.pdfs_only:
                if note_path.exists() and pdf_to_link:
                    content = note_path.read_text(encoding="utf-8")
                    old = "**PDF:** *(not downloaded)*"
                    new = f"**PDF:** [[Bibliography/PDFs/{pdf_to_link}]]"
                    if old in content:
                        note_path.write_text(content.replace(old, new, 1), encoding="utf-8")
                        print(f"  ✏️   [{key}] PDF link updated in existing note")
                continue

            if note_path.exists() and not args.overwrite:
                # Patch PDF link if we just found/downloaded one
                if pdf_to_link:
                    content = note_path.read_text(encoding="utf-8")
                    old = "**PDF:** *(not downloaded)*"
                    new = f"**PDF:** [[Bibliography/PDFs/{pdf_to_link}]]"
                    if old in content:
                        note_path.write_text(content.replace(old, new, 1), encoding="utf-8")
                        print(f"  ✏️   [{key}] PDF link patched in existing note")
                    else:
                        print(f"  ⏭️   [{key}] Note exists — skipped")
                else:
                    print(f"  ⏭️   [{key}] Note exists — skipped")
                notes_skipped += 1
                continue

            content = entry_to_markdown(entry, kw_links, pdf_to_link)
            note_path.write_text(content, encoding="utf-8")
            print(f"  ✅  [{key}] {note_filename}")
            notes_created += 1

        except Exception as e:
            print(f"  ❌  [{key}] Error: {e}")
            notes_errors += 1

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'─'*57}")
    print(f"  Notes  : {notes_created} created, {notes_skipped} skipped, {notes_errors} errors")
    print(f"  PDFs   : {pdfs_linked} matched from folder, "
          f"{pdfs_downloaded} downloaded, {pdfs_failed} not found")
    print(f"{'─'*57}")

    if notes_skipped:
        print("\n  Tip: use --overwrite to replace existing notes.")
        print("       Warning: this erases your reading notes.")
    if pdfs_failed and args.pdf:
        if args.pdf == "unpaywall":
            print(f"\n  {pdfs_failed} PDFs not found on Unpaywall.")
            print("  Try --pdf both or --pdf scihub for more coverage.")
        elif args.pdf in ("scihub", "both"):
            print(f"\n  {pdfs_failed} PDFs could not be downloaded.")
            print("  Sci-Hub may be blocked on your network — try from home or a VPN.")


if __name__ == "__main__":
    main()
