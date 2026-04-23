from __future__ import annotations

import unittest

from dna_sonifier.sonifier import SonificationConfig, energy_score, normalize_sequence, sonify_sequence


class SonifierTests(unittest.TestCase):
    def test_normalize_sequence_replaces_ambiguous_bases(self) -> None:
        self.assertEqual(normalize_sequence("acgtNryk"), "ACGTNNNN")

    def test_energy_score_is_normalized(self) -> None:
        value = energy_score("ACGT" * 50)
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_sonification_is_deterministic(self) -> None:
        sequence = "ACGTGCAATGCC" * 400
        config = SonificationConfig(duration_seconds=120)

        _, left = sonify_sequence(sequence, config, source_label="test")
        _, right = sonify_sequence(sequence, config, source_label="test")

        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
