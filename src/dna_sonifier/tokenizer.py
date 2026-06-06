from __future__ import annotations

import math
from pathlib import Path
from music21 import converter, note, chord, stream, instrument

# Constants for discrete MIDI values to keep the vocabulary small and clean
DURATIONS = [0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
VELOCITIES = [16, 32, 48, 64, 80, 96, 112, 127]


def quantize_value(val: float, choices: list[float]) -> float:
    """Finds the closest value in choices to the given val."""
    return min(choices, key=lambda x: abs(x - val))


class DNATokenizer:
    """Tokenizer for DNA sequences. Maps bases to unique IDs."""
    
    SPECIAL_TOKENS = ["<pad>", "<s>", "</s>", "<unk>"]
    BASES = ["A", "C", "G", "T", "N"]
    
    def __init__(self) -> None:
        self.vocab = self.SPECIAL_TOKENS + self.BASES
        self.token_to_id = {token: idx for idx, token in enumerate(self.vocab)}
        self.id_to_token = {idx: token for idx, token in enumerate(self.vocab)}
        self.pad_id = self.token_to_id["<pad>"]
        self.bos_id = self.token_to_id["<s>"]
        self.eos_id = self.token_to_id["</s>"]
        self.unk_id = self.token_to_id["<unk>"]
        self.vocab_size = len(self.vocab)

    def encode(self, sequence: str, add_special_tokens: bool = True) -> list[int]:
        """Converts DNA string to list of token IDs."""
        tokens = []
        if add_special_tokens:
            tokens.append(self.bos_id)
            
        for char in sequence.upper():
            if char in self.token_to_id:
                tokens.append(self.token_to_id[char])
            elif char.isalpha():
                tokens.append(self.token_to_id["N"])
            else:
                tokens.append(self.unk_id)
                
        if add_special_tokens:
            tokens.append(self.eos_id)
        return tokens

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        """Converts token IDs back to a DNA string."""
        chars = []
        for idx in token_ids:
            token = self.id_to_token.get(idx, "<unk>")
            if skip_special_tokens and token in self.SPECIAL_TOKENS:
                continue
            chars.append(token)
        return "".join(chars)


class MIDITokenizer:
    """REMI-style MIDI Event Tokenizer.
    
    Uses an event-based representation:
    - NOTE_ON_<pitch> (0-127)
    - DURATION_<duration> (from discrete DURATIONS)
    - VELOCITY_<velocity> (from discrete VELOCITIES)
    - TIME_SHIFT_<dt> (from discrete DURATIONS)
    """

    SPECIAL_TOKENS = ["<pad>", "<s>", "</s>", "<unk>"]

    def __init__(self) -> None:
        self.vocab = list(self.SPECIAL_TOKENS)
        
        # NOTE_ON tokens
        self.note_on_tokens = [f"NOTE_ON_{i}" for i in range(128)]
        self.vocab.extend(self.note_on_tokens)
        
        # DURATION tokens
        self.duration_tokens = [f"DURATION_{d}" for d in DURATIONS]
        self.vocab.extend(self.duration_tokens)
        
        # VELOCITY tokens
        self.velocity_tokens = [f"VELOCITY_{v}" for v in VELOCITIES]
        self.vocab.extend(self.velocity_tokens)
        
        # TIME_SHIFT tokens
        self.time_shift_tokens = [f"TIME_SHIFT_{d}" for d in DURATIONS]
        self.vocab.extend(self.time_shift_tokens)
        
        self.token_to_id = {token: idx for idx, token in enumerate(self.vocab)}
        self.id_to_token = {idx: token for idx, token in enumerate(self.vocab)}
        self.pad_id = self.token_to_id["<pad>"]
        self.bos_id = self.token_to_id["<s>"]
        self.eos_id = self.token_to_id["</s>"]
        self.unk_id = self.token_to_id["<unk>"]
        self.vocab_size = len(self.vocab)

    def encode(self, tokens: list[str], add_special_tokens: bool = True) -> list[int]:
        """Converts string tokens to list of token IDs."""
        ids = []
        if add_special_tokens:
            ids.append(self.bos_id)
        for token in tokens:
            ids.append(self.token_to_id.get(token, self.unk_id))
        if add_special_tokens:
            ids.append(self.eos_id)
        return ids

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> list[str]:
        """Converts token IDs back to string tokens."""
        tokens = []
        for idx in token_ids:
            token = self.id_to_token.get(idx, "<unk>")
            if skip_special_tokens and token in self.SPECIAL_TOKENS:
                continue
            tokens.append(token)
        return tokens

    def encode_midi(self, midi_path_or_score: str | Path | stream.Score) -> list[str]:
        """Extracts Note and Chord events from a music21 stream or MIDI file,
        sorting them chronologically and converting into string tokens.
        """
        if isinstance(midi_path_or_score, (str, Path)):
            score = converter.parse(str(midi_path_or_score))
        else:
            score = midi_path_or_score

        flat_elements = score.flatten()
        events = []

        # Gather notes and chords
        for element in flat_elements:
            if isinstance(element, note.Note):
                pitch = element.pitch.midi
                duration = float(element.duration.quarterLength)
                velocity = element.volume.velocity if element.volume.velocity is not None else 64
                events.append((float(element.offset), "note", pitch, duration, velocity))
            elif isinstance(element, chord.Chord):
                duration = float(element.duration.quarterLength)
                velocity = element.volume.velocity if element.volume.velocity is not None else 64
                for pitch_obj in element.pitches:
                    events.append((float(element.offset), "note", pitch_obj.midi, duration, velocity))

        if not events:
            return []

        # Sort events by starting offset (time)
        events.sort(key=lambda x: (x[0], x[2]))  # Sort by offset, then by pitch

        tokens = []
        last_offset = 0.0

        for offset, ev_type, pitch, duration, velocity in events:
            dt = offset - last_offset
            if dt > 0.01:  # Threshold to treat as a distinct offset
                # Quantize the time shift
                quantized_dt = quantize_value(dt, DURATIONS)
                tokens.append(f"TIME_SHIFT_{quantized_dt}")
                last_offset = offset
            elif dt < 0:
                # Chronologically out of order fallback (should not happen after sorting)
                pass
            
            # Quantize duration and velocity
            quant_dur = quantize_value(duration, DURATIONS)
            quant_vel = int(quantize_value(velocity, VELOCITIES))
            
            tokens.append(f"NOTE_ON_{pitch}")
            tokens.append(f"DURATION_{quant_dur}")
            tokens.append(f"VELOCITY_{quant_vel}")

        return tokens

    def decode_tokens(self, tokens: list[str]) -> stream.Score:
        """Translates string tokens back into a music21 Score."""
        score = stream.Score(id="AI_Generated_Piano")
        part = stream.Part(id="PianoPart")
        part.insert(0, instrument.Piano())
        
        current_time = 0.0
        
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            
            if token.startswith("TIME_SHIFT_"):
                try:
                    dt = float(token.split("_")[-1])
                    current_time += dt
                except ValueError:
                    pass
                idx += 1
                
            elif token.startswith("NOTE_ON_"):
                try:
                    pitch_val = int(token.split("_")[-1])
                    
                    # Look ahead for duration and velocity
                    duration_val = 1.0
                    velocity_val = 64
                    
                    if idx + 1 < len(tokens) and tokens[idx + 1].startswith("DURATION_"):
                        try:
                            duration_val = float(tokens[idx + 1].split("_")[-1])
                        except ValueError:
                            pass
                        idx += 1
                        
                    if idx + 1 < len(tokens) and tokens[idx + 1].startswith("VELOCITY_"):
                        try:
                            velocity_val = int(tokens[idx + 1].split("_")[-1])
                        except ValueError:
                            pass
                        idx += 1
                        
                    n = note.Note()
                    n.pitch.midi = pitch_val
                    n.quarterLength = duration_val
                    n.volume.velocity = velocity_val
                    part.insert(current_time, n)
                    
                except ValueError:
                    pass
                idx += 1
            else:
                idx += 1  # Skip unknown or special tokens

        score.insert(0, part)
        return score
