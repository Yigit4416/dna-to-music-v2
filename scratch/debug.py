import music21 as m21
score = m21.converter.parse("out/ai_test.mid")
score.show('text')
