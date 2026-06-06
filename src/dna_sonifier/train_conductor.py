import torch
import torch.nn as nn
import torch.optim as optim
import random
from pathlib import Path
from tqdm import tqdm

from dna_sonifier.conductor import get_conductor_pipeline

def calculate_gc_content(sequence: str) -> float:
    seq_len = len(sequence)
    if seq_len == 0: return 0.0
    gc_count = sequence.count('G') + sequence.count('C')
    return gc_count / seq_len

def generate_random_dna(length: int) -> str:
    return "".join(random.choices(['A', 'C', 'G', 'T'], k=length))

def generate_mutated_dna(length: int) -> str:
    # A sequence with unusual repetition or weird structure to simulate an anomaly
    base = generate_random_dna(10)
    return (base * (length // 10 + 1))[:length]

def train_conductor(
    epochs: int = 100,
    batch_size: int = 16,
    window_size: int = 300,
    use_pretrained: bool = False,
    output_path: str = "conductor_weights.pt"
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on {device}...")
    
    # 1. Initialize the pipeline
    encoder, conductor = get_conductor_pipeline(use_pretrained=use_pretrained, device=device)
    
    # We freeze the encoder so we only train the conductor
    for param in encoder.parameters():
        param.requires_grad = False
    
    conductor.train()
    optimizer = optim.Adam(conductor.parameters(), lr=0.001)
    
    # Loss functions for the 4 outputs
    criterion_ce = nn.CrossEntropyLoss()
    criterion_mse = nn.MSELoss()

    print("Starting training loop...")
    for epoch in range(epochs):
        epoch_loss = 0.0
        
        # We simulate a "dataset" by generating random batches on the fly
        # In a real scenario, you'd load your specific biological sequences here.
        sequences = []
        target_progressions = []
        target_patterns = []
        target_velocities = []
        
        for _ in range(batch_size):
            is_anomaly = random.random() < 0.3
            if is_anomaly:
                seq = generate_mutated_dna(window_size)
                target_prog = 1 # Prog B (Minor/Dissonant)
                target_pat = 2  # Arpeggio (Chaotic)
                target_vel = 0.9 # High intensity
            else:
                seq = generate_random_dna(window_size)
                gc = calculate_gc_content(seq)
                target_prog = 0 # Prog A
                
                if gc > 0.55:
                    target_pat = 1 # Broken Chord
                    target_vel = 0.7
                else:
                    target_pat = 0 # Ballad
                    target_vel = 0.4
                    
            sequences.append(seq)
            target_progressions.append(target_prog)
            target_patterns.append(target_pat)
            target_velocities.append(target_vel)

        target_progressions = torch.tensor(target_progressions, dtype=torch.long).to(device)
        target_patterns = torch.tensor(target_patterns, dtype=torch.long).to(device)
        target_velocities = torch.tensor(target_velocities, dtype=torch.float32).unsqueeze(1).to(device)
        
        optimizer.zero_grad()
        
        total_batch_loss = 0
        for i in range(batch_size):
            # Encode biology
            bio_out = encoder(sequences[i])
            embedding = bio_out["embedding"]
            anomaly_score = bio_out["anomaly_score"]
            
            # Forward pass through Conductor (we need logits to calculate loss)
            anomaly_tensor = torch.tensor([[anomaly_score]], dtype=embedding.dtype, device=device)
            x = torch.cat([embedding, anomaly_tensor], dim=1)
            x = conductor.relu(conductor.fc1(x))
            x = conductor.relu(conductor.fc2(x))
            
            progression_logits = conductor.progression_head(x)
            pattern_logits = conductor.pattern_head(x)
            velocity_val = conductor.velocity_head(x)
            
            # Calculate Loss
            loss_prog = criterion_ce(progression_logits, target_progressions[i].unsqueeze(0))
            loss_pat = criterion_ce(pattern_logits, target_patterns[i].unsqueeze(0))
            loss_vel = criterion_mse(velocity_val, target_velocities[i].unsqueeze(0))
            
            loss = loss_prog + loss_pat + loss_vel
            total_batch_loss += loss

        # Average loss and backprop
        total_batch_loss = total_batch_loss / batch_size
        total_batch_loss.backward()
        optimizer.step()
        
        epoch_loss += total_batch_loss.item()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss:.4f}")

    # Save weights
    torch.save(conductor.state_dict(), output_path)
    print(f"\nTraining complete! Conductor weights saved to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--use-pretrained", action="store_true", help="Egitimde HuggingFace modelini kullan (daha yavas).")
    parser.add_argument("--output", type=str, default="conductor.pt")
    args = parser.parse_args()
    
    train_conductor(epochs=args.epochs, use_pretrained=args.use_pretrained, output_path=args.output)
