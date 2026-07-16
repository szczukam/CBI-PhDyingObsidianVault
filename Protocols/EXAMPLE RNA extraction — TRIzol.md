---
date: 2026-03-15
version: v2
project: Hypoxia response in HeLa cells
validated: yes
---

# Protocol — RNA extraction · TRIzol

**Project:** [[Projects/Hypoxia response in HeLa cells]]
**Version:** v2
**Validated:** yes
**Last updated:** 2026-03-15

---

## Purpose

> Extract total RNA from cultured cells using TRIzol reagent for downstream RT-qPCR or RNA-seq.

---

## Materials & reagents

| Item | Quantity | Supplier / Reference |
|------|----------|----------------------|
| TRIzol reagent | 1 mL per well (6-well plate) | Thermo Fisher #15596026 |
| Chloroform | 200 µL per sample | Sigma |
| Isopropanol | 500 µL per sample | Sigma |
| 75% ethanol (in DEPC water) | 1 mL per sample | prepared in-house |
| DEPC-treated water | 30–50 µL per sample | prepared in-house |
| RNase-free tubes (1.5 mL) | 2 per sample | |

---

## Steps

1. Remove medium from cells, add 1 mL TRIzol directly to the well. Pipette up and down to lyse.
2. Transfer lysate to 1.5 mL tube. Incubate 5 min at RT.
3. Add 200 µL chloroform. Vortex 15 sec. Incubate 3 min at RT.
4. Centrifuge 12,000 × g, 15 min, 4 °C.
5. Transfer the upper aqueous phase (~400 µL) to a new tube — **do not touch the interphase**.
6. Add 500 µL isopropanol. Mix by inversion. Incubate 10 min at RT.
7. Centrifuge 12,000 × g, 10 min, 4 °C. Discard supernatant — RNA pellet may be invisible.
8. Wash pellet with 1 mL 75% ethanol. Centrifuge 7,500 × g, 5 min, 4 °C. Discard supernatant.
9. Air-dry pellet 5–10 min. Do not over-dry.
10. Resuspend in 30–50 µL DEPC-treated water. Incubate 10 min at 55 °C to dissolve.
11. Quantify by Nanodrop. Store at −80 °C.

---

## Critical steps & warnings

> ⚠️ Work on ice and in RNase-free conditions throughout.
> ⚠️ Step 5: taking any interphase will contaminate the RNA with DNA and protein.
> ⚠️ Step 9: over-drying the pellet makes it very hard to resuspend.

---

## Expected results

- 260/280 ratio between 1.9 and 2.1
- 260/230 ratio above 1.8
- Yield: ~1–5 µg per well of a 6-well plate (HeLa cells at 80% confluency)

---

## Troubleshooting

| Problem | Possible cause | Solution |
|---------|---------------|----------|
| Low 260/280 ratio | Protein contamination | Repeat chloroform step |
| Low 260/230 ratio | Salt or solvent contamination | Extra wash with 75% ethanol |
| No pellet visible | Low cell number | Normal — proceed anyway |
| Degraded RNA on gel | RNase contamination | Use fresh DEPC water, clean bench with RNaseZap |

---

## Notes & modifications

- v2: added 10 min incubation at step 6 — improved yield on low-cell-number samples.

---

## Experiments using this protocol

- [[Experiments/HeLa hypoxia treatment — 10-05-2026]]

---

## Version history

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-01-10 | Initial version |
| v2 | 2026-03-15 | Added isopropanol incubation step |
