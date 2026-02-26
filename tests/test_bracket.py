import pytest

from bracket import BracketSimulator


def make_simple_teams(n):
    return [f"T{i}" for i in range(n)]


def make_uniform_probs(teams):
    # 50/50 for every matchup
    return {(a, b): 0.5 for a in teams for b in teams if a != b}


def test_dp_single_game():
    teams = ["A", "B"]
    probs = {("A", "B"): 0.7, ("B", "A"): 0.3}
    sim = BracketSimulator(teams, probs)
    champion, prob, struct = sim.most_likely_bracket()
    assert champion == "A"
    assert abs(prob - 0.7) < 1e-6


def test_4_team_bracket():
    teams = ["A", "B", "C", "D"]
    # A beats B / C beats D, then finals 60/40 between A and C
    probs = {
        ("A", "B"): 0.9,
        ("B", "A"): 0.1,
        ("C", "D"): 0.8,
        ("D", "C"): 0.2,
        ("A", "C"): 0.6,
        ("C", "A"): 0.4,
        ("A", "D"): 0.7,
        ("D", "A"): 0.3,
        ("B", "C"): 0.5,
        ("C", "B"): 0.5,
        ("B", "D"): 0.5,
        ("D", "B"): 0.5,
    }
    sim = BracketSimulator(teams, probs)
    champ, prob, struct = sim.most_likely_bracket()
    # the obvious most likely bracket is A beating B, C beating D,
    # then A beating C
    assert champ == "A"
    assert pytest.approx(prob, rel=1e-3) == 0.9 * 0.8 * 0.6


def test_marginals_sum_to_one():
    # verify a larger bracket still works and probabilities normalize
    teams = make_simple_teams(64)
    probs = make_uniform_probs(teams)
    sim = BracketSimulator(teams, probs)
    marginals = sim.probability_of_each_team()
    total = sum(marginals.values())
    assert pytest.approx(total, rel=1e-6) == 1.0


def test_invalid_team_count():
    # bracket size must be a power of two and >= 2
    with pytest.raises(ValueError):
        BracketSimulator(["A", "B", "C"], {})
    with pytest.raises(ValueError):
        BracketSimulator([], {})


def test_structure_matches():
    # build a small 4-team bracket with predictable probabilities
    teams = ["A", "B", "C", "D"]
    probs = {("A", "B"): 1.0, ("B", "A"): 0.0,
             ("C", "D"): 0.0, ("D", "C"): 1.0,
             ("A", "D"): 0.5, ("D", "A"): 0.5}
    sim = BracketSimulator(teams, probs)
    champ, _, struct = sim.most_likely_bracket()
    matches = BracketSimulator.structure_matches(struct, len(teams))
    # first-round matches are A vs B and C vs D
    first_round = [m for m in matches if m[0] == 1]
    assert set((m[1], m[2]) for m in first_round) == {("A", "B"), ("C", "D")}
    # final match should involve A (winner of left) and D (winner of right)
    final = next(m for m in matches if m[0] == 2)
    assert final[1:] == ("A", "D", champ)


def test_bracket_widget_and_images(tmp_path):
    # verify layout coordinates are computed and image loader works
    from main import BracketWidget, MainWindow
    from PyQt5 import QtWidgets, QtGui, QtCore

    app = QtWidgets.QApplication([])
    teams = ["A", "B", "C", "D"]
    probs = {("A", "B"): 0.6, ("B", "A"): 0.4,
             ("C", "D"): 0.7, ("D", "C"): 0.3,
             ("A", "C"): 0.5, ("C", "A"): 0.5,
             ("B", "D"): 0.5, ("D", "B"): 0.5}
    sim = BracketSimulator(teams, probs)
    _, _, struct = sim.most_likely_bracket()
    widget = BracketWidget()
    widget.set_structure(teams, struct, {})
    assert widget.depth == 2
    # ensure both leaves and root have coords
    for t in teams:
        assert t in widget.node_coords
    # leaves have distinct vertical positions; simple sanity check
    ys = [widget.node_coords[t][1] for t in teams]
    assert len(set(ys)) == len(teams)

    # test image loading helper
    w = MainWindow()
    w.teams = teams
    imgfile = tmp_path / "A.png"
    pix = QtGui.QPixmap(10, 10)
    pix.fill(QtCore.Qt.red)
    pix.save(str(imgfile))
    w._load_images_from_dir(str(tmp_path))
    assert "A" in w.images


def test_structure_matches():
    # build a small 4-team bracket with predictable probabilities
    teams = ["A", "B", "C", "D"]
    probs = {("A", "B"): 1.0, ("B", "A"): 0.0,
             ("C", "D"): 0.0, ("D", "C"): 1.0,
             ("A", "D"): 0.5, ("D", "A"): 0.5}
    sim = BracketSimulator(teams, probs)
    champ, _, struct = sim.most_likely_bracket()
    matches = BracketSimulator.structure_matches(struct, len(teams))
    # first-round matches are A vs B and C vs D
    first_round = [m for m in matches if m[0] == 1]
    assert set((m[1], m[2]) for m in first_round) == {("A", "B"), ("C", "D")}
    # final match should involve A (winner of left) and D (winner of right)
    final = next(m for m in matches if m[0] == 2)
    assert final[1:] == ("A", "D", champ)
