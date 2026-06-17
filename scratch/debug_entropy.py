import math
from collections import Counter

motif = "ACGTGCCG"
normal_dna = (motif * 500)[:3000]

# Simulate Sonifier window expansion
sequence = normal_dna
expanded = sequence
window_size = 300
stride = 150

windows = [
    expanded[index * stride : index * stride + window_size]
    for index in range(26)
]

for i, w in enumerate(windows):
    counts = Counter(w)
    total = len(w)
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values()) if total > 0 else 0
    print(f"Measure {i+1}: Length {total}, Counts {counts}, Entropy {entropy:.4f}")
