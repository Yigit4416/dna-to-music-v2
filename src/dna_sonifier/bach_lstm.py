import torch
import torch.nn as nn

class BachLSTM(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int = 128, dna_dim: int = 256, hidden_dim: int = 256, num_layers: int = 2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        # The LSTM now takes the note embedding + the dna embedding
        self.lstm = nn.LSTM(embedding_dim + dna_dim, hidden_dim, num_layers=num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, vocab_size)
        
    def forward(self, x, dna_embedding=None, hidden=None):
        # x is [batch_size, seq_len]
        # dna_embedding is [batch_size, dna_dim]
        embeds = self.embedding(x) # [batch_size, seq_len, embedding_dim]
        
        # If no dna_embedding is provided (e.g., legacy code), use zeros
        if dna_embedding is None:
            dna_embedding = torch.zeros(x.size(0), 256, device=x.device)
            
        # Expand dna_embedding to match seq_len: [batch_size, seq_len, dna_dim]
        seq_len = x.size(1)
        dna_expanded = dna_embedding.unsqueeze(1).expand(-1, seq_len, -1)
        
        # Concatenate note embeddings with DNA embeddings
        combined = torch.cat((embeds, dna_expanded), dim=2)
        
        lstm_out, hidden = self.lstm(combined, hidden) # [batch_size, seq_len, hidden_dim]
        logits = self.fc(lstm_out) # [batch_size, seq_len, vocab_size]
        return logits, hidden
