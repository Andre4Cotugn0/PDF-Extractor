#!/usr/bin/env python3
"""
Script di esempio per eseguire l'estrazione massiva di PDF
"""

import sys
from pathlib import Path

def main():
    """Esempio di utilizzo del sistema di estrazione"""
    
    # Verifica se è stata specificata una cartella
    if len(sys.argv) < 2:
        print("Uso: python run_extraction.py <cartella_pdf>")
        print("Esempio: python run_extraction.py ./sample_pdfs")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    
    # Nome file Excel basato sulla cartella
    folder_name = Path(input_folder).name
    output_excel = f"output/bollette_{folder_name}_estratte.xlsx"
    log_file = f"output/discrepancies_{folder_name}.log"
    
    # Crea cartella output se non esiste
    Path("output").mkdir(exist_ok=True)
    
    # Costruisce comando
    cmd = [
        sys.executable, "main.py", 
        input_folder,
        "--output-excel", output_excel,
        "--log-discrepancies", log_file,
        "--log-level", "INFO"
    ]
    
    print("=== ESTRATTORE MASSIVO BOLLETTE GAS ===")
    print(f"Cartella input: {input_folder}")
    print(f"File Excel output: {output_excel}")
    print(f"Log discrepanze: {log_file}")
    print(f"Comando: {' '.join(cmd)}")
    print("\nAvvio elaborazione...")
    
    # Esegue il comando
    import subprocess
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n✅ Elaborazione completata con successo!")
        print(f"📊 Risultati salvati in: {output_excel}")
        print(f"📝 Log discrepanze in: {log_file}")
    else:
        print(f"\n❌ Errore durante l'elaborazione (codice: {result.returncode})")
        sys.exit(1)

if __name__ == "__main__":
    main()
