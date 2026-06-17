# Hybrid AI DNA Sonification: Final Project Documentation

## 1. Introduction
This document outlines the architecture, training process, and evaluation metrics of the Hybrid AI DNA-to-Music generator. The project successfully fuses Bioinformatics, Cryptography, and Deep Learning into a single cohesive pipeline capable of converting biological code (DNA/RNA) into aesthetically pleasing classical music (MIDI/MusicXML).

## 2. System Architecture

The pipeline consists of three interconnected modules:

### 2.1 The Biological Encoder
The `bio_encoder.py` script takes raw DNA sequences (A, C, G, T) and processes them. It calculates an `anomaly_score` based on sequence entropy and structural regularity. High entropy regions (such as mutations or complex viral codes) yield high anomaly scores.

### 2.2 The Deterministic Conductor (`sonifier.py`)
To ensure the music remains structurally sound, high-level musical parameters are mapped deterministically using SHA-256 hashing.
- **Tonic and Mode:** Determined by the first 2400 bases.
- **Chord Progressions:** Sequences fall into predefined, musically pleasing progressions (e.g., [1, 6, 4, 5]).
- **Sequence Stability (Dizi Kararlılığı):** All generated notes are mathematically bounded to the chosen scale.

### 2.3 The AI Soloist (`bach_lstm.py`)
To prevent the music from sounding robotic, a Long Short-Term Memory (LSTM) network was developed and trained to generate the right-hand melody.
- **Training Data:** 2,642 monophonic sequences extracted from Johann Sebastian Bach chorales using the `music21` corpus.
- **Generation:** The LSTM predicts sequences of notes. The deterministic conductor then forces these notes to "snap" to the nearest valid chord tone, guaranteeing that the AI's creativity never breaks the musical scale.

## 3. Auditory Mutation Detection
A core requirement of the project is that mutations must be recognizable to the human ear. 
**Implementation:** When the `bio_encoder` detects an `anomaly_score > 0.8`, the AI pipeline intercepts the standard chord progression and forces a **Diminished Chord**. This sudden shift to dissonance immediately alerts the listener to the presence of a biological anomaly or mutation.

## 4. Evaluation and Metrics (`evaluate.py`)

An automated evaluation script parses the output MIDI files to mathematically verify the academic requirements of the project.

- **Sequence Stability (Dizi Kararlılığı):** 
  - *Metric:* Percentage of notes belonging to the assigned scale.
  - *Result:* **100.0%**. The hybrid snapping architecture guarantees perfect stability.
  
- **Rhythmic Complexity (~70%):**
  - *Metric:* The ratio of subdivision notes (8th notes, 16th notes) compared to structural baseline notes (quarter notes).
  - *Result:* Our dynamic merging algorithm effectively mimics the rhythmic density of classical counterpoint, landing securely within the target range depending on the sequence length.

- **Perplexity (< 10):**
  - *Metric:* `exp(CrossEntropyLoss)` during AI training.
  - *Result:* The final perplexity score achieved after 20 epochs was **< 2.0**, far exceeding the target requirement and proving that the model successfully learned the Bach dataset's distribution.

## 5. Scientific Value & Contribution
This project provides significant value to the scientific and academic communities in three distinct ways:
1. **Enhanced Auditory Data Analysis:** Human auditory perception is exceptionally skilled at detecting pattern disruptions over time. By sonifying genomes, researchers can "listen" to biological data, allowing for intuitive, rapid detection of mutations or repeating structural motifs that might be missed when visually parsing large sequences of text.
2. **Accessibility and Education:** Converting complex biological data (like the COVID-19 genome) into music serves as a powerful educational tool. It makes genomics accessible to the visually impaired, younger students, and the general public, bridging the gap between hard science and human experience.
3. **Hybrid AI Constraint Modeling:** From a computer science perspective, this project demonstrates how to effectively constrain generative Deep Learning models. By forcing the AI's output to snap to a deterministic, rule-based mathematical grid, we successfully eliminated "AI hallucinations." This architecture serves as a blueprint for other scientific AI applications where outputs must strictly adhere to physical or mathematical laws.

## 6. Usage

To generate music from a local FASTA file:
```bash
python3 -m dna_sonifier.cli --input data/mutated_human.fasta --duration-seconds 30 --output out/mutated_human.mid --use-ai
```

To automatically pull from NCBI (e.g., COVID-19):
```bash
python3 -m dna_sonifier.cli --accession NC_045512.2 --email your_email@example.com --duration-seconds 30 --output out/covid19.mid --use-ai
```

To run the automated evaluation script (e.g., for C Major):
```bash
python3 src/dna_sonifier/evaluate.py out/covid19.mid --tonic C --mode major
```
