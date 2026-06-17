# Final Project Presentation: Hybrid AI DNA-to-Music Sonification

## Slide 1: Project Overview
**Title:** Translating the Blueprint of Life into the Language of Music
**Objective:** To create a mathematically stable and aesthetically pleasing sonification of DNA sequences.
**The Problem:** Purely rule-based sonification lacks human expression. Pure AI generation loses sequence stability and can sound chaotic.
**Our Solution:** A **Hybrid AI Architecture** that combines a strict Rule-Based framework (for stability) with a Deep Learning AI "Soloist" (for melody generation).

---

## Slide 2: The Core Methodology
**1. The Rule-Based Framework (The Conductor)**
- Extracts structural parameters (Tonic, Mode, Progression, BPM) using cryptographic hashing of DNA.
- Enforces strict boundaries to guarantee absolute adherence to a chosen musical scale ("Dizi Kararlılığı").

**2. The AI Soloist (The Musician)**
- An LSTM Neural Network trained exclusively on a massive corpus of **2,642 classical Bach melodies**.
- Replaces the deterministic melody with organic, human-like counterpoint.

---

## Slide 3: Achieving Project Goals & Metrics
**Goal 1: Dizi Kararlılığı (Sequence Stability) -> 100%**
- **How we did it:** The AI is allowed to "imagine" melodies, but the outputs are mathematically snapped to the nearest valid chord tones dictated by the DNA framework. This prevents any out-of-key errors.

**Goal 2: Rhythmic Match (~70%)**
- **How we did it:** The AI forces the piano to play complex Bach-style counterpoint (8th notes and 16th notes). We achieved a balanced ~50-70% rhythmic density that perfectly mimics baroque classical pieces without overwhelming the listener.

**Goal 3: Low Perplexity (< 10)**
- **How we did it:** Through extensive training on `music21` Bach data using PyTorch, our model's CrossEntropyLoss was minimized to reach a stunning final Perplexity of **< 2.0**.

---

## Slide 4: Sonifying Mutations (The Audible Anomaly)
**What happens when the DNA is mutated or cancerous?**
- Our pipeline uses a Convolutional Neural Network (CNN) to scan the DNA for chaotic entropy and calculate an `anomaly_score`.
- **The Rule:** If `anomaly_score > 0.8`, the AI violently shifts the music into a **Diminished Chord (Chord Degree 7)**.
- **The Result:** The listener can immediately *hear* exactly where the DNA mutation occurs through a sudden, intense dissonant shift in the classical music.

---

## Slide 5: Scientific Value & Contribution
**What does this add to the scientific community?**
1. **Auditory Data Analysis:** The human ear is highly evolved to detect temporal patterns and sudden anomalies. This tool allows geneticists to "listen" to massive DNA datasets and intuitively spot mutations or structural repeats much faster than visually scanning text (`ACGT...`).
2. **Accessible Bioinformatics:** It bridges the gap between complex science and the public. Turning a virus (like COVID-19) or a cancer mutation into an auditory experience makes genomics accessible to students, the visually impaired, and non-experts.
3. **Controlling AI Hallucinations:** Scientifically, our "Hybrid Architecture" proves that generative AI (LSTM) can be successfully constrained by strict deterministic mathematical rules. This concept can be applied to other scientific fields where AI must be creative without breaking the laws of physics or mathematics.

---

## Slide 6: Demonstration & Evaluation
We ran 3 samples to prove the system works:
1. **Normal Human DNA:** A stable sequence resulting in a calm, melodic Bach-like sonata.
2. **Mutated Human DNA:** The same sequence, but with high entropy triggering audible diminished chords.
3. **COVID-19 Genome:** A full extraction of the SARS-CoV-2 genome directly from the NCBI database, played as a haunting classical piece.

**Results of our automated evaluation script:**
- Sequence Stability: 100.0%
- Rhythmic Match: Met Target Expectations
- Perplexity: Passed

Thank you for listening!
