from __future__ import annotations

import unittest
import torch
import music21

from dna_sonifier.tokenizer import DNATokenizer, MIDITokenizer
from dna_sonifier.model import Seq2SeqTransformer
from dna_sonifier.dataset import collate_pretrain, collate_seq2seq


class TestAITokenizers(unittest.TestCase):
    def setUp(self) -> None:
        self.dna_tokenizer = DNATokenizer()
        self.midi_tokenizer = MIDITokenizer()

    def test_dna_tokenizer_encodes_and_decodes(self) -> None:
        sequence = "ACGTNRYK"
        encoded = self.dna_tokenizer.encode(sequence, add_special_tokens=True)
        
        # Checking BOS, EOS, and special mapping
        self.assertEqual(encoded[0], self.dna_tokenizer.bos_id)
        self.assertEqual(encoded[-1], self.dna_tokenizer.eos_id)
        self.assertEqual(len(encoded), len(sequence) + 2)
        
        decoded = self.dna_tokenizer.decode(encoded, skip_special_tokens=True)
        # R, Y, K should map to N during normalization in sonification, or we tokenize non-bases as unk/N.
        # Let's verify character output
        self.assertEqual(decoded[:4], "ACGT")

    def test_midi_tokenizer_vocabulary(self) -> None:
        # Check that special tokens, Note-ons, velocities, durations, and shifts are all populated
        self.assertGreater(self.midi_tokenizer.vocab_size, 160)
        self.assertEqual(self.midi_tokenizer.pad_id, 0)
        self.assertEqual(self.midi_tokenizer.bos_id, 1)

    def test_midi_encoding_decoding_roundtrip(self) -> None:
        # Create a music21 stream with a simple note
        score = music21.stream.Score()
        part = music21.stream.Part()
        n = music21.note.Note("C4")
        n.quarterLength = 1.0
        n.volume.velocity = 80
        part.insert(0.0, n)
        
        n2 = music21.note.Note("E4")
        n2.quarterLength = 2.0
        n2.volume.velocity = 96
        part.insert(1.0, n2)
        
        score.insert(0, part)
        
        tokens = self.midi_tokenizer.encode_midi(score)
        self.assertGreater(len(tokens), 0)
        
        # Check first event is note C4 (midi 60)
        self.assertIn("NOTE_ON_60", tokens)
        self.assertIn("DURATION_1.0", tokens)
        self.assertIn("VELOCITY_80", tokens)
        
        # Check second event is note E4 (midi 64) after time shift
        self.assertIn("TIME_SHIFT_1.0", tokens)
        self.assertIn("NOTE_ON_64", tokens)
        self.assertIn("DURATION_2.0", tokens)
        self.assertIn("VELOCITY_96", tokens)
        
        # Decode back to score
        reconstructed = self.midi_tokenizer.decode_tokens(tokens)
        reconstructed_flat = reconstructed.flatten()
        notes = [el for el in reconstructed_flat if isinstance(el, music21.note.Note)]
        
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].pitch.midi, 60)
        self.assertEqual(notes[1].pitch.midi, 64)


class TestSeq2SeqModel(unittest.TestCase):
    def setUp(self) -> None:
        self.midi_tokenizer = MIDITokenizer()
        self.model = Seq2SeqTransformer(
            dna_vocab_size=9,
            midi_vocab_size=164,
            d_model=64,
            nhead=2,
            num_encoder_layers=1,
            num_decoder_layers=1,
            dim_feedforward=128,
            max_seq_len=64,
        )

    def test_model_pretraining_forward_shape(self) -> None:
        # Pretraining: batch_size=2, seq_len=10, src=None
        tgt = torch.randint(1, 160, (2, 10))
        logits = self.model(src=None, tgt=tgt)
        
        self.assertEqual(logits.shape, (2, 10, 164))

    def test_model_seq2seq_forward_shape(self) -> None:
        # Seq2Seq: batch_size=2, src_seq_len=15, tgt_seq_len=10
        src = torch.randint(1, 8, (2, 15))
        tgt = torch.randint(1, 160, (2, 10))
        
        src_padding_mask = src == 0
        tgt_padding_mask = tgt == 0
        
        logits = self.model(
            src=src,
            tgt=tgt,
            src_padding_mask=src_padding_mask,
            tgt_padding_mask=tgt_padding_mask,
        )
        
        self.assertEqual(logits.shape, (2, 10, 164))

    def test_model_generate_auto_regressive(self) -> None:
        src = torch.randint(1, 8, (12,))
        # Generate with max_len = 5
        generated = self.model.generate(
            src=src,
            bos_id=1,
            eos_id=2,
            pad_id=0,
            midi_tokenizer=self.midi_tokenizer,
            max_len=5,
            temperature=1.0,
            top_k=5,
            device="cpu",
        )
        
        self.assertGreaterEqual(len(generated), 1)
        self.assertEqual(generated[0], 1)  # BOS check


class TestDatasetCollation(unittest.TestCase):
    def test_collate_pretrain(self) -> None:
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([2, 3, 4])),
            (torch.tensor([1, 5]), torch.tensor([5, 6])),
        ]
        inputs, targets = collate_pretrain(batch)
        
        # Batch size 2, max seq length 3
        self.assertEqual(inputs.shape, (2, 3))
        self.assertEqual(targets.shape, (2, 3))
        # Checking pad values
        self.assertEqual(inputs[1, 2].item(), 0)
        self.assertEqual(targets[1, 2].item(), -100)

    def test_collate_seq2seq(self) -> None:
        batch = [
            (torch.tensor([10, 11, 12]), torch.tensor([1, 2]), torch.tensor([2, 3])),
            (torch.tensor([10, 13]), torch.tensor([1, 4, 5]), torch.tensor([4, 5, 6])),
        ]
        srcs, tgt_inputs, tgt_targets, src_masks, tgt_masks = collate_seq2seq(batch)
        
        # Batch size 2
        # Max src length 3, Max tgt length 3
        self.assertEqual(srcs.shape, (2, 3))
        self.assertEqual(tgt_inputs.shape, (2, 3))
        self.assertEqual(tgt_targets.shape, (2, 3))
        
        # Verification of padding masks
        self.assertTrue(src_masks[1, 2].item())  # Padded location
        self.assertFalse(src_masks[0, 2].item())  # Normal location


if __name__ == "__main__":
    unittest.main()
