#!/usr/bin/env python3
"""
Esempio di utilizzo dell'estrattore di bollette gas
"""

import sys
from pathlib import Path

# Aggiungi il percorso src al Python path
sys.path.append(str(Path(__file__).parent))

from src.extractors import GasBillExtractor
from src.models import GasBillData
import json


def example_usage():
    """Esempio di utilizzo dell'estrattore"""
    
    # Esempio con un file PDF di prova
    # (sostituisci con il percorso di un vero file PDF)
    pdf_path = "sample_pdfs/bolletta_esempio.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  File di esempio non trovato: {pdf_path}")
        print("Per testare il sistema:")
        print("1. Metti un file PDF di bolletta gas nella cartella 'sample_pdfs/'")
        print("2. Modifica il percorso in questo script")
        print("3. Oppure usa il comando: python main.py /percorso/al/tuo/file.pdf")
        return
    
    try:
        print(f"🔍 Analizzando: {pdf_path}")
        print("-" * 50)
        
        # Crea estrattore
        extractor = GasBillExtractor(pdf_path)
        
        # Estrae dati
        bill_data = extractor.extract_data()
        
        # Mostra risultati
        print("📊 DATI ESTRATTI:")
        print("-" * 30)
        
        if bill_data.cliente_nome:
            print(f"👤 Cliente: {bill_data.cliente_nome} {bill_data.cliente_cognome or ''}")
        
        if bill_data.numero_fattura:
            print(f"🧾 Numero fattura: {bill_data.numero_fattura}")
        
        if bill_data.data_emissione:
            print(f"📅 Data emissione: {bill_data.data_emissione.strftime('%d/%m/%Y')}")
        
        if bill_data.data_scadenza:
            print(f"⏰ Scadenza: {bill_data.data_scadenza.strftime('%d/%m/%Y')}")
        
        if bill_data.importo_totale:
            print(f"💰 Importo totale: €{bill_data.importo_totale:.2f}")
        
        if bill_data.consumo_mc:
            print(f"⛽ Consumo: {bill_data.consumo_mc} mc")
        
        if bill_data.codice_pdr:
            print(f"🏠 PDR: {bill_data.codice_pdr}")
        
        if bill_data.fornitore_nome:
            print(f"🏢 Fornitore: {bill_data.fornitore_nome}")
        
        print(f"\n📈 Confidence: {bill_data.extraction_confidence:.2%}")
        
        # Salva risultato dettagliato
        output_file = "output/esempio_estrazione.json"
        Path("output").mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bill_data.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Risultato completo salvato in: {output_file}")
        
        # Mostra testo estratto (prime 500 caratteri)
        if bill_data.raw_text:
            print(f"\n📝 Testo estratto (anteprima):")
            print("-" * 40)
            print(bill_data.raw_text[:500] + "..." if len(bill_data.raw_text) > 500 else bill_data.raw_text)
        
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_manual_extraction():
    """Demo dell'estrazione manuale di dati"""
    
    print("\n" + "="*60)
    print("🧪 DEMO - Estrazione manuale da testo")
    print("="*60)
    
    # Testo di esempio (simula il contenuto di una bolletta)
    sample_text = """
    ENEL ENERGIA SPA
    Partita IVA: 12345678901
    
    FATTURA N. FT123456789
    Data emissione: 15/05/2024
    Scadenza: 30/06/2024
    
    Intestatario: Mario Rossi
    Via Roma 123
    20121 Milano (MI)
    
    Codice Cliente: CL987654321
    PDR: 12345678901234
    
    Periodo di fornitura: dal 01/04/2024 al 30/04/2024
    
    Consumi:
    Lettura precedente: 1250 mc
    Lettura attuale: 1380 mc
    Consumo: 130 mc
    
    Dettaglio importi:
    Spesa per la materia energia: €45,20
    Spesa per il trasporto: €12,30
    Oneri di sistema: €8,50
    Accise: €15,60
    IVA 22%: €18,02
    
    TOTALE DA PAGARE: €99,62
    """
    
    from src.utils import TextProcessor
    
    print("📝 Testo di esempio elaborato:")
    print("-" * 40)
    
    # Test estrazione importi
    amounts = TextProcessor.extract_bill_amounts(sample_text)
    print("💰 Importi trovati:")
    for key, value in amounts.items():
        if value:
            print(f"  - {key.title()}: €{value:.2f}")
    
    # Test estrazione codici
    print("\n🔢 Codici trovati:")
    codes = ['codice_cliente', 'numero_fattura', 'pdr', 'partita_iva']
    for code in codes:
        value = TextProcessor.extract_code_by_pattern(sample_text, code)
        if value:
            print(f"  - {code.replace('_', ' ').title()}: {value}")
    
    # Test estrazione informazioni cliente
    print("\n👤 Info cliente:")
    customer_info = TextProcessor.extract_customer_info(sample_text)
    for key, value in customer_info.items():
        if value:
            print(f"  - {key.title()}: {value}")
    
    # Test identificazione fornitore
    supplier = TextProcessor.identify_supplier(sample_text)
    if supplier:
        print(f"\n🏢 Fornitore identificato: {supplier}")


if __name__ == "__main__":
    print("🔬 GAS BILL PDF EXTRACTOR - Esempio d'uso")
    print("="*50)
    
    # Demo con file PDF (se disponibile)
    example_usage()
    
    # Demo con testo di esempio
    demo_manual_extraction()
    
    print("\n" + "="*50)
    print("✅ Demo completata!")
    print("\nPer usare il sistema:")
    print("  python main.py /percorso/al/tuo/file.pdf")
    print("  python main.py cartella_con_pdf/ --recursive")
    print("  python main.py file.pdf --excel risultati.xlsx")
