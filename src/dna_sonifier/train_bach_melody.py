import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import music21 as m21
import math
import argparse
from pathlib import Path

from dna_sonifier.bach_lstm import BachLSTM

class BachMelodyDataset(Dataset):
    def __init__(self, sequences):
        self.sequences = sequences

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        seq = self.sequences[idx]
        # Input: all notes except last. Target: all notes except first.
        # This allows predicting the next note at every step.
        x = torch.tensor(seq[:-1], dtype=torch.long)
        y = torch.tensor(seq[1:], dtype=torch.long)
        return x, y

def extract_melodies_from_corpus(limit=50, seq_length=32):
    print(f"Extracting melodies from up to {limit} Bach chorales...")
    bach_paths = m21.corpus.getComposer('bach')
    all_sequences = []
    
    count = 0
    for path in bach_paths:
        if count >= limit:
            break
        try:
            score = m21.corpus.parse(path)
            # Usually the Soprano part is the top melody, which is index 0
            parts = score.getElementsByClass(m21.stream.Part)
            if not parts:
                continue
            
            melody_part = parts[0]
            notes = melody_part.flatten().notes
            
            pitches = []
            for n in notes:
                if isinstance(n, m21.note.Note):
                    pitches.append(n.pitch.midi)
                elif isinstance(n, m21.chord.Chord):
                    pitches.append(n.sortAscending()[-1].pitch.midi) # highest pitch
                    
            if len(pitches) > seq_length:
                # Create rolling windows of length seq_length + 1
                for i in range(len(pitches) - seq_length):
                    window = pitches[i : i + seq_length + 1]
                    # Filter out out-of-bounds MIDI just in case
                    window = [max(0, min(127, p)) for p in window]
                    all_sequences.append(window)
            count += 1
        except Exception as e:
            print(f"Error parsing {path}: {e}")
            
    print(f"Extracted {len(all_sequences)} sequences of length {seq_length}.")
    return all_sequences

def train_bach_lstm(epochs=20, batch_size=32, limit=100, output_path="bach_lstm.pt"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training Bach LSTM on {device}...")
    
    sequences = extract_melodies_from_corpus(limit=limit, seq_length=32)
    if not sequences:
        print("No sequences found. Cannot train.")
        return
        
    dataset = BachMelodyDataset(sequences)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    model = BachLSTM(vocab_size=128).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad()
            logits, _ = model(x)
            
            # Reshape for CrossEntropy: logits [batch*seq_len, vocab], y [batch*seq_len]
            logits = logits.reshape(-1, 128)
            y = y.reshape(-1)
            
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        perplexity = math.exp(avg_loss)
        print(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f} - Perplexity: {perplexity:.4f}")
        
    torch.save(model.state_dict(), output_path)
    print(f"Saved trained model to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--limit", type=int, default=100, help="Number of Bach pieces to parse")
    parser.add_argument("--output", type=str, default="bach_lstm.pt")
    args = parser.parse_args()
    
    train_bach_lstm(epochs=args.epochs, limit=args.limit, output_path=args.output)
