import random

# Normal DNA: A stable repeating motif
motif = "ACGTGCCG"
normal_dna = (motif * 500)[:3000]

with open("data/normal_human.fasta", "w") as f:
    f.write(">Normal_Human_DNA\n")
    f.write(normal_dna)

# Mutated DNA: Same, but with a massive chunk of chaotic entropy in the middle
mutated_dna = list(normal_dna)
# Insert mutation at base 1500 to 2000
for i in range(1500, 2000):
    mutated_dna[i] = random.choice(["A", "C", "G", "T"])
mutated_dna = "".join(mutated_dna)

with open("data/mutated_human.fasta", "w") as f:
    f.write(">Mutated_Human_DNA\n")
    f.write(mutated_dna)
    
print("Created normal and mutated DNA fasta files.")
