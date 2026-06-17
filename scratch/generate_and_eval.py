import subprocess
import re
import os

commands = [
    {
        "name": "Normal Human",
        "cmd": ["python3", "-m", "dna_sonifier.cli", "--input", "data/normal_human.fasta", "--duration-seconds", "60", "--output", "out/normal_human.mid", "--use-ai"]
    },
    {
        "name": "Mutated Human",
        "cmd": ["python3", "-m", "dna_sonifier.cli", "--input", "data/mutated_human.fasta", "--duration-seconds", "60", "--output", "out/mutated_human.mid", "--use-ai"]
    },
    {
        "name": "COVID-19",
        "cmd": ["python3", "-m", "dna_sonifier.cli", "--accession", "NC_045512.2", "--email", "test@example.com", "--duration-seconds", "60", "--output", "out/covid19.mid", "--use-ai"]
    }
]

env = os.environ.copy()
env["PYTHONPATH"] = "src"

for item in commands:
    print(f"--- Generating {item['name']} ---")
    result = subprocess.run(item['cmd'], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error generating {item['name']}:\n{result.stderr}")
        continue
        
    print(result.stdout.strip())
    
    # Extract tonic and mode from output: "Olustu: out/...mid | C major | ..."
    # Note: mode could be "natural_minor", but the CLI prints "Natural Minor (Aeolian)".
    # Wait, the CLI output: "{summary.tonic} {summary.mode} | "
    # In `sonifier.py`: summary.mode is the raw string e.g. "major", "natural_minor".
    # Wait, the CLI does `summary.mode`. So it prints "C major" or "C natural_minor".
    
    match = re.search(r'Olustu:.*?\|\s+([A-G]#?)\s+(\w+(?:_\w+)?)\s+\|', result.stdout)
    if match:
        tonic = match.group(1)
        mode = match.group(2)
        print(f"Evaluated Tonic: {tonic}, Mode: {mode}")
        
        # Run evaluation
        eval_cmd = ["python3", "src/dna_sonifier/evaluate.py", item['cmd'][item['cmd'].index('--output')+1], "--tonic", tonic, "--mode", mode]
        eval_res = subprocess.run(eval_cmd, env=env, capture_output=True, text=True)
        print(eval_res.stdout.strip())
    else:
        print("Could not extract tonic/mode from output.")
        print(result.stdout)
    print("\n")
