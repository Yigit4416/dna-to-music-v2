from dna_sonifier.bio_encoder import CustomCNNEncoder

encoder = CustomCNNEncoder()
motif = "ACGTGCCG"
window = (motif * 500)[:300]
print("Normal DNA anomaly score:")
print(encoder(window)["anomaly_score"])

import random
mutated = "".join(random.choice("ACGT") for _ in range(300))
print("Mutated DNA anomaly score:")
print(encoder(mutated)["anomaly_score"])
