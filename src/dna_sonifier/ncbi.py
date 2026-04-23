from __future__ import annotations

from dataclasses import dataclass

from Bio import Entrez, SeqIO


@dataclass(frozen=True)
class NCBIRecord:
    accession: str
    description: str
    sequence: str


def fetch_sequence(accession: str, email: str, db: str = "nucleotide", api_key: str | None = None) -> NCBIRecord:
    if not email:
        raise ValueError("NCBI fetch icin --email gereklidir.")

    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key

    with Entrez.efetch(db=db, id=accession, rettype="fasta", retmode="text") as handle:
        record = SeqIO.read(handle, "fasta")

    return NCBIRecord(
        accession=accession,
        description=record.description,
        sequence=str(record.seq),
    )

