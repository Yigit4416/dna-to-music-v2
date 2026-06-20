from __future__ import annotations

import unittest
import torch
from unittest.mock import MagicMock

from dna_sonifier.rl import RewardEvaluator, run_reinforce_training
from dna_sonifier.tokenizer import DNATokenizer, MIDITokenizer
from dna_sonifier.model import Seq2SeqTransformer
from dna_sonifier.dataset import DNAtoMIDIDataset


class TestRLRewardEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = RewardEvaluator()
        self.dna_tokenizer = DNATokenizer()
        self.midi_tokenizer = MIDITokenizer()

    def test_scale_alignment_reward(self) -> None:
        # A simple DNA sequence that maps to C Major or another scale
        dna = "ATGCGATCGATCGATC"
        
        # Test C Major pitches: C4 (60), E4 (64), G4 (67)
        tokens_in_scale = ["NOTE_ON_60", "DURATION_1.0", "VELOCITY_80", "TIME_SHIFT_1.0",
                           "NOTE_ON_64", "DURATION_1.0", "VELOCITY_80", "TIME_SHIFT_1.0",
                           "NOTE_ON_67", "DURATION_1.0", "VELOCITY_80"]
        reward_in_scale = self.evaluator.evaluate(dna, tokens_in_scale)
        
        # Test out-of-scale pitches: F#4 (66), G#4 (68), A#4 (70)
        tokens_out_scale = ["NOTE_ON_66", "DURATION_1.0", "VELOCITY_80", "TIME_SHIFT_1.0",
                            "NOTE_ON_68", "DURATION_1.0", "VELOCITY_80", "TIME_SHIFT_1.0",
                            "NOTE_ON_70", "DURATION_1.0", "VELOCITY_80"]
        reward_out_scale = self.evaluator.evaluate(dna, tokens_out_scale)
        
        self.assertGreater(reward_in_scale, reward_out_scale, "Scale matching tokens should yield a higher reward than out-of-scale tokens.")

    def test_aaa_repetition_penalty(self) -> None:
        dna = "ATGCGATCGATCGATC"
        
        # 3 consecutive repeats of Note C4 (60)
        tokens_repeat = ["NOTE_ON_60", "NOTE_ON_60", "NOTE_ON_60", "TIME_SHIFT_1.0"]
        reward_repeat = self.evaluator.evaluate(dna, tokens_repeat)
        
        # Alternating notes
        tokens_no_repeat = ["NOTE_ON_60", "NOTE_ON_62", "NOTE_ON_60", "TIME_SHIFT_1.0"]
        reward_no_repeat = self.evaluator.evaluate(dna, tokens_no_repeat)
        
        self.assertGreater(reward_no_repeat, reward_repeat, "Repeated notes should trigger the AAA repetition penalty and yield a lower reward.")

    def test_rhythm_time_shifts_reward(self) -> None:
        dna = "ATGCGATCGATCGATC"
        
        # Healthy ratio of time shifts (approx 15-35% of events). We have 6 note events and 2 time shifts (total = 8, ratio = 25%)
        tokens_healthy = [
            "NOTE_ON_60", "NOTE_ON_64", "NOTE_ON_67", "TIME_SHIFT_1.0",
            "NOTE_ON_62", "NOTE_ON_66", "NOTE_ON_69", "TIME_SHIFT_1.0"
        ]
        reward_healthy = self.evaluator.evaluate(dna, tokens_healthy)
        
        # No time shifts at all (0%)
        tokens_no_shift = ["NOTE_ON_60", "NOTE_ON_62", "NOTE_ON_64", "NOTE_ON_66", "NOTE_ON_68"]
        reward_no_shift = self.evaluator.evaluate(dna, tokens_no_shift)
        
        self.assertGreater(reward_healthy, reward_no_shift, "Healthy time shifts should yield a higher reward than 0 shifts (distorted clangs).")


class TestRLTrainingLoop(unittest.TestCase):
    def test_rl_training_one_step(self) -> None:
        # Create a tiny mock model and dataset to check that run_reinforce_training executes without errors
        model = Seq2SeqTransformer(
            dna_vocab_size=9,
            midi_vocab_size=164,
            d_model=32,
            nhead=2,
            num_encoder_layers=1,
            num_decoder_layers=1,
            dim_feedforward=64,
            max_seq_len=2048,  # Match model specs
        )
        
        # Create a mock dataset returning a single parallel pair
        class MockDataset(torch.utils.data.Dataset):
            def __len__(self) -> int:
                return 1
            def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
                # Return DNA sequence tokens, target input, target output
                # The DNA sequence tokens must map to letters A/C/G/T/N under tokenizer.decode
                # Let's see: DNATokenizer uses: 0: pad, 1: bos, 2: eos, 3: unk, 4: A, 5: C, 6: G, 7: T, 8: N
                # So indices 4-8 are valid bases. Let's return valid DNA base token IDs.
                src = torch.tensor([1, 4, 5, 6, 7, 8, 2], dtype=torch.long)
                tgt_in = torch.randint(4, 160, (20,))
                tgt_out = torch.randint(4, 160, (20,))
                return src, tgt_in, tgt_out

        dataset = MockDataset()
        
        # Run REINFORCE training for 1 epoch
        epoch_rewards = run_reinforce_training(
            model=model,
            dataset=dataset,
            epochs=1,
            lr=1e-5,
            device="cpu",
            checkpoint_path=None,
        )
        
        self.assertEqual(len(epoch_rewards), 1)
        self.assertGreaterEqual(epoch_rewards[0], 0.0)
        self.assertLessEqual(epoch_rewards[0], 1.0)


if __name__ == "__main__":
    unittest.main()
