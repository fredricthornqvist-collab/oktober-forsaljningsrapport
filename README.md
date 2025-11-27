# 📊 Försäljningsrapport Oktober - Fortnox

Interaktiv försäljningsdashboard som analyserar oktober-försäljning med YoY och MoM jämförelser.

## ✨ Features

- 📈 **Nyckeltal** - Ordervärde, Försäljning, Försäljningsantal, Rabatt%
- 📊 **YoY & MoM jämförelser** - Se både årliga och månatliga trender
- 🎯 **Dimensionsanalys** - Kundtyp, Säljkanaler, Kampanjkoder, Bolagsform, SNI med mera
- 🎨 **Fortnox-styling** - Modern design med Fortnox färger och typsnitt
- 📄 **PDF-export** - Optimerad för utskrift och PDF-export

## 🚀 Användning

### Generera Dashboard

```bash
# Installera dependencies
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install pandas numpy

# Generera dashboard
python generera_dashboard.py
```

Detta skapar `oktober_dashboard.html` som kan öppnas direkt i webbläsaren.

### Visa Dashboard

```bash
open oktober_dashboard.html
```

eller dubbelklicka på filen.

## 📁 Projektstruktur

```
oktober-fsg/
├── generera_dashboard.py          # Huvudscript för att generera HTML-dashboard
├── oktober_analys.py               # Textbaserad analysrapport (terminal)
├── oktober_dashboard.html          # Genererad interaktiv dashboard
├── 8520e6e8-926a-4264-b6ad-e545036fe730 - Sheet1.csv  # Försäljningsdata
└── README.md
```

## 📊 Data Format

CSV-filen förväntas ha följande kolumner:
- `ÅrMånad` - Format: YYYYMM (t.ex. 202510)
- `KampanjKod` - Kampanjkod
- `SäljKanal` - Försäljningskanal
- `Antal anställda` - Företagsstorlek
- `Avtalsperiod` - Avtalslängd
- `Bolagsform` - AB, EF, etc.
- `Kundtyp` - FÖRETAG, BYRÅ
- `SNI` - Branschkod
- `Antal försäljningsordrar` - Antal ordrar
- `Försäljning` - Försäljningsbelopp
- `Rabattvärde` - Rabattbelopp

## 🎨 Styling

Dashboarden använder Fortnox färgpalett:
- **Fortnox Green**: #00B888
- **Navy**: #0A2540
- **Typsnitt**: Inter

## 📄 Export till PDF

1. Öppna `oktober_dashboard.html` i Chrome/Safari
2. Tryck `Cmd + P` (Print)
3. Välj "Spara som PDF"
4. Aktivera "Bakgrundsgrafik" för att behålla färger
5. Spara!

## 🔧 Anpassning

För att analysera andra perioder, ändra i `generera_dashboard.py`:

```python
# Ändra perioder här
okt_2025 = filtrera_period(df, 2025, 10)  # Aktuell period
okt_2024 = filtrera_period(df, 2024, 10)  # YoY jämförelse
sep_2025 = filtrera_period(df, 2025, 9)   # MoM jämförelse
```

## 📝 Licens

Internt projekt - Fortnox

## 👤 Författare

Genererad med hjälp av GitHub Copilot
