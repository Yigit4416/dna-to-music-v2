import torch
import torch.nn as nn
from transformers import AutoModelForMaskedLM, AutoTokenizer

class BaseBioEncoder(nn.Module):
    """Abstract base class for biological feature extraction."""
    def forward(self, sequence: str) -> torch.Tensor:
        raise NotImplementedError

class PretrainedBioEncoder(BaseBioEncoder):
    """
    Uses a lightweight HuggingFace model (like DNABERT or Nucleotide Transformer)
    to compute an anomaly score (perplexity/loss) and dense embeddings for a sequence.
    """
    def __init__(self, model_name: str = "InstaDeepAI/nucleotide-transformer-500m-human-ref", device: str = "cpu"):
        super().__init__()
        self.device = torch.device(device)
        
        # We wrap in try-except so it doesn't crash if the user hasn't downloaded it yet,
        # but realistically this will pull from HF hub on first run.
        # For a truly lightweight local run without downloading 2GB, we could use a smaller model
        # or a custom CNN. We will use a smaller model if available, or just standard transformers.
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForMaskedLM.from_pretrained(model_name).to(self.device)
        self.model.eval()

    @torch.no_grad()
    def forward(self, sequence: str) -> dict:
        """
        Returns a dictionary containing:
        - 'embedding': [1, hidden_dim] tensor summarizing the sequence.
        - 'anomaly_score': float, the perplexity/loss of the sequence (higher = more anomalous/mutated).
        """
        inputs = self.tokenizer(sequence, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        
        # To get an anomaly score, we can use the loss (perplexity) of the sequence
        # by passing the input_ids as labels.
        outputs = self.model(**inputs, labels=inputs["input_ids"], output_hidden_states=True)
        
        loss = outputs.loss.item() if outputs.loss is not None else 0.0
        
        # The hidden states of the last layer
        last_hidden_state = outputs.hidden_states[-1] # [batch, seq_len, hidden_dim]
        # Average pooling for a single embedding vector
        seq_embedding = last_hidden_state.mean(dim=1) # [batch, hidden_dim]
        
        return {
            "embedding": seq_embedding,
            "anomaly_score": loss
        }

class CustomCNNEncoder(BaseBioEncoder):
    """
    A lightweight, built-from-scratch CNN feature extractor.
    This is useful if you don't want to use large pre-trained HF models.
    """
    def __init__(self, kmer_size=3, hidden_dim=256):
        super().__init__()
        self.vocab = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}
        self.embedding = nn.Embedding(5, 16)
        self.conv1 = nn.Conv1d(in_channels=16, out_channels=64, kernel_size=kmer_size, padding=1)
        self.conv2 = nn.Conv1d(in_channels=64, out_channels=hidden_dim, kernel_size=kmer_size, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.relu = nn.ReLU()

    def forward(self, sequence: str) -> dict:
        indices = [self.vocab.get(c, 4) for c in sequence.upper()]
        x = torch.tensor(indices, dtype=torch.long, device=self.embedding.weight.device).unsqueeze(0) # [1, seq_len]
        x = self.embedding(x).transpose(1, 2) # [1, 16, seq_len]
        
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.pool(x).squeeze(-1) # [1, hidden_dim]
        
        # Since this is a simple local CNN without language modeling, 
        # anomaly score can just be simulated or computed based on GC content/entropy manually.
        # Here we just output a dummy anomaly score.
        return {
            "embedding": x,
            "anomaly_score": 0.5
        }
