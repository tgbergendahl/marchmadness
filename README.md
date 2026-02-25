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

## Getting Started

Example input files are provided under the `examples/` directory; you can
run the CLI or GUI against those to see how the system behaves.


### Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> The GUI is built with PyQt5; you can also install `PyQt6` and adjust the
> imports if preferred.

### Running

```bash
python main.py
```

Use the buttons to load your teams file and probability CSV, then click
"Compute most likely bracket".

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
