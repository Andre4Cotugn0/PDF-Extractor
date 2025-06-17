#!/usr/bin/env python3
"""
Gas Bill PDF Extractor
Estrattore di dati da bollette del gas in formato PDF
Elabora TUTTI i PDF in una cartella e produce un file Excel consolidato
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.extractors import GasBillExtractor
from src.models import GasBillData


def setup_logging(level: str = "INFO", log_file: str = None) -> None:
    """Configura il logging con file per discrepanze"""
    # Include nome del thread per distinguere l'output in parallelo
    log_format = '%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
    
    # Logger principale
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger specifico per discrepanze
    if log_file:
        discrepancy_logger = logging.getLogger('discrepancies')
        discrepancy_handler = logging.FileHandler(log_file, encoding='utf-8')
        discrepancy_handler.setFormatter(logging.Formatter(log_format))
        discrepancy_logger.addHandler(discrepancy_handler)
        discrepancy_logger.setLevel(logging.INFO)


def process_all_pdfs_in_folder(folder_path: str, output_excel: str, log_discrepancies: str = None) -> None:
    """Elabora TUTTI i PDF in una cartella e produce un file Excel consolidato"""
    logger = logging.getLogger(__name__)
    discrepancy_logger = logging.getLogger('discrepancies')
    
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        logger.error(f"La cartella {folder_path} non esiste o non è una cartella")
        sys.exit(1)
    
    # Trova TUTTI i PDF ricorsivamente
    pdf_files = list(folder.rglob("*.pdf"))

    if not pdf_files:
        logger.error(f"Nessun file PDF trovato nella cartella {folder_path}")
        sys.exit(1)

    logger.info(f"Trovati {len(pdf_files)} file PDF da elaborare")

    # Lista per raccogliere tutti i dati
    all_data = []
    processed_count = 0
    error_count = 0

    # Parallel processing: 5 thread, ciascuno lavora su blocchi di 10 PDF
    from concurrent.futures import ThreadPoolExecutor

    def _process_pdf_item(item):
        i, pdf_path = item
        try:
            extractor = GasBillExtractor(str(pdf_path))
            bill_data = extractor.extract_data()
            data_dict = bill_data.to_dict()
            data_dict['pdf_filename'] = pdf_path.name
            data_dict['pdf_path'] = str(pdf_path)
            data_dict['processing_order'] = i

            # Controllo campi critici
            missing_critical_fields = []
            critical_fields = ['numero_fattura', 'importo_totale', 'codice_cliente', 'cliente_nome']
            for field in critical_fields:
                if not data_dict.get(field):
                    missing_critical_fields.append(field)
            if missing_critical_fields:
                discrepancy_logger.warning(
                    f"PDF: {pdf_path.name} - Campi critici mancanti: {', '.join(missing_critical_fields)}"
                )

            # Controllo confidence
            confidence = data_dict.get('extraction_confidence', 0)
            if confidence < 0.5:
                discrepancy_logger.warning(
                    f"PDF: {pdf_path.name} - Bassa confidence: {confidence:.2%}"
                )

            return data_dict, False
        except Exception as e:
            logger.error(f"Errore nell'elaborazione di {pdf_path.name}: {e}")
            discrepancy_logger.error(f"PDF: {pdf_path.name} - Errore: {str(e)}")
            error_dict = {
                'pdf_filename': pdf_path.name,
                'pdf_path': str(pdf_path),
                'processing_order': i,
                'extraction_error': str(e)
            }
            return error_dict, True

    items = list(enumerate(pdf_files, 1))
    with ThreadPoolExecutor(max_workers=5) as executor:
        for data_dict, is_error in executor.map(_process_pdf_item, items, chunksize=10):
            all_data.append(data_dict)
            if is_error:
                error_count += 1
            else:
                processed_count += 1

    logger.info(f"Elaborazione completata: {processed_count} successi, {error_count} errori")
    
    # Crea DataFrame e gestisce colonne dinamiche
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Riordina colonne: campi importanti prima
        important_cols = ['processing_order', 'pdf_filename', 'numero_fattura', 'cliente_nome', 
                         'cliente_cognome', 'codice_cliente', 'importo_totale', 'data_emissione', 
                         'consumo_mc', 'fornitore_nome', 'extraction_confidence']
        
        # Mantieni solo le colonne che esistono effettivamente
        existing_important_cols = [col for col in important_cols if col in df.columns]
        other_cols = [col for col in df.columns if col not in existing_important_cols]
        
        # Riordina DataFrame
        df = df[existing_important_cols + other_cols]
        
        # Salva in Excel
        try:
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Bollette Gas', index=False)
                
                # Formatta il foglio
                worksheet = writer.sheets['Bollette Gas']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Dati esportati in Excel: {output_excel}")
            logger.info(f"Totale righe nel file Excel: {len(df)}")
            logger.info(f"Totale colonne nel file Excel: {len(df.columns)}")
            
        except Exception as e:
            logger.error(f"Errore nella creazione del file Excel: {e}")
            sys.exit(1)
    else:
        logger.error("Nessun dato da esportare")
        sys.exit(1)

def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(
        description="Estrattore di dati da bollette del gas in PDF - Elabora TUTTI i PDF in una cartella"
    )
    
    parser.add_argument(
        'folder', 
        help='Cartella contenente i PDF da elaborare'
    )
    
    parser.add_argument(
        '-o', '--output-excel',
        required=True,
        help='File Excel di output (OBBLIGATORIO)'
    )
    
    parser.add_argument(
        '-l', '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Livello di logging (default: INFO)'
    )
    
    parser.add_argument(
        '--log-discrepancies',
        help='File di log per discrepanze e errori (default: discrepancies.log)'
    )
    
    args = parser.parse_args()
    
    # Imposta file log discrepanze se non specificato
    if not args.log_discrepancies:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.log_discrepancies = f"discrepancies_{timestamp}.log"
    
    # Configura logging
    setup_logging(args.log_level, args.log_discrepancies)
    logger = logging.getLogger(__name__)
    
    logger.info("=== AVVIO ELABORAZIONE MASSIVA PDF ===")
    logger.info(f"Cartella input: {args.folder}")
    logger.info(f"File Excel output: {args.output_excel}")
    logger.info(f"File log discrepanze: {args.log_discrepancies}")
    
    # Verifica che la cartella input esista
    if not Path(args.folder).exists():
        logger.error(f"La cartella {args.folder} non esiste")
        sys.exit(1)
    
    # Verifica che il file Excel abbia l'estensione corretta
    if not args.output_excel.endswith(('.xlsx', '.xls')):
        logger.error("Il file di output deve avere estensione .xlsx o .xls")
        sys.exit(1)
    
    # Crea cartella di output se non esiste
    output_dir = Path(args.output_excel).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Elabora TUTTI i PDF
    try:
        process_all_pdfs_in_folder(args.folder, args.output_excel, args.log_discrepancies)
        logger.info("=== ELABORAZIONE COMPLETATA CON SUCCESSO ===")
    except KeyboardInterrupt:
        logger.warning("Elaborazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Errore generale nell'elaborazione: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
