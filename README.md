# Lab Vault — Complete Guide for Beginners

<p align="center"><img src="./_Attachments/README-visgraph.png" alt="Bibliography graph view example" width="760"></p><p align="center"><em>Bibliography graph view example</em</p>

> This guide assumes you have never used Obsidian or Markdown before. Read it once at the start and keep it as a reference.

---

## Table of contents

1. What is Obsidian?
2. What is Markdown?
3. Installing Obsidian and opening this vault
4. The vault structure — what goes where
5. Templates — what they are and how to use them
6. How to create a note step by step
7. How linking works — with a real example
8. How to embed images and figures
9. Recommended plugins and how to install them
10. Daily workflow suggestion
11. Bibliography management — importing from Zotero

---

## 1. What is Obsidian?

Obsidian is a free note-taking app that stores all your notes as simple text files on your computer (not in the cloud, not locked in a proprietary format — just `.md` files in a folder). You can open and edit them with any text editor, even without Obsidian.

The key idea is that notes can **link to each other**, just like web pages. Over time this creates a connected network of your research — you can jump from a meeting note to the experiment discussed, to the protocol used, to the results obtained, in just a few clicks.

---

## 2. What is Markdown?

Markdown is a simple way of formatting text using plain characters. Here are the ones you will actually use:

```
# Big title          (one hashtag = biggest heading)
## Section title     (two hashtags = section)
### Subsection       (three hashtags = subsection)

- Item in a list     (dash + space = bullet point)
- Another item

- [ ] Task to do     (dash + space + [ ] = checkbox, unticked)
- [x] Task done      (dash + space + [x] = checkbox, ticked)

**bold text**        (double asterisks = bold)
*italic text*        (single asterisks = italic)

[[Note name]]        (double square brackets = link to another note)
![[image.png]]       (exclamation + double brackets = embed an image)
```

That is essentially all you need. Obsidian will render these as formatted text as you type.

---

## 3. Installing Obsidian and opening this vault

1. Download Obsidian for free at **https://obsidian.md** and install it.
2. Unzip the folder you received (`Lab-Vault.zip`) somewhere on your computer — for example in your Documents folder.
3. Open Obsidian. Click **"Open folder as vault"**.
4. Select the unzipped `vault` folder.
5. Obsidian will open and you will see the folder structure on the left.

> ⚠️ Do not move individual files out of the vault folder — the links between notes will break.

---

## 4. The vault structure — what goes where

```
vault/
├── Meetings/       → one note per meeting
├── Daily/          → one note per working day
├── Projects/       → one note per research project
├── Protocols/      → your experimental protocols
├── Experiments/    → one note per experiment run
├── Results/        → figures and graphical results
├── _Attachments/   → images and files embedded in notes
├── _Templates/     → templates (do not edit these)
├── README.md       → quick reference guide
└── README-Extended.md  → this file
```

**Rule of thumb:** if you are not sure where a note belongs, ask yourself what you would look for first — the project, the date, or the technique. Then use the folder that matches that.

---

## 5. Templates — what they are and how to use them

A template is a pre-filled note with sections already set up for you. Instead of starting from a blank page every time, you just pick the right template and fill in the blanks.

The vault comes with 6 templates, stored in `_Templates/`:

| Template | Use for |
|----------|---------|
| `Meeting` | Every meeting |
| `Daily` | Every working day |
| `Project` | Each new research project |
| `Protocol` | Each experimental protocol |
| `Experiment` | Each time you run an experiment |
| `Results` | Each set of figures or results |

### How to use a template (once Templater is installed — see section 9)

1. Press `Ctrl+N` (Windows/Linux) or `Cmd+N` (Mac) to create a new note.
2. Obsidian will ask which template to use — pick the right one.
3. The note opens pre-filled. Just fill in the blanks.

> Until you install Templater, you can apply a template manually: open the template file, select all (`Ctrl+A`), copy (`Ctrl+C`), go to your new note, and paste (`Ctrl+V`).

---

## 6. How to create a note — step by step example

Let's say you just had a meeting with your supervisor on Tuesday 13 May 2026.

**Step 1.** Click on the `Meetings` folder in the left sidebar.

**Step 2.** Press `Ctrl+N` to create a new note. Name it: `Tuesday 13-05-2026`

**Step 3.** Apply the Meeting template (see above).

**Step 4.** Fill in the properties at the top:
```
date: 2026-05-13
people: Supervisor
project: Hypoxia response in HeLa cells
```

**Step 5.** Fill in the title line and the body sections.

**Step 6.** In the **Project** line, type `[[Projects/` — Obsidian will show you a list of your project notes. Select the right one and press Enter. This creates a clickable link.

**Step 7.** Open your project note (`Projects/EXAMPLE Hypoxia response in HeLa cells`) and add a link to this meeting under the **Meetings** section:
```
- [[Meetings/Tuesday 13-05-2026]]
```

Done. The meeting is now connected to the project and you can navigate between them with one click.

---

## 7. How linking works — with a real example

Links are written as `[[Note name]]`. When you click on them in Obsidian, they open the linked note.

Here is how a full chain of notes looks in this vault:

```
Project: Hypoxia response in HeLa cells
│
├── Protocol: [[Protocols/EXAMPLE RNA extraction — TRIzol]]
│
├── Experiment: [[Experiments/EXAMPLE Western blot HIF-1α — 13-05-2026]]
│       └── uses Protocol: [[Protocols/EXAMPLE Western Blot — standard]]
│       └── produced: [[Results/EXAMPLE Western blot HIF-1α — 13-05-2026]]
│
├── Results: [[Results/EXAMPLE Western blot HIF-1α — 13-05-2026]]
│       └── links back to Experiment + Project
│
└── Meeting: [[Meetings/EXAMPLE Tuesday 13-05-2026]]
        └── links to Project
```

And in your Daily note for that day:
```
- Experiments run: [[Experiments/EXAMPLE Western blot HIF-1α — 13-05-2026]]
- Meetings: [[Meetings/EXAMPLE Tuesday 13-05-2026]]
- Projects: [[Projects/EXAMPLE Hypoxia response in HeLa cells]]
```

This means you can always answer questions like:
- *What experiments did I run last Tuesday?* → open the Daily note
- *Which experiments used this protocol?* → open the Protocol note
- *What results came out of this experiment?* → open the Experiment note
- *Was this result discussed with my supervisor?* → check the Results note property `discussed: yes/no`

### The graph view

In Obsidian, go to **View → Open graph view**. You will see a visual map of all your notes and how they connect. It starts sparse — after a few weeks it becomes a genuine map of your research.

---

## 8. How to embed images and figures

To add a figure to a Results or Experiment note:

1. Drag and drop the image file into Obsidian (anywhere in the app window).
2. Obsidian will automatically save it in `_Attachments/` and insert the link for you.
3. The link looks like this: `![[_Attachments/your-figure.png]]`
4. The image will display inline in the note.

> Tip: name your image files clearly before dropping them in — for example `WB_HIF1a_13052026.png`. Once inside Obsidian, renaming files is fine but must be done from within Obsidian (right-click → Rename) so the links update automatically.

---

## 9. Recommended plugins and how to install them

Plugins are small add-ons that extend Obsidian. They are free and installed directly from inside the app.

**How to install any plugin:**
1. Open Obsidian Settings (gear icon, bottom left).
2. Go to **Community plugins**.
3. Click **Browse**, search for the plugin name, click **Install**, then **Enable**.

### Templater *(essential)*
Lets you apply a template when creating a new note, and fills in the date automatically.

After installing:
1. Go to Settings → Templater.
2. Set **Template folder location** to `_Templates`.
3. Enable **Trigger Templater on new file creation**.
4. Under **Folder templates**, assign each template to its folder:
   - `Meetings` → `_Templates/Meeting`
   - `Daily` → `_Templates/Daily`
   - `Projects` → `_Templates/Project`
   - `Protocols` → `_Templates/Protocol`
   - `Experiments` → `_Templates/Experiment`
   - `Results` → `_Templates/Results`

From now on, creating a new note inside a folder will automatically apply the right template.

### Task Genius *(recommended)*
Visual Lists, Kanban tables, Calendar, Progression Bars 

### Calendar
Adds a calendar to the right sidebar. Click any date to open (or create) the daily note for that day.
No extra configuration needed after enabling.


### Tasks
Lets you see all your `- [ ]` checkboxes from across the entire vault in one place.

After installing, you can create a note with this content to see all pending tasks:
````
```tasks
not done
```
````

---

## 10. Daily workflow suggestion

This is a suggestion — adapt it to what works for you.

### Morning (5 minutes)
1. Create today's Daily note (`Daily/Weekday DD-MM-YYYY`).
2. Write what you plan to do under **What I did** (fill it in as you go).
3. Check yesterday's **To do tomorrow** list.

### During the day
- When you start an experiment → create an Experiment note.
- When you have a meeting → create a Meeting note during or just after.
- When you get figures or results → create a Results note, embed the figures.
- Drop any quick thoughts or observations into the Daily note.

### End of day (5 minutes)
1. Fill in **To do tomorrow** in the Daily note.
2. Add links to the experiments and meetings of the day.
3. Update the relevant Project note if something important happened.

### When you write or update a protocol
- Create or update the Protocol note.
- Increment the version number (v1 → v2) and log the change in **Version history**.
- Link the protocol from any experiment that uses it.

---

## Quick reference card

| Action | Shortcut |
|--------|----------|
| New note | `Ctrl+N` / `Cmd+N` |
| Search all notes | `Ctrl+Shift+F` / `Cmd+Shift+F` |
| Open a link | Click on it (or `Ctrl+Click` to open in new pane) |
| Open graph view | `Ctrl+G` / `Cmd+G` |
| Toggle reading / editing mode | `Ctrl+E` / `Cmd+E` |
| Create a link while typing | Type `[[` then start typing the note name |

---

## 11. Bibliography management — importing from Zotero

### Overview

The `Bibliography/` folder stores one Markdown note per paper, generated automatically from your Zotero library. Each note contains all metadata (authors, year, journal, DOI, keywords as Obsidian `[[links]]`) plus empty sections for your own reading notes.

The script can also **download the PDF** for each paper and store it in `Bibliography/PDFs/`, then create a clickable link inside the note.

```
Bibliography/
├── Forsythe 1996 — HIF-1α essential for VEGF.md
├── Semenza 2001 — HIF-1 and human disease.md
└── PDFs/
    ├── Forsythe1996.pdf
    └── Semenza2001.pdf
```

---

### Step 1 — Install Better BibTeX in Zotero

Better BibTeX is a free Zotero plugin that exports your library as a clean `.bib` file.

1. Go to: **https://retorque.re/zotero-better-bibtex/installation/**
2. Download the `.xpi` file.
3. In Zotero: **Tools → Add-ons → gear icon → Install Add-on From File** → select the `.xpi`.
4. Restart Zotero.

---

### Step 2 — Export your Zotero library as BibTeX

1. In Zotero, select the collection you want (or your whole library).
2. Right-click → **Export Collection…**
3. Format: **Better BibTeX**
4. ✅ Check **"Keep updated"** — the file will refresh automatically when you add papers.
5. Save it somewhere easy to find, e.g. `~/Documents/my_library.bib`

> **Tip:** make sure your Zotero entries have **keywords** filled in — these become `[[links]]` in Obsidian and build your knowledge graph automatically.

---

### Step 3 — Check that Python is installed

Open a terminal and type:

```bash
python3 --version
```

You should see something like `Python 3.11.2`. If not:
- **Mac:** `brew install python3` or download from https://www.python.org
- **Windows:** download from https://www.python.org — tick **"Add Python to PATH"** during install
- **Linux:** `sudo apt install python3`

No external libraries are needed — the script uses only Python's built-in modules.

---

### Step 4 — Run the script

The script `zotero_to_obsidian.py` is in the vault root. Open a terminal, navigate to the vault folder, and run one of the following commands depending on what you want.

**Open a terminal in the vault folder:**
- Mac/Linux: `cd /path/to/your/vault`
- Windows: open PowerShell, then `cd C:\path\to\your\vault`

---

#### Option A — Notes only (PDF exported via Zotero and saved in ./Bibliography/PDFs)

```bash
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/
```

Creates one Markdown note per paper. No PDFs downloaded.

---

#### Option B — Notes + open-access PDFs (legal, via Unpaywall)

Unpaywall finds freely and legally available PDFs (preprints, PubMed Central, institutional repositories). Coverage is roughly 50% of recent papers.

```bash
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ \
    --pdf unpaywall --email you@institution.edu
```

Your email is sent to the Unpaywall API as identification (it is a public, free API — your email is not sold or spammed).

---

#### Option C — Notes + PDFs via Sci-Hub

Sci-Hub provides access to virtually any paper. Access may be restricted depending on your country or institution network.

```bash
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ --pdf scihub
```

> ⚠️ The legal status of Sci-Hub varies by country. Using it is your own responsibility.

---

#### Option D — Try Unpaywall first, fall back to Sci-Hub

```bash
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ \
    --pdf both --email you@institution.edu
```

This is the most effective option: gets as many PDFs as possible, legally where available.

---

#### Other useful options

```bash
# Skip note creation — only download missing PDFs for existing notes
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ \
    --pdf scihub --pdfs-only

# Slow down requests if a server is rate-limiting you (default is 2 seconds between requests)
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ \
    --pdf scihub --delay 5

# Overwrite existing notes (warning: your reading notes will be erased)
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ --overwrite
```

---

### What the output looks like

Example terminal output:

```
📖  Reading my_library.bib …
    Found 87 entries.

📥  PDF source: Unpaywall → Sci-Hub

  🔍  [Forsythe1996] Trying Unpaywall … not available
  🔍  [Forsythe1996] Trying Sci-Hub … found ✓
  ⬇️   [Forsythe1996] Downloading PDF … ✅  Forsythe1996.pdf (1823 KB)
  ✅  [Forsythe1996] Forsythe 1996 — Activation of vascular endothelial…

  🔍  [Semenza2001] Trying Unpaywall … found ✓
  ⬇️   [Semenza2001] Downloading PDF … ✅  Semenza2001.pdf (312 KB)
  ✅  [Semenza2001] Semenza 2001 — HIF-1, O2, and the 3 PHDs…
  ...

───────────────────────────────────────────────────────
  Notes  : 87 created, 0 skipped, 0 errors
  PDFs   : 71 downloaded, 0 already existed, 16 not found
───────────────────────────────────────────────────────
```

Each generated note includes:
- Full metadata as YAML properties
- Keywords from Zotero converted to `[[links]]` — these appear in the Obsidian graph
- A clickable DOI link
- A direct link to the PDF: `[[Bibliography/PDFs/Forsythe1996.pdf]]`
- Empty sections for your own notes: "In one sentence", "Key findings", "Relevance to my work", etc.

---

### Keeping your bibliography up to date

When you add new papers to Zotero, the `.bib` file updates automatically (if you checked "Keep updated"). Re-run the script — **existing notes are skipped by default**, so your reading notes are safe.

```bash
# Run again — only new papers get new notes; existing notes untouched
python3 zotero_to_obsidian.py ~/Documents/my_library.bib ./Bibliography/ --pdf both --email you@lab.edu
```

---

### Linking papers to experiments and projects

From any note in the vault, you can link to a paper:

```
- Based on: [[Bibliography/Forsythe 1996 — Activation of vascular endothelial…]]
- See also: [[Bibliography/Kaelin 2008 — Oxygen sensing by metazoans…]]
```

In your **Project** note, add a **Key papers** section and list the most relevant ones. Over time, Obsidian's graph view will show you which papers connect to which experiments, protocols, and projects.
*Last updated: July 2026*
