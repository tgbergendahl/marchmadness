"""Simple PyQt5 GUI frontend for the bracket simulator."""
import sys
import os
from typing import List

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QFileDialog,
    QTextEdit,
)

from bracket import BracketSimulator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("March Madness Bracket Simulator")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.teams_path_label = QLabel("No teams file loaded")
        self.probs_path_label = QLabel("No probabilities file loaded")
        layout.addWidget(self.teams_path_label)
        layout.addWidget(self.probs_path_label)

        load_teams_btn = QPushButton("Load teams list")
        load_teams_btn.clicked.connect(self.load_teams)
        layout.addWidget(load_teams_btn)

        load_probs_btn = QPushButton("Load match-up probabilities")
        load_probs_btn.clicked.connect(self.load_probs)
        layout.addWidget(load_probs_btn)

        self.run_btn = QPushButton("Compute most likely bracket")
        self.run_btn.clicked.connect(self.run_simulation)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.teams: List[str] = []
        self.probs_file: str = ""

    def load_teams(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select teams file", "", "Text files (*.txt);;All files (*)")
        if path:
            with open(path) as f:
                self.teams = [line.strip() for line in f if line.strip()]
            self.teams_path_label.setText(f"Teams: {os.path.basename(path)} ({len(self.teams)})")
            self.check_ready()

    def load_probs(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select probabilities CSV", "", "CSV files (*.csv);;All files (*)")
        if path:
            self.probs_file = path
            self.probs_path_label.setText(f"Probabilities: {os.path.basename(path)}")
            self.check_ready()

    def check_ready(self):
        if self.teams and self.probs_file:
            self.run_btn.setEnabled(True)

    def run_simulation(self):
        try:
            sim = BracketSimulator.load_from_csv(self.teams, self.probs_file)
            champ, prob, struct = sim.most_likely_bracket()
            marginals = sim.probability_of_each_team()

            out = []
            out.append(f"Most likely champion: {champ} (p={prob:.4f})\n")
            out.append("Probabilities of each team winning:\n")
            for t, p in sorted(marginals.items(), key=lambda x: -x[1]):
                out.append(f"  {t}: {p:.4f}")

            out.append("\nPredicted bracket (most likely outcomes):")
            matches = BracketSimulator.structure_matches(struct, len(self.teams))
            for rnd, a, b, w in matches:
                out.append(f"  Round {rnd}: {a} vs {b} -> {w}")

            self.result_area.setText("\n".join(out))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
