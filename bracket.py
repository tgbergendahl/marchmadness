"""Core logic for March Madness bracket simulation and inference.

We treat the tournament as a fixed 64-team single-elimination bracket.  The user
provides probability estimates for every possible matchup (A beats B), and the
simulator will compute:

* the most probable full-bracket resolution (maximum-likelihood bracket)
* the probability that each team wins the tournament
* Monte-Carlo simulation of many random brackets using the supplied
  probabilities

The dynamic programming routine in :func:`_dp` builds up maximum-likelihood
sub-brackets for every team across all subtrees of the bracket.
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any
import csv
import math

Team = str

PairwiseProbabilities = Dict[Tuple[Team, Team], float]


class BracketSimulator:
    def __init__(self, teams: List[Team], pairwise: PairwiseProbabilities):
        # support any single-elimination bracket size that is a power of two
        n = len(teams)
        if n < 2 or (n & (n - 1)) != 0:
            raise ValueError("Number of teams must be a power of two and at least 2")
        self.teams = teams
        self.pairwise = pairwise

    @classmethod
    def load_from_csv(cls, teams: List[Team], csv_path: str) -> "BracketSimulator":
        """Create a simulator by reading pairwise probabilities from a CSV file.

        The CSV is expected to have three columns::

            team_a,team_b,probability_a_wins

        Each row must appear only once; the lookup is symmetric (i.e. you only
        need to specify one of (A,B) or (B,A)).  Missing entries default to
        0.5.
        """
        pairwise: PairwiseProbabilities = {}
        with open(csv_path, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                a, b, p_str = row
                p = float(p_str)
                pairwise[(a, b)] = p
                pairwise[(b, a)] = 1 - p
        return cls(teams, pairwise)

    def _p(self, a: Team, b: Team) -> float:
        """Return probability that team a beats team b."""
        return self.pairwise.get((a, b), 0.5)

    def _dp(self, teams: List[Team]) -> Dict[Team, Tuple[float, Any]]:
        """Dynamic-program algorithm building best-subtrees.

        Returns a mapping from each team in ``teams`` to a tuple ``(prob,
        structure)`` where ``prob`` is the probability of the most-likely set of
        game outcomes in this subtree that leads to that team winning the subtree.
        ``structure`` is a nested dictionary describing the winners of every
        match within the subtree and can be flattened for output.
        """
        if len(teams) == 1:
            # leaf node stores its own winner
            return {teams[0]: (1.0, {"winner": teams[0], "left": None, "right": None})}

        half = len(teams) // 2
        left = self._dp(teams[:half])
        right = self._dp(teams[half:])

        result: Dict[Team, Tuple[float, Any]] = {}
        for a, (pa, struct_a) in left.items():
            for b, (pb, struct_b) in right.items():
                # probability of each advancing and winning the final
                p_a_wins = self._p(a, b)
                prob_a = pa * pb * p_a_wins
                prob_b = pa * pb * (1 - p_a_wins)

                # if this matchup produces a better best-bracket for 'a',
                # record it
                if prob_a > result.get(a, (0.0, None))[0]:
                    result[a] = (
                        prob_a,
                        {"winner": a, "left": struct_a, "right": struct_b},
                    )
                if prob_b > result.get(b, (0.0, None))[0]:
                    result[b] = (
                        prob_b,
                        {"winner": b, "left": struct_a, "right": struct_b},
                    )
        return result

    def most_likely_bracket(self) -> Tuple[Team, float, Any]:
        """Return the champion, its probability, and the full bracket structure.

        ``bracket`` is a nested dictionary; use :func:`flatten_structure` to
        convert it to a list of match results.
        """
        dp_result = self._dp(self.teams)
        champ, (prob, structure) = max(dp_result.items(), key=lambda kv: kv[1][0])
        return champ, prob, structure

    def probability_of_each_team(self) -> Dict[Team, float]:
        """Compute the marginal probability that each team wins the tournament.

        Unlike :meth:`most_likely_bracket`, which builds a *maximum-likelihood*
        bracket, this method returns the actual probability of each team
        emerging from the entire bracket.  It therefore sums over all possible
        ways the team can reach the end.
        """
        return self._marginals_dp(self.teams)

    def _marginals_dp(self, teams: List[Team]) -> Dict[Team, float]:
        """Recursive computation of true win probabilities for each team.

        The returned dictionary maps every team present in ``teams`` to the
        probability that it wins the subtree.  This routine simply convolves
        the distributions of the left and right halves using the pairwise
        win-probabilities.
        """
        if len(teams) == 1:
            return {teams[0]: 1.0}
        half = len(teams) // 2
        left = self._marginals_dp(teams[:half])
        right = self._marginals_dp(teams[half:])
        dist: Dict[Team, float] = {}
        for a, pa in left.items():
            for b, pb in right.items():
                p_a_wins = self._p(a, b)
                dist[a] = dist.get(a, 0.0) + pa * pb * p_a_wins
                dist[b] = dist.get(b, 0.0) + pa * pb * (1 - p_a_wins)
        return dist

    @staticmethod
    def flatten_structure(struct: Any, prefix: List[str] = None) -> List[Tuple[int, Team]]:
        """Flatten the nested "structure" returned by ``_dp``.

        Returns a list of tuples ``(round_number, winner)`` ordered from the
        earliest rounds to the championship.  Round numbers start at 1 for the
        first set of games in the subtree.
        """
        if prefix is None:
            prefix = []
        if struct is None:
            return []
        res: List[Tuple[int, Team]] = []
        # recursively flatten left and right
        res.extend(BracketSimulator.flatten_structure(struct["left"], prefix))
        res.extend(BracketSimulator.flatten_structure(struct["right"], prefix))
        res.append((len(prefix) + 1, struct["winner"]))
        return res

    @staticmethod
    def structure_matches(struct: Any, size: int) -> List[Tuple[int, Team, Team, Team]]:
        """Return a list of explicit matches from the DP structure.

        Each entry is ``(round, team_left, team_right, winner)``.  The ``size``
        argument should be the number of teams in the subtree represented by
        ``struct``; it is used to compute the round number as ``log2(size)``.
        """
        if struct is None or size <= 1:
            return []
        half = size // 2
        matches: List[Tuple[int, Team, Team, Team]] = []
        matches.extend(BracketSimulator.structure_matches(struct["left"], half))
        matches.extend(BracketSimulator.structure_matches(struct["right"], half))
        left_w = struct["left"]["winner"]
        right_w = struct["right"]["winner"]
        round_num = int(math.log2(size))
        matches.append((round_num, left_w, right_w, struct["winner"]))
        return matches


# A simple CLI demonstration when run as a script.
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze a 64-team bracket.")
    parser.add_argument("--teams", help="path to newline-separated team list", required=True)
    parser.add_argument("--probs", help="CSV with pairwise probabilities", required=True)
    args = parser.parse_args()

    with open(args.teams) as f:
        tm = [line.strip() for line in f if line.strip()]

    sim = BracketSimulator.load_from_csv(tm, args.probs)
    champ, prob, struct = sim.most_likely_bracket()
    print(f"Most likely champion: {champ} (p={prob:.4f})")
    print("Probability each team wins:")
    for t, p in sorted(sim.probability_of_each_team().items(), key=lambda x: -x[1]):
        print(f"  {t}: {p:.4f}")
    print("\nPredicted match results:")
    matches = BracketSimulator.structure_matches(struct, len(tm))
    for rnd, a, b, w in matches:
        print(f"Round {rnd}: {a} vs {b} -> {w}")
