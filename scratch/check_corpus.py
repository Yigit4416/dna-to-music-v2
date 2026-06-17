import music21 as m21

bach_paths = m21.corpus.getComposer('bach')
print(f"Found {len(bach_paths)} Bach pieces in music21 corpus.")

if len(bach_paths) > 0:
    first_piece = m21.corpus.parse(bach_paths[0])
    parts = first_piece.getElementsByClass(m21.stream.Part)
    print(f"First piece has {len(parts)} parts.")
    if len(parts) > 0:
        notes = list(parts[0].flatten().getElementsByClass(m21.note.Note))
        print(f"First part has {len(notes)} notes. Example pitch: {notes[0].pitch.midi}")
