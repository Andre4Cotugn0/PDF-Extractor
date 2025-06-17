# Gas Bill PDF Extractor

Un estrattore Python avanzato per l'estrazione automatica di dati da bollette del gas in formato PDF.

## 🚀 Caratteristiche

- **Estrazione completa**: Estrae oltre 30 campi dati diversi dalle bollette
- **Multi-fornitore**: Funziona con bollette di diversi fornitori (ENEL, ENI, A2A, HERA, ecc.)
- **Robusto**: Utilizza multiple librerie PDF per massimizzare il successo dell'estrazione
- **Esportazione flessibile**: Output in JSON e Excel
- **Confidence score**: Valuta automaticamente la qualità dell'estrazione
- **Elaborazione batch**: Processa multipli file contemporaneamente

## 📦 Installazione

1. **Clona il repository:**
```bash
git clone [repository-url]
cd "PDF Extractor (EXTRA)"
```

2. **Crea ambiente virtuale:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oppure
.venv\Scripts\activate     # Windows
```

3. **Installa dipendenze:**
```bash
pip install -r requirements.txt
```

## 🔧 Utilizzo

### Elaborazione singolo file
```bash
python main.py bolletta.pdf
```

### Elaborazione multipli file
```bash
python main.py file1.pdf file2.pdf file3.pdf
```

### Elaborazione cartella (ricorsiva)
```bash
python main.py cartella_bollette/ --recursive
```

### Esportazione in Excel
```bash
python main.py bollette/ --excel risultati.xlsx
```

### Opzioni avanzate
```bash
python main.py bollette/ \
    --output cartella_output \
    --excel report.xlsx \
    --log-level DEBUG \
    --recursive
```

## 📊 Dati Estratti

Il sistema estrae automaticamente:

### 👤 Informazioni Cliente
- Nome e cognome
- Codice cliente
- Indirizzo completo (via, CAP, città, provincia)

### 🧾 Informazioni Bolletta
- Numero fattura
- Data emissione
- Data scadenza
- Periodo di fatturazione

### ⛽ Dati Consumo
- Letture contatore (precedente/attuale)
- Consumo in metri cubi (mc)
- Consumo in standard metri cubi (smc)
- Coefficiente C

### 💰 Importi
- Spesa energia/gas
- Spesa trasporto
- Oneri di sistema
- Accise
- IVA
- Totale da pagare

### 🏢 Dati Tecnici
- PDR (Punto di Riconsegna)
- REMI
- Matricola contatore
- Fornitore e P.IVA
- Tariffa applicata

## 📁 Struttura Output

```
output/
├── bolletta1_extracted.json      # Dati estratti singoli
├── bolletta2_extracted.json
├── extraction_summary.json       # Report riassuntivo
└── risultati.xlsx                # Export Excel (opzionale)
```

### Esempio JSON Output
```json
{
  "file": "bolletta_gas_maggio.pdf",
  "success": true,
  "confidence": 0.85,
  "data": {
    "cliente_nome": "Mario",
    "cliente_cognome": "Rossi",
    "numero_fattura": "FT123456789",
    "data_emissione": "2024-05-15T00:00:00",
    "importo_totale": 99.62,
    "consumo_mc": 130.0,
    "codice_pdr": "12345678901234",
    "fornitore_nome": "ENEL"
  }
}
```

## 🧪 Test ed Esempi

### Esegui test
```bash
python tests/test_extractor.py
```

### Prova l'esempio
```bash
python example.py
```

## 🔧 API Programmatica

```python
from src.extractors import GasBillExtractor

# Crea estrattore
extractor = GasBillExtractor("bolletta.pdf")

# Estrai dati
bill_data = extractor.extract_data()

# Accedi ai dati
print(f"Cliente: {bill_data.cliente_nome}")
print(f"Totale: €{bill_data.importo_totale}")
print(f"Confidence: {bill_data.extraction_confidence:.2%}")

# Esporta come dizionario
data_dict = bill_data.to_dict()
```

## 📋 Librerie Utilizzate

- **pdfplumber**: Estrazione testo e tabelle primary
- **PyPDF2**: Estrazione testo backup
- **pandas**: Manipolazione dati e export Excel
- **regex**: Pattern matching avanzato
- **python-dateutil**: Parsing date flessibile
- **camelot-py**: Estrazione tabelle avanzata

## 🐛 Risoluzione Problemi

### PDF non leggibile
```bash
# Prova con log dettagliato
python main.py bolletta.pdf --log-level DEBUG
```

### Confidence basso
- Verifica qualità scan PDF
- Controlla se il fornitore è supportato
- Considera pre-elaborazione OCR per PDF scansionati

### Dati mancanti
- Alcuni fornitori usano formati non standard
- Il sistema è extensibile per nuovi pattern

## 🤝 Contribuire

1. Fork del repository
2. Crea branch feature (`git checkout -b feature/nuova-funzionalita`)
3. Commit modifiche (`git commit -am 'Aggiungi nuova funzionalità'`)
4. Push branch (`git push origin feature/nuova-funzionalita`)
5. Crea Pull Request

## 📝 Licenza

[Specificare licenza]

## 📞 Supporto

Per problemi o domande, aprire un issue su GitHub.

---

**Note**: Questo estrattore è progettato per bollette del gas italiane. Per altri paesi, potrebbero essere necessari adattamenti ai pattern di estrazione.