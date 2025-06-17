# Gas Bill PDF Extractor - Sistema di Estrazione Massiva

Un estrattore Python avanzato per l'elaborazione massiva di bollette del gas in formato PDF con output Excel consolidato.

## 🚀 Caratteristiche Principali

- **Elaborazione massiva**: Elabora TUTTI i PDF in una cartella, anche migliaia di file
- **Output Excel obbligatorio**: Un singolo file Excel consolidato con tutti i dati
- **Multiple librerie PDF**: Utilizza 4+ librerie diverse per garantire l'estrazione robusta
- **Colonne dinamiche**: Aggiunge automaticamente nuove colonne per dati extra trovati
- **Sistema di logging discrepanze**: File di log dedicato per errori e dati mancanti
- **Gestione errori avanzata**: Campi vuoti per dati non estratti, nessun blocco del processo
- **Multi-fornitore**: Funziona con bollette di diversi fornitori (ENEL, ENI, A2A, HERA, ecc.)
- **Confidence score avanzato**: Valuta la qualità dell'estrazione con multiple metriche

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

## 🎯 Uso Rapido

### Elaborazione Massiva (Modalità Principale)

```bash
# Elabora TUTTI i PDF in una cartella
python main.py /path/to/cartella_pdf --output-excel risultati.xlsx

# Con script di comodo
python run_extraction.py /path/to/cartella_pdf
```

### Esempio Completo

```bash
# Elabora tutti i PDF nella cartella sample_pdfs
python main.py ./sample_pdfs \
    --output-excel ./output/bollette_complete.xlsx \
    --log-discrepancies ./output/errori.log \
    --log-level INFO
```

## 📊 Output del Sistema

### File Excel Consolidato
- **Una riga per PDF**: Ogni bolletta occupa una riga
- **Colonne dinamiche**: Nuove colonne create automaticamente per dati extra
- **Campi vuoti**: Celle vuote per dati non estratti (nessun errore)
- **Ordinamento**: PDF ordinati per ordine di elaborazione
- **Metadati**: Include nome file, confidence score, metodo di estrazione

### File di Log Discrepanze
- **Solo errori**: Contiene solo PDF con problemi
- **Dati mancanti**: Lista dei campi critici non estratti
- **Errori tecnici**: Eccezioni durante l'elaborazione
- **Bassa confidence**: PDF con punteggio qualità < 50%

## 🔧 Librerie di Estrazione

Il sistema utilizza 4 librerie PDF in parallelo:

1. **PDFPlumber**: Estrazione testo e tabelle di alta qualità
2. **PyPDF2**: Estrazione testo classica e robusta  
3. **PyMuPDF (fitz)**: Estrazione avanzata con OCR
4. **PDFMiner**: Estrazione low-level per PDF difficili
5. **Tabula**: Estrazione tabelle specializzata
6. **Camelot**: Estrazione tabelle con riconoscimento struttura

### Sistema di Selezione Automatica
- Valuta la qualità di ogni estrazione
- Seleziona automaticamente il metodo migliore
- Combina risultati per massimizzare i dati estratti

## 📋 Campi Estratti

### Informazioni Cliente
- Nome e cognome
- Indirizzo completo (via, CAP, città, provincia)
- Codice cliente

### Informazioni Contratto
- Numero contratto
- Codice PDR (Punto di Riconsegna)
- Codice REMI
- Matricola contatore

### Informazioni Bolletta
- Numero fattura
- Date (emissione, scadenza, periodo fatturazione)
- Fornitore e Partita IVA

### Consumi
- Letture precedenti e attuali
- Consumo in mc e smc
- Coefficiente di correzione

### Importi
- Importo energia/gas
- Trasporto e distribuzione
- Oneri di sistema
- Accise e IVA
- **Importo totale**

### Metadati
- Nome file PDF
- Timestamp elaborazione
- Confidence score
- Metodo di estrazione utilizzato
- Eventuali errori

## ⚙️ Configurazione Avanzata

### Parametri Linea di Comando

```bash
python main.py CARTELLA_PDF --output-excel FILE.xlsx [OPZIONI]

Opzioni:
  --output-excel FILE     File Excel output (OBBLIGATORIO)
  --log-discrepancies FILE Log per errori e discrepanze  
  --log-level LEVEL       Livello di logging (DEBUG, INFO, WARNING, ERROR)
```

### Gestione Errori

Il sistema è progettato per NON interrompersi mai:

- **PDF corrotti**: Registra errore e continua
- **Dati mancanti**: Lascia celle vuote in Excel
- **Errori di libreria**: Prova libreria successiva
- **Memoria insufficiente**: Elaborazione progressiva

## 🔍 Monitoraggio Qualità

### Confidence Score
- **> 80%**: Estrazione eccellente
- **60-80%**: Estrazione buona  
- **40-60%**: Estrazione sufficiente (verificare log)
- **< 40%**: Estrazione scarsa (controllare PDF)

### Campi Critici Monitorati
- Numero fattura
- Importo totale
- Codice cliente
- Nome cliente
- Consumo mc
- Data emissione
- Fornitore

## 📁 Struttura Output

```
output/
├── bollette_complete.xlsx      # File Excel principale
├── discrepancies_20241217.log  # Log errori con timestamp
└── backup/                     # Backup precedenti (opzionale)
```

## 🚨 Risoluzione Problemi

### PDF Non Elaborati
1. Controllare log discrepanze
2. Verificare che sia un PDF valido
3. Controllare che contenga testo (non solo immagini)

### Dati Mancanti
1. Normale per alcuni PDF con layout diversi
2. Verificare confidence score
3. Aggiungere pattern personalizzati se necessario

### Performance con Molti File
- Il sistema gestisce automaticamente migliaia di file
- Monitorare memoria disponibile per batch molto grandi
- Usare SSD per performance ottimali

## 🔄 Aggiornamenti e Manutenzione

### Aggiungere Nuovi Pattern
Modificare `src/utils/text_processor.py` per pattern specifici del fornitore.

### Personalizzare Output Excel
Modificare `main.py` nella funzione `process_all_pdfs_in_folder()`.

### Estendere Librerie PDF
Aggiungere nuovi metodi in `src/extractors/pdf_extractor.py`.

## 📞 Supporto

Per problemi specifici:
1. Controllare sempre il file di log discrepanze
2. Aumentare log-level a DEBUG per dettagli
3. Fornire file PDF di esempio problematici

---

**Sistema ottimizzato per elaborazione massiva di bollette gas italiane**
