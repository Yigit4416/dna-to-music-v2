from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from Bio import SeqIO
from music21 import chord, clef, expressions, instrument, metadata, meter, note, stream, tempo

TONICS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
TONIC_TO_PC = {name: index for index, name in enumerate(TONICS)}

MODES = ["major", "natural_minor", "dorian", "phrygian"]
MODE_DISPLAY = {
    "major": "Major (Ionian)",
    "natural_minor": "Natural Minor (Aeolian)",
    "dorian": "Dorian",
    "phrygian": "Phrygian",
}
MODE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
}
TRIAD_QUALITIES = {
    "major": ["maj", "min", "min", "maj", "maj", "min", "dim"],
    "natural_minor": ["min", "dim", "maj", "min", "min", "maj", "maj"],
    "dorian": ["min", "min", "maj", "maj", "min", "dim", "maj"],
    "phrygian": ["min", "maj", "maj", "min", "dim", "maj", "min"],
}
PROGRESSIONS = {
    "Prog A": [1, 6, 4, 5],
    "Prog B": [6, 4, 1, 5],
}
PATTERN_LABELS = {
    "P1": "Ballad",
    "P2": "Broken Chord",
    "P3": "Arpeggio",
}
BASE_SCALE_OCTAVE = 4
MELODY_MIN_POSITION = 4
MELODY_MAX_POSITION = 13


@dataclass(frozen=True)
class SonificationConfig:
    duration_seconds: int = 120
    window_size: int = 300
    stride: int = 150
    enable_add9: bool = False
    title: str = "DNA Sonification"


@dataclass(frozen=True)
class PieceSummary:
    source_label: str
    tonic: str
    mode: str
    progression: str
    bpm: int
    duration_seconds: int
    measures: int
    global_entropy: float
    add9_enabled: bool

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["mode_display"] = MODE_DISPLAY[self.mode]
        payload["scale_pitch_classes"] = list(build_scale_pitch_classes(self.tonic, self.mode))
        payload["progression_degrees"] = list(PROGRESSIONS[self.progression])
        return payload


def sonify_sequence(sequence: str, config: SonificationConfig, source_label: str = "DNA") -> tuple[stream.Score, PieceSummary]:
    normalized = normalize_sequence(sequence)
    identity_seed = repeat_to_length(normalized, 2400)

    tonic = TONICS[sha_mod(identity_seed[:1200], 12, "tonic")]
    mode = MODES[sha_mod(identity_seed[1200:2400], 4, "mode")]
    progression_name = "Prog A" if purine_ratio(identity_seed[:1200]) < 0.50 else "Prog B"
    progression = PROGRESSIONS[progression_name]

    global_entropy = normalized_shannon_entropy(normalized)
    bpm = select_bpm(global_entropy)
    measures = max(1, round((config.duration_seconds * bpm) / 240))

    required_length = max(2400, config.window_size + config.stride * max(0, measures - 1))
    expanded = repeat_to_length(normalized, required_length)
    windows = [
        expanded[index * config.stride : index * config.stride + config.window_size]
        for index in range(measures)
    ]

    summary = PieceSummary(
        source_label=source_label,
        tonic=tonic,
        mode=mode,
        progression=progression_name,
        bpm=bpm,
        duration_seconds=config.duration_seconds,
        measures=measures,
        global_entropy=round(global_entropy, 4),
        add9_enabled=config.enable_add9,
    )

    score = build_score(
        windows=windows,
        tonic=tonic,
        mode=mode,
        progression=progression,
        bpm=bpm,
        summary=summary,
        config=config,
    )
    return score, summary


def build_score(
    windows: list[str],
    tonic: str,
    mode: str,
    progression: list[int],
    bpm: int,
    summary: PieceSummary,
    config: SonificationConfig,
) -> stream.Score:
    score = stream.Score(id="DNA_Sonification")
    score.metadata = metadata.Metadata()
    score.metadata.title = config.title
    score.metadata.composer = "dna-sonifier"
    score.insert(0, tempo.MetronomeMark(number=bpm))

    right_hand = stream.Part(id="RH")
    right_hand.insert(0, instrument.Piano())
    right_hand.insert(0, clef.TrebleClef())
    right_hand.insert(0, meter.TimeSignature("4/4"))

    left_hand = stream.Part(id="LH")
    left_hand.insert(0, instrument.Piano())
    left_hand.insert(0, clef.BassClef())
    left_hand.insert(0, meter.TimeSignature("4/4"))

    previous_signature: int | None = None
    melody_history: list[int] = []
    current_position = degree_octave_to_position(progression[0], 5)

    for measure_index, window in enumerate(windows):
        chord_degree = progression[measure_index % len(progression)]
        energy = energy_score(window)
        velocity = select_velocity(strength_score(window))
        pattern = select_pattern(energy)
        signature = sha_mod(window, 16, "measure-signature")
        variation_needed = previous_signature == signature

        step = sha_mod(window, 5, f"step-{measure_index}") + 1
        direction = 1 if sha_mod(window, 2, f"direction-{measure_index}") == 0 else -1
        add9 = config.enable_add9 and should_add9(windows, measure_index)

        melody_positions, current_position = build_melody_positions(
            chord_degree=chord_degree,
            step=step,
            direction=direction,
            previous_position=current_position,
            history=melody_history,
            window=window,
            measure_index=measure_index,
            variation_needed=variation_needed,
        )

        melody_history.extend(melody_positions)
        right_measure = build_right_hand_measure(
            measure_number=measure_index + 1,
            tonic=tonic,
            mode=mode,
            chord_degree=chord_degree,
            melody_positions=melody_positions,
            pattern=pattern,
            velocity=velocity,
            split_last_beat=variation_needed,
            direction=direction,
            add9=add9,
        )
        left_measure = build_left_hand_measure(
            measure_number=measure_index + 1,
            tonic=tonic,
            mode=mode,
            chord_degree=chord_degree,
            energy=energy,
            velocity=velocity,
        )

        add_measure_annotation(right_measure, pattern=pattern, signature=signature, summary=summary if measure_index == 0 else None)
        right_hand.append(right_measure)
        left_hand.append(left_measure)
        previous_signature = signature

    score.insert(0, right_hand)
    score.insert(0, left_hand)
    return score


def build_right_hand_measure(
    measure_number: int,
    tonic: str,
    mode: str,
    chord_degree: int,
    melody_positions: list[int],
    pattern: str,
    velocity: int,
    split_last_beat: bool,
    direction: int,
    add9: bool,
) -> stream.Measure:
    measure = stream.Measure(number=measure_number)
    melody_voice = stream.Voice(id=f"melody-{measure_number}")
    texture_voice = stream.Voice(id=f"texture-{measure_number}")

    for beat_index, position_value in enumerate(melody_positions[:3]):
        melody_voice.append(make_note(position_to_midi(tonic, mode, position_value), 1.0, velocity))

    final_pitch = melody_positions[3]
    if split_last_beat:
        first = make_note(position_to_midi(tonic, mode, final_pitch), 0.5, velocity)
        follow_up = enforce_bounds(final_pitch + (1 if direction >= 0 else -1), MELODY_MIN_POSITION, MELODY_MAX_POSITION)
        second = make_note(position_to_midi(tonic, mode, follow_up), 0.5, velocity)
        melody_voice.append(first)
        melody_voice.append(second)
    else:
        melody_voice.append(make_note(position_to_midi(tonic, mode, final_pitch), 1.0, velocity))

    texture_events = build_texture_events(
        tonic=tonic,
        mode=mode,
        chord_degree=chord_degree,
        pattern=pattern,
        velocity=max(40, velocity - 8),
        add9=add9,
    )
    for event in texture_events:
        texture_voice.append(event)

    measure.insert(0, melody_voice)
    measure.insert(0, texture_voice)
    return measure


def build_left_hand_measure(
    measure_number: int,
    tonic: str,
    mode: str,
    chord_degree: int,
    energy: float,
    velocity: int,
) -> stream.Measure:
    measure = stream.Measure(number=measure_number)
    root_position = degree_octave_to_position(chord_degree, 2)
    fifth_position = root_position + 4

    pitches = [
        position_to_midi(tonic, mode, root_position),
        position_to_midi(tonic, mode, fifth_position),
    ]
    if energy >= 0.66:
        pitches.append(position_to_midi(tonic, mode, root_position + 7))

    event = chord.Chord(pitches, quarterLength=4.0)
    event.volume.velocity = max(35, velocity - 14)
    measure.append(event)
    return measure


def build_texture_events(
    tonic: str,
    mode: str,
    chord_degree: int,
    pattern: str,
    velocity: int,
    add9: bool,
) -> list[note.Note | chord.Chord]:
    root = degree_octave_to_position(chord_degree, 4)
    triad_positions = [root, root + 2, root + 4]
    chord_positions = list(triad_positions)
    if add9:
        chord_positions.append(root + 8)

    if pattern == "P1":
        first = chord.Chord([position_to_midi(tonic, mode, pos) for pos in chord_positions], quarterLength=2.0)
        second = chord.Chord([position_to_midi(tonic, mode, pos) for pos in chord_positions], quarterLength=2.0)
        first.volume.velocity = velocity
        second.volume.velocity = velocity
        return [first, second]

    if pattern == "P2":
        sequence = [root, root + 2, root + 4, root + 2, root + 7, root + 4, root + 2, root + 4]
    else:
        sequence = [root, root + 2, root + 4, root + 7, root + 4, root + 2, root, root + 2]

    events: list[note.Note] = []
    for position_value in sequence:
        midi_number = position_to_midi(tonic, mode, position_value)
        item = make_note(midi_number, 0.5, velocity)
        events.append(item)
    return events


def build_melody_positions(
    chord_degree: int,
    step: int,
    direction: int,
    previous_position: int,
    history: list[int],
    window: str,
    measure_index: int,
    variation_needed: bool,
) -> tuple[list[int], int]:
    chord_candidates = expand_chord_positions(chord_degree, octave_span=(4, 6))
    melody_positions: list[int] = []

    beat_one_target = previous_position
    beat_one = choose_nearest(chord_candidates, beat_one_target, seed=sha_int(window, f"beat1-{measure_index}"))
    beat_one = avoid_triple_repeat(beat_one, history + melody_positions, direction)
    melody_positions.append(beat_one)

    beat_two = choose_passing_tone(beat_one, direction, chord_candidates)
    beat_two = avoid_triple_repeat(beat_two, history + melody_positions, direction)
    melody_positions.append(beat_two)

    beat_three_target = beat_two + direction * step
    beat_three = choose_nearest(chord_candidates, beat_three_target, seed=sha_int(window, f"beat3-{measure_index}"))
    beat_three = avoid_triple_repeat(beat_three, history + melody_positions, direction)
    melody_positions.append(beat_three)

    recovery_direction = -direction if step >= 4 else direction
    beat_four = choose_passing_tone(beat_three, recovery_direction, chord_candidates)
    if variation_needed:
        shift = 2 if sha_mod(window, 2, f"variation-{measure_index}") == 0 else -2
        beat_two = avoid_triple_repeat(
            enforce_bounds(beat_two + shift, MELODY_MIN_POSITION, MELODY_MAX_POSITION),
            history + [melody_positions[0]],
            direction,
        )
        melody_positions[1] = beat_two
    beat_four = avoid_triple_repeat(beat_four, history + melody_positions, recovery_direction)
    melody_positions.append(beat_four)
    return melody_positions, beat_four


def add_measure_annotation(measure: stream.Measure, pattern: str, signature: int, summary: PieceSummary | None) -> None:
    if summary is None:
        return
    text = (
        f"{summary.tonic} {MODE_DISPLAY[summary.mode]} | "
        f"{summary.progression} | {summary.bpm} BPM | {PATTERN_LABELS[pattern]} | sig={signature}"
    )
    measure.insert(0, expressions.TextExpression(text))


def choose_passing_tone(anchor: int, direction: int, chord_candidates: list[int]) -> int:
    primary = enforce_bounds(anchor + direction, MELODY_MIN_POSITION, MELODY_MAX_POSITION)
    secondary = enforce_bounds(anchor - direction, MELODY_MIN_POSITION, MELODY_MAX_POSITION)

    if primary not in chord_candidates:
        return primary
    if secondary not in chord_candidates:
        return secondary
    return primary


def expand_chord_positions(chord_degree: int, octave_span: tuple[int, int]) -> list[int]:
    positions: list[int] = []
    for octave in range(octave_span[0], octave_span[1] + 1):
        root = degree_octave_to_position(chord_degree, octave)
        positions.extend([root, root + 2, root + 4])
    return [pos for pos in positions if MELODY_MIN_POSITION - 7 <= pos <= MELODY_MAX_POSITION + 7]


def choose_nearest(candidates: list[int], target: int, seed: int) -> int:
    ranked = sorted(candidates, key=lambda value: (abs(value - target), tie_breaker(value, seed)))
    return enforce_bounds(ranked[0], MELODY_MIN_POSITION, MELODY_MAX_POSITION)


def tie_breaker(value: int, seed: int) -> int:
    return abs((seed % 19) - (value % 19))


def avoid_triple_repeat(position_value: int, history: list[int], direction: int) -> int:
    if len(history) >= 2 and history[-1] == history[-2] == position_value:
        forward = enforce_bounds(position_value + 1, MELODY_MIN_POSITION, MELODY_MAX_POSITION)
        backward = enforce_bounds(position_value - 1, MELODY_MIN_POSITION, MELODY_MAX_POSITION)
        return forward if direction >= 0 else backward
    return position_value


def should_add9(windows: list[str], measure_index: int) -> bool:
    block_start = (measure_index // 4) * 4
    block = "".join(windows[block_start : block_start + 4])
    slot = sha_mod(block, 4, f"add9-slot-{block_start}")
    return (measure_index - block_start) == slot


def select_bpm(entropy_value: float) -> int:
    if entropy_value < 0.33:
        return 80
    if entropy_value < 0.66:
        return 92
    return 104


def select_pattern(energy_value: float) -> str:
    if energy_value < 0.33:
        return "P1"
    if energy_value < 0.66:
        return "P2"
    return "P3"


def select_velocity(strength_value: float) -> int:
    if strength_value < 0.33:
        return 55
    if strength_value < 0.66:
        return 72
    return 88


def build_scale_pitch_classes(tonic: str, mode: str) -> tuple[int, ...]:
    tonic_pc = TONIC_TO_PC[tonic]
    return tuple((tonic_pc + interval) % 12 for interval in MODE_INTERVALS[mode])


def position_to_midi(tonic: str, mode: str, position_value: int) -> int:
    octave_offset, scale_degree = divmod(position_value, 7)
    tonic_pc = TONIC_TO_PC[tonic]
    semitone_offset = MODE_INTERVALS[mode][scale_degree]
    octave = BASE_SCALE_OCTAVE + octave_offset
    return (octave + 1) * 12 + tonic_pc + semitone_offset


def degree_octave_to_position(degree: int, octave: int) -> int:
    return (degree - 1) + 7 * (octave - BASE_SCALE_OCTAVE)


def make_note(midi_number: int, duration: float, velocity: int) -> note.Note:
    item = note.Note()
    item.pitch.midi = midi_number
    item.quarterLength = duration
    item.volume.velocity = velocity
    return item


def normalize_sequence(sequence: str) -> str:
    filtered: list[str] = []
    for char in sequence.upper():
        if char in {"A", "C", "G", "T"}:
            filtered.append(char)
        elif char.isalpha():
            filtered.append("N")
    normalized = "".join(filtered)
    if not normalized or not any(base in {"A", "C", "G", "T"} for base in normalized):
        raise ValueError("Gecerli A/C/G/T bazlari bulunamadi.")
    return normalized


def repeat_to_length(sequence: str, target_length: int) -> str:
    repeats = math.ceil(target_length / len(sequence))
    return (sequence * repeats)[:target_length]


def normalized_shannon_entropy(segment: str) -> float:
    bases = canonical_bases(segment)
    if not bases:
        return 0.0
    counts = Counter(bases)
    entropy_value = 0.0
    total = len(bases)
    for count in counts.values():
        probability = count / total
        entropy_value -= probability * math.log2(probability)
    return min(1.0, entropy_value / 2.0)


def purine_ratio(segment: str) -> float:
    bases = canonical_bases(segment)
    if not bases:
        return 0.5
    purines = sum(1 for base in bases if base in {"A", "G"})
    return purines / len(bases)


def strength_score(segment: str) -> float:
    bases = canonical_bases(segment)
    if not bases:
        return 0.5
    weights = {"A": 2, "T": 2, "C": 3, "G": 3}
    average = sum(weights[base] for base in bases) / len(bases)
    return max(0.0, min(1.0, average - 2.0))


def energy_score(segment: str) -> float:
    entropy_value = normalized_shannon_entropy(segment)
    transitions = transition_rate(segment)
    return max(0.0, min(1.0, 0.55 * entropy_value + 0.45 * transitions))


def transition_rate(segment: str) -> float:
    bases = canonical_bases(segment)
    if len(bases) < 2:
        return 0.0
    transitions = sum(1 for left, right in zip(bases, bases[1:]) if left != right)
    return transitions / (len(bases) - 1)


def canonical_bases(segment: str) -> list[str]:
    return [base for base in segment if base in {"A", "C", "G", "T"}]


def sha_int(payload: str, salt: str = "") -> int:
    digest = hashlib.sha256(f"{salt}|{payload}".encode("utf-8")).hexdigest()
    return int(digest, 16)


def sha_mod(payload: str, modulo: int, salt: str = "") -> int:
    return sha_int(payload, salt) % modulo


def enforce_bounds(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def load_sequence_from_file(path: Path) -> tuple[str, str]:
    raw_text = path.read_text(encoding="utf-8")
    if raw_text.lstrip().startswith(">"):
        records = list(SeqIO.parse(str(path), "fasta"))
        if not records:
            raise ValueError(f"FASTA icinde kayit bulunamadi: {path}")
        record = records[0]
        return str(record.seq), record.id
    return raw_text, path.stem


def write_summary(path: Path, summary: PieceSummary) -> None:
    path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
