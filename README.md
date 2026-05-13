# Metric Fasteners — Fusion 360 Parameter Script

A Fusion 360 script that inserts metric fastener clearance and fit dimensions
as **user parameters** into your active design.  Parameters cover hex nut
press/slip fits, square nut fits, bolt clearance holes, counterbore geometry,
countersink geometry, washer dimensions, and a derived chamfer value — all
sourced from a single CSV file so the data is easy to maintain independently
of the script.

These values are primarily used, when designing parts that are 3D Printed.

---

## Parameter Groups

| Size | Parameters inserted |
|------|-------------------|
| M3   | 15 |
| M4   | 15 |
| M5   | 15 |
| M6   | 15 |
| M8   | 15 |
| M10  | 15 |

Each group contains:

| Suffix | Description |
|--------|-------------|
| `NutPressFit` | Hex nut press-fit socket diameter |
| `NutSlipFit` | Hex nut slip-fit socket diameter |
| `NutThickness` | Hex nut height |
| `SquareNutPressFitWidth` | Square nut press-fit pocket width |
| `SquareNutSlipFitWidth` | Square nut slip-fit pocket width |
| `SquareNutSlipThickness` | Square nut pocket depth (slip) |
| `SquareNutVerticalSlipWidth` | Square nut vertical-drop pocket width |
| `BoltSlipFit` | Bolt clearance hole diameter |
| `CbDia` | Counterbore diameter |
| `CbDepth` | Counterbore depth |
| `CsDia` | Countersink diameter |
| `CsDepth` | Countersink depth |
| `WasherDia` | Washer outer diameter |
| `WasherThickness` | Washer thickness |
| `CsChamfer` | Countersink chamfer offset *(derived formula)* |

---

## Installation

1. Clone or download this repository.
2. In Fusion 360, open **Scripts and Add-ins** (`Shift+S`).
3. Under the **Scripts** tab, click the **+** icon next to *My Scripts*.
4. Browse to the cloned folder and select it.  
   Both `MetricFasteners.py` **and** `MetricFastenersV2.csv` must be in the
   same folder — Fusion copies the entire folder into your scripts directory.

---

## Usage

1. Open (or create) a Fusion 360 design.
2. Launch **Scripts and Add-ins** (`Shift+S`), select **MetricFasteners**, and
   click **Run**.
3. A dialog appears with a checkbox for each size group plus a **Select All**
   toggle at the top.
4. Check the sizes you want, then click **OK**.
5. A summary reports how many parameters were created, how many were skipped
   (already existed), and any errors.

Parameters that already exist in the design are **skipped**, so it is safe to
run the script multiple times or to add new sizes to an existing design.

---

## Customizing the Data

All values live in `MetricFastenersV2.csv`.  The file uses three columns:

```
Name,Unit,Expression
m3NutPressFit,mm,5.5
m3CsChamfer,mm,(m3CsDia - m3BoltSlipFit) / 2
```

- **Name** — the parameter name exactly as it will appear in Fusion.
- **Unit** — `mm` for all current entries.
- **Expression** — a numeric literal *or* a formula referencing other
  parameters.  Formulas must only reference parameters that appear earlier
  in the same size group (i.e., earlier rows in the file).

To add a new size (e.g. M12), add rows following the same `m12Xxx` naming
convention.  The script detects sizes automatically — no code changes needed.

---

## File Structure

```
MetricFasteners/
├── MetricFasteners.py       # Fusion 360 script
├── MetricFastenersV2.csv    # Parameter data
└── README.md                # This file
```

---

## Requirements

- Autodesk Fusion 360 (any recent version)
- An open design in Fusion 360 before running the script

No external Python packages are required.

---

## License

MIT — free to use, modify, and distribute.  Attribution appreciated but not
required.
