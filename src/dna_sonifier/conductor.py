import torch
import torch.nn as nn

class AIConductor(nn.Module):
    """
    The Conductor receives biological embeddings and anomaly scores from the BioEncoder
    and translates them into musical parameters for the rule-based engine.
    """
    def __init__(self, input_dim: int = 256, num_progressions: int = 2, num_patterns: int = 3):
        super().__init__()
        
        # A simple feed-forward network to process the sequence embeddings
        self.fc1 = nn.Linear(input_dim + 1, 128) # +1 for anomaly_score
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, 64)
        
        # "Heads" for different musical decisions
        # 1. Tempo modifier (-1: slow down, 0: keep, 1: speed up)
        self.tempo_head = nn.Linear(64, 3)
        # 2. Harmonic Progression (e.g. Prog A or Prog B)
        self.progression_head = nn.Linear(64, num_progressions)
        # 3. Pattern selection (e.g. Ballad, Broken Chord, Arpeggio)
        self.pattern_head = nn.Linear(64, num_patterns)
        # 4. Energy/Velocity intensity (Continuous value 0 to 1)
        self.velocity_head = nn.Sequential(
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, embedding: torch.Tensor, anomaly_score: float) -> dict:
        """
        embedding: [1, input_dim]
        anomaly_score: float
        """
        # Append anomaly score to the embedding
        anomaly_tensor = torch.tensor([[anomaly_score]], dtype=embedding.dtype, device=embedding.device)
        x = torch.cat([embedding, anomaly_tensor], dim=1)
        
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        
        tempo_logits = self.tempo_head(x)
        progression_logits = self.progression_head(x)
        pattern_logits = self.pattern_head(x)
        velocity_val = self.velocity_head(x)
        
        return {
            "tempo_shift": torch.argmax(tempo_logits, dim=-1).item() - 1, # -1, 0, or 1
            "progression_idx": torch.argmax(progression_logits, dim=-1).item(),
            "pattern_idx": torch.argmax(pattern_logits, dim=-1).item(),
            "velocity_mult": velocity_val.item() # 0.0 to 1.0
        }

import os

# Factory function for easy instantiation
def get_conductor_pipeline(use_pretrained: bool = False, device: str = "cpu", weights_path: str = None):
    from .bio_encoder import PretrainedBioEncoder, CustomCNNEncoder
    
    if use_pretrained:
        # Note: input_dim depends on the pretrained model used.
        # Nucleotide-transformer-500m has hidden_dim 1024 typically, adjust if needed.
        encoder = PretrainedBioEncoder(device=device)
        conductor = AIConductor(input_dim=1024).to(device)
    else:
        encoder = CustomCNNEncoder(hidden_dim=256).to(device)
        conductor = AIConductor(input_dim=256).to(device)
        
    if weights_path and os.path.exists(weights_path):
        print(f"[{weights_path}] agirliklari yukleniyor...")
        conductor.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
        
    return encoder, conductor
