# Lab Vault — Quick Guide

## Folders

```
Meetings/      one note per meeting
Daily/         one note per working day
Projects/      one note per research project
Protocols/     your experimental protocols
Experiments/   one note per experiment run
Results/       figures and graphical results
_Attachments/  images and files you embed in notes
_Templates/    templates — do not edit these directly
```

## Templates

| Template | When to use |
|----------|-------------|
| `Meeting` | Every meeting — with supervisor, lab, collaborators |
| `Daily` | Every working day |
| `Project` | Each new research project |
| `Protocol` | Each experimental protocol (one note = one protocol) |
| `Experiment` | Each time you run an experiment |
| `Results` | Each set of figures or results to track |

## How to name notes

| Folder | Format | Example |
|--------|--------|---------|
| Meetings & Daily | Weekday DD-MM-YYYY | `EXAMPLE Tuesday 13-05-2026` |
| Projects | Project name | `EXAMPLE Hypoxia response in HeLa cells` |
| Protocols | Technique · details | `EXAMPLE RNA extraction — TRIzol` |
| Experiments | What · date | `EXAMPLE Western blot HIF-1α — 13-05-2026` |
| Results | What · date | `EXAMPLE Western blot HIF-1α — 13-05-2026` |

## How everything connects

```
Project
 ├── Protocols used  →  [[Protocols/...]]
 ├── Experiments     →  [[Experiments/...]]
 ├── Results         →  [[Results/...]]
 └── Meetings        →  [[Meetings/...]]

Experiment  →  links to Protocol used + Results produced
Results     →  links back to Experiment + Project
Meeting     →  links to Project discussed
Daily       →  links to Experiments run + Project + Meeting
```

## The one habit to build

Whenever you create a note, fill in the **Project** link, then add a back-link in the project note. That's it — everything stays connected.

## Recommended plugins (free, installed from Obsidian settings)

- **Templater** — applies templates automatically when you create a note
- **Calendar** — sidebar calendar to navigate daily notes
- **Tasks** — shows all your `- [ ]` checkboxes across the vault in one view

→ See `README-Extended.md` for full setup instructions and a step-by-step walkthrough.
