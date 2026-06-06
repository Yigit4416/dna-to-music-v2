# DNA Sonification Projesi

Bu proje, DNA dizilerini deterministik kurallarla solo piyano müziğine dönüştürmek için geliştirildi. Sistem `music21` kullanarak MIDI ve isteğe bağlı olarak MusicXML üretir; DNA verisini ise yerel FASTA/ham dizi girişinden veya `NCBI` üzerinden accession numarası ile alabilir.

Bu repo, paylaştığınız `DNA Sonification Projesi - Solo Piyano İçin Kural Sistemi (V1.2)` dokümanını çalışan bir Python aracına dönüştürür.

## Projede Neler Yapıldı

- `music21` tabanlı bir solo piyano üretim motoru yazıldı.
- DNA verisini `FASTA`, ham string veya `NCBI accession` üzerinden alabilen bir CLI oluşturuldu.
- Projeye özel bir `.venv` sanal ortamı kuruldu.
- Kurallar dokümandaki gibi deterministik olacak şekilde `SHA-256` tabanlı seçim mekanizmasıyla uygulandı.
- Parça üretiminde tonik, mod, progresyon, tempo, ritim/pattern, melodi ve dinamik kuralları kodlandı.
- `AAA yasağı` ve `kopya ölçü engeli` gibi anti-monotonluk kuralları eklendi.
- MIDI yanında JSON metadata ve MusicXML üretme desteği eklendi.
- Temel doğrulama için test dosyaları eklendi.

## Kullanılan Teknolojiler

- Python 3
- `music21`
- `biopython`
- `NCBI Entrez`

## Proje Yapısı

```text
.
├── .venv/
├── out/
├── src/
│   └── dna_sonifier/
│       ├── __init__.py
│       ├── cli.py
│       ├── ncbi.py
│       └── sonifier.py
├── tests/
│   └── test_sonifier.py
├── pyproject.toml
└── README.md
```

## Kod Nasıl Çalışıyor

Sistem genel olarak şu akışla çalışır:

1. DNA dizisi okunur.
2. Dizi normalize edilir.
   Yalnızca `A`, `C`, `G`, `T` doğrudan kullanılır; belirsiz bazlar `N` olarak normalize edilir.
3. İlk 1200 bazdan tonik seçilir.
4. Sonraki 1200 bazdan mod seçilir.
5. İlk 1200 bazdaki purin oranına göre progresyon seçilir.
6. Tüm DNA için entropy hesaplanır ve BPM belirlenir.
7. DNA, pencereleme mantığıyla ölçülere bölünür.
8. Her pencere için:
   - akor belirlenir,
   - energy hesabıyla pattern seçilir,
   - strength hesabıyla velocity seçilir,
   - melodi notaları üretilir,
   - anti-monotonluk kuralları uygulanır.
9. Sol el ve sağ el partileri oluşturulur.
10. Çıktı olarak MIDI, isteğe bağlı olarak MusicXML ve JSON metadata yazılır.

## Uygulanan Müzikal Kurallar

### 1. Kimlik Kuralları

- Tonik: `DNA[0:1200] -> SHA256 mod 12`
- Mod: `DNA[1200:2400] -> SHA256 mod 4`
- Aynı DNA girdisi her zaman aynı tonik ve modu üretir.

### 2. Harmoni

Kullanılan progresyonlar yalnızca şunlardır:

- `Prog A = I - vi - IV - V`
- `Prog B = vi - IV - I - V`

Seçim:

- `purine_ratio < 0.50` ise `Prog A`
- `purine_ratio >= 0.50` ise `Prog B`

### 3. Tempo

Global entropy değerine göre tempo seçilir:

- `0.00 - 0.33` -> `80 BPM`
- `0.33 - 0.66` -> `92 BPM`
- `0.66 - 1.00` -> `104 BPM`

### 4. Pattern

Her ölçü için pencere bazlı `energy` skoruna göre pattern seçilir:

- `P1`: Ballad
- `P2`: Broken Chord
- `P3`: Arpeggio

### 5. Melodi

Her ölçüde 4 ana beat için melodi notaları üretilir:

- Beat 1 ve 3: ağırlıklı olarak akor tonu
- Beat 2 ve 4: ağırlıklı olarak geçiş tonu

Melodik hareket deterministiktir:

- step büyüklüğü: `1 - 5`
- yön: yukarı veya aşağı

### 6. Anti-Monotonluk

- Aynı nota 3 kez üst üste gelirse üçüncü nota gam içinde kaydırılır.
- Ardışık iki ölçü aynı imzaya sahipse küçük varyasyon uygulanır:
  - Beat 2 notası kaydırılır
  - Beat 4 ritmi iki sekizliğe bölünür

## Kaynak Kod Dosyaları

### `src/dna_sonifier/sonifier.py`

Ana üretim motorudur. Şunları yapar:

- DNA'yı normalize eder
- Kimlik bilgilerini çıkarır
- Entropy, energy, strength skorlarını hesaplar
- Sol el ve sağ el partilerini oluşturur
- MIDI üretimi için `music21` score yapısını kurar

### `src/dna_sonifier/ncbi.py`

NCBI üzerinden accession ile DNA çekmek için kullanılır.

- `Entrez.efetch(...)` ile FASTA verisi alınır
- dönen kayıt içinden sekans çıkarılır

### `src/dna_sonifier/cli.py`

Komut satırı arayüzüdür.

Şunları destekler:

- dosyadan DNA okuma
- doğrudan komut satırından DNA string alma
- NCBI accession ile veri çekme
- MIDI, MusicXML ve JSON çıktı üretme

## Kurulum

Bu projede sanal ortam kullanılır.

### 1. Sanal ortamı oluştur

```bash
python3 -m venv .venv
```

### 2. Sanal ortamı aktif et

```bash
source .venv/bin/activate
```

### 3. Paketleri kur

```bash
pip install --upgrade pip
pip install -e .
```

## Nasıl Çalıştırılır

### Seçenek 1: Yerel FASTA dosyası ile

```bash
source .venv/bin/activate
dna-sonify --input path/to/sequence.fasta --output out/output.mid
```

### Seçenek 2: Ham DNA dizisi ile

```bash
source .venv/bin/activate
dna-sonify --sequence ACGTGCAATGCCACGTGCAATGCC --output out/raw.mid
```

### Seçenek 3: NCBI accession ile

`NCBI` kullanırken email vermek gerekir.

```bash
source .venv/bin/activate
dna-sonify \
  --accession NC_045512.2 \
  --email you@example.com \
  --output out/ncbi.mid
```

## Gelişmiş Kullanım

### JSON metadata ve MusicXML ile birlikte üretim

```bash
source .venv/bin/activate
dna-sonify \
  --input path/to/sequence.fasta \
  --output out/example.mid \
  --metadata-output out/example.json \
  --musicxml-output out/example.musicxml
```

### Add9 süslemesini açmak

```bash
source .venv/bin/activate
dna-sonify \
  --input path/to/sequence.fasta \
  --output out/example.mid \
  --enable-add9
```

### Süre, pencere ve stride değiştirmek

```bash
source .venv/bin/activate
dna-sonify \
  --input path/to/sequence.fasta \
  --duration-seconds 180 \
  --window 300 \
  --stride 150 \
  --output out/longer_piece.mid
```

## Komut Satırı Parametreleri

| Parametre            | Açıklama                          |
| -------------------- | --------------------------------- |
| `--input`            | FASTA veya ham DNA içeren dosya   |
| `--sequence`         | Doğrudan ham DNA string           |
| `--accession`        | NCBI accession numarası           |
| `--email`            | NCBI kullanımı için zorunlu email |
| `--api-key`          | İsteğe bağlı NCBI API key         |
| `--ncbi-db`          | Varsayılan `nucleotide`           |
| `--output`           | MIDI çıktı dosyası                |
| `--musicxml-output`  | İsteğe bağlı MusicXML dosyası     |
| `--metadata-output`  | İsteğe bağlı JSON özet dosyası    |
| `--duration-seconds` | Parça süresi                      |
| `--window`           | Ölçü başına DNA pencere boyu      |
| `--stride`           | Örtüşmeli kayma miktarı           |
| `--title`            | Parça başlığı                     |
| `--enable-add9`      | Add9 süslemeyi açar               |

## Örnek Çıktılar

Bu repoda test amaçlı oluşturulmuş örnekler:

- `out/sample.mid`
- `out/sample.json`
- `out/ncbi_sample.mid`
- `out/ncbi_sample.json`

## Test Çalıştırma

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

## Notlar

- `NVBI` yerine doğru kaynak `NCBI` olarak kullanıldı.
- Aynı DNA girdisi aynı müzikal çıktıyı üretir.
- DNA kısa ise parça uzunluğunu doldurmak için dizi deterministik olarak tekrar edilir.
- Ambiguous bazlar analizde sınırlı kullanılır; müzikal kararlar esas olarak `A/C/G/T` üzerinden verilir.

## Kısa Başlangıç

Hızlı deneme için:

```bash
source .venv/bin/activate
dna-sonify \
  --sequence ACGTGCAATGCCACGTGCAATGCCACGTGCAATGCC \
  --duration-seconds 12 \
  --output out/quick_test.mid \
  --metadata-output out/quick_test.json
```

Bu komut çalıştığında:

- `out/quick_test.mid` oluşur
- `out/quick_test.json` oluşur
- terminalde tonik, mod, progresyon, BPM ve ölçü sayısı yazdırılır

agy --conversation=2765be40-76b0-4c13-be53-563e510c746e (or -c)
