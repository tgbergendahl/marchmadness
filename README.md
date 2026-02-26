# March Madness Bracket Simulator

This project provides a simple GUI application for simulating a 64-team
"March Madness"-style single-elimination tournament, based on user-supplied
percent-chance estimates for each possible matchup.

## Features

* Load a list of 64 team names from a text file (one per line).
* Load pairwise matchup probabilities from a CSV file (`team_a,team_b,prob`).
* Compute the most likely full bracket resolution using dynamic programming.
* Display the marginal probability that each team wins the tournament.
* Show the predicted winner of every matchup (round-by-round) based on the
  input probabilities.
* Display a graphical bracket drawing with optional team images loaded from a
  directory. Images should be named to match the team (e.g. `Duke.png`).  The
  visualization now mirrors the familiar March Madness layout: first‑round
  teams are on the left, rounds progress to the right, and round numbers are
  shown at the top.  Matches are drawn with right‑angle connectors and boxes
  around team names for clarity.

## Getting Started

Example input files are provided under the `examples/` directory; you can
run the CLI or GUI against those to see how the system behaves.


### Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **WSL users:** if you use WSLg the GUI should appear automatically.  On
> older WSL installations you may need to run an X server (VcXsrv/Xming) and
> set `DISPLAY`/`WAYLAND_DISPLAY` appropriately.  The code now detects a
> Wayland display and forces `QT_QPA_PLATFORM=wayland` to avoid the common
> "could not load xcb" error.

> The GUI is built with PyQt5; you can also install `PyQt6` and adjust the
> imports if preferred.

### Running

```bash
python main.py
```

Use the buttons to load your teams file, probability CSV, and (optionally)
a directory of images. Each image file must be named for a team (e.g.
`Michigan.png`). After clicking "Compute most likely bracket" you'll get a
text summary and a separate window showing the full bracket graphic; loaded
images appear beside their teams.  The GUI features a custom title bar with
classic red “×” and blue “–” controls in the top‑right corner; you can also
use your window manager’s normal minimize/close decorations if preferred.

### CSV format

Each row should contain a matchup probability for two teams, for example:

```
Duke,Kentucky,0.65
Kansas,Gonzaga,0.48
```

Entries are treated symmetrically; you only need to list each pairing once.

### CLI Usage

The core computation can also be invoked from the command line:

```bash
python bracket.py --teams teams.txt --probs probs.csv
```

## Testing

There's a simple unit test ensuring the dynamic programming logic functions
correctly. Run it with `pytest` from the repository root:

```bash
pip install pytest
pytest
```
