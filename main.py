"""Simple PyQt5 GUI frontend for the bracket simulator."""
import sys
import os
from typing import List, Dict, Tuple, Any

# on WSLg/Wayland systems Qt defaults to the xcb plugin which frequently
# fails even though other backends are available.  Force the wayland
# platform when we have a Wayland display in the environment so the GUI
# starts without the "could not load xcb" error.
if "WAYLAND_DISPLAY" in os.environ:
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QScrollArea,
    QDialog,
)

from bracket import BracketSimulator


class BracketWidget(QWidget):
    """Widget that renders a graphical bracket tree.

    The layout is computed from the nested ``structure`` produced by the
    simulator.  Team images may be supplied; if present they are drawn next
    to the team names.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.teams: List[str] = []
        self.structure: Any = None
        self.images: Dict[str, QtGui.QPixmap] = {}
        self.team_index: Dict[str, int] = {}
        self.node_coords: Dict[str, Tuple[float, float]] = {}
        self.lines: List[Tuple[str, str]] = []
        self.depth = 0
        self.h_spacing = 150
        self.v_spacing = 80

    def set_structure(self, teams: List[str], struct: Any, images: Dict[str, QtGui.QPixmap]):
        self.teams = teams
        self.structure = struct
        self.images = images
        # compute depth and reset layout state
        self.depth = self._compute_depth(struct)
        self.node_coords.clear()
        self.lines.clear()
        self.current_y = 50  # running vertical position for leaves
        self._layout(struct, 0)
        # width equal to number of rounds
        width = (self.depth + 1) * self.h_spacing + 200
        # height based on used vertical space instead of team count
        height = max(self.current_y + 50, 400)
        self.setMinimumSize(width, height)
        self.update()

    def _compute_depth(self, struct: Any) -> int:
        if struct is None or struct.get("left") is None:
            return 0
        return 1 + max(self._compute_depth(struct["left"]), self._compute_depth(struct["right"]))

    def _layout(self, struct: Any, round_num: int) -> float:
        # returns y coordinate for this node; performs in-order traversal
        if struct is None:
            return 0
        # leaf
        if struct.get("left") is None and struct.get("right") is None:
            y = self.current_y
            # leaf x-position: far left (round_num determines depth but leaves at 0)
            x = (self.depth - round_num) * self.h_spacing
            self.node_coords[struct["winner"]] = (x, y)
            self.current_y += self.v_spacing
            return y
        # internal node: layout children first
        y_l = self._layout(struct["left"], round_num + 1)
        y_r = self._layout(struct["right"], round_num + 1)
        y = (y_l + y_r) / 2
        x = (self.depth - round_num) * self.h_spacing
        self.node_coords[struct["winner"]] = (x, y)
        self.lines.append((struct["left"]["winner"], struct["winner"]))
        self.lines.append((struct["right"]["winner"], struct["winner"]))
        return y

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(QtCore.Qt.black)
        painter.setPen(pen)
        # draw connecting lines with right-angle elbow for clarity
        for a, b in self.lines:
            xa, ya = self.node_coords.get(a, (0, 0))
            xb, yb = self.node_coords.get(b, (0, 0))
            xa_i, ya_i = int(xa), int(ya)
            xb_i, yb_i = int(xb), int(yb)
            # ensure child is to left of parent
            if xa_i > xb_i:
                xa_i, xb_i = xb_i, xa_i
                ya_i, yb_i = yb_i, ya_i
            mid_x = (xa_i + xb_i) // 2
            painter.drawLine(xa_i + 40, ya_i, mid_x, ya_i)
            painter.drawLine(mid_x, ya_i, mid_x, yb_i)
            painter.drawLine(mid_x, yb_i, xb_i - 40, yb_i)
        # optionally draw round labels at top
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        for r in range(self.depth + 1):
            x_label = int(r * self.h_spacing)
            painter.drawText(x_label + 10, 20, f"R{r+1}")
        # draw nodes as boxes with optional images
        for team, (x, y) in self.node_coords.items():
            x_i, y_i = int(x), int(y)
            rect = QtCore.QRect(x_i, y_i - 10, 120, 20)
            painter.drawRect(rect)
            if team in self.images:
                pix = self.images[team]
                painter.drawPixmap(x_i, y_i - 20, 20, 20, pix)
                painter.drawText(x_i + 25, y_i + 5, team)
            else:
                painter.drawText(x_i + 5, y_i + 5, team)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # frameless so we can render our own title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(1920, 1080)

        title_bar = QWidget(self)
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(30)
        title_layout = QtWidgets.QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 0, 0)

        title_label = QLabel("March Madness Bracket Simulator")
        title_label.setStyleSheet("font-weight:bold; color: white;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self._min_btn = QPushButton("-")
        self._min_btn.setFixedSize(20, 20)
        self._min_btn.setStyleSheet("background-color: blue; color: white; border: none;")
        self._min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self._min_btn)

        self._close_btn = QPushButton("x")
        self._close_btn.setFixedSize(20, 20)
        self._close_btn.setStyleSheet("background-color: red; color: white; border: none;")
        self._close_btn.clicked.connect(self.close)
        title_layout.addWidget(self._close_btn)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title_bar)

        self.teams_path_label = QLabel("No teams file loaded")
        self.probs_path_label = QLabel("No probabilities file loaded")
        self.images_path_label = QLabel("No images loaded")
        layout.addWidget(self.teams_path_label)
        layout.addWidget(self.probs_path_label)
        layout.addWidget(self.images_path_label)

        load_teams_btn = QPushButton("Load teams list")
        load_teams_btn.clicked.connect(self.load_teams)
        layout.addWidget(load_teams_btn)

        load_probs_btn = QPushButton("Load match-up probabilities")
        load_probs_btn.clicked.connect(self.load_probs)
        layout.addWidget(load_probs_btn)

        load_images_btn = QPushButton("Load team images")
        load_images_btn.clicked.connect(self.load_images)
        layout.addWidget(load_images_btn)

        self.run_btn = QPushButton("Compute most likely bracket")
        self.run_btn.clicked.connect(self.run_simulation)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.teams: List[str] = []
        self.probs_file: str = ""
        self.images: Dict[str, QtGui.QPixmap] = {}
        self._drag_pos = None

    # dragging support
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # data/load helpers
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

    def _load_images_from_dir(self, path: str):
        """Load any image files matching team names from ``path``.

        This is factored out so it can be exercised by unit tests without
        invoking a file dialog.
        """
        self.images.clear()
        for fname in os.listdir(path):
            name, ext = os.path.splitext(fname)
            if name in self.teams:
                pix = QtGui.QPixmap(os.path.join(path, fname))
                if not pix.isNull():
                    self.images[name] = pix

    def load_images(self):
        path = QFileDialog.getExistingDirectory(self, "Select directory with team images")
        if not path:
            return
        self._load_images_from_dir(path)
        self.images_path_label.setText(f"Images: {os.path.basename(path)} ({len(self.images)})")

    def check_ready(self):
        if self.teams and self.probs_file:
            self.run_btn.setEnabled(True)

    def run_simulation(self):
        try:
            sim = BracketSimulator.load_from_csv(self.teams, self.probs_file)
            champ, prob, struct = sim.most_likely_bracket()
            marginals = sim.probability_of_each_team()

            out: List[str] = []
            out.append(f"Most likely champion: {champ} (p={prob:.4f})\n")
            out.append("Probabilities of each team winning:\n")
            for t, p in sorted(marginals.items(), key=lambda x: -x[1]):
                out.append(f"  {t}: {p:.4f}")

            out.append("\nPredicted bracket (most likely outcomes):")
            matches = BracketSimulator.structure_matches(struct, len(self.teams))
            for rnd, a, b, w in matches:
                out.append(f"  Round {rnd}: {a} vs {b} -> {w}")

            self.result_area.setText("\n".join(out))

            dlg = QDialog(self)
            dlg.setWindowTitle("Bracket visualization")
            scroll = QScrollArea(dlg)
            bracket_w = BracketWidget()
            bracket_w.set_structure(self.teams, struct, self.images)
            scroll.setWidget(bracket_w)
            scroll.setWidgetResizable(True)
            dlg_layout = QVBoxLayout(dlg)
            dlg_layout.addWidget(scroll)
            dlg.resize(800, 600)
            dlg.exec_()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
