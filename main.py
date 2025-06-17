#!/usr/bin/env python3
"""
Gas Bill PDF Extractor
Estrattore di dati da bollette del gas in formato PDF
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from src.extractors import GasBillExtractor
from src.models import GasBillData


def setup_logging(level: str = "INFO") -> None:
    """Configura il logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def process_single_pdf(pdf_path: str, output_dir: str = "output") -> Dict[str, Any]:
    """Elabora un singolo file PDF"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Elaborazione file: {pdf_path}")
        
        # Crea estrattore
        extractor = GasBillExtractor(pdf_path)
        
        # Estrae dati
        bill_data = extractor.extract_data()
        
        # Prepara risultato
        result = {
            'file': pdf_path,
            'success': True,
            'confidence': bill_data.extraction_confidence,
            'data': bill_data.to_dict(),
            'error': None
        }
        
        # Salva risultato
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        pdf_name = Path(pdf_path).stem
        
        # Salva come JSON
        json_file = output_path / f"{pdf_name}_extracted.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Dati salvati in: {json_file}")
        logger.info(f"Confidence score: {bill_data.extraction_confidence:.2%}")
        
        return result
        
    except Exception as e:
        logger.error(f"Errore nell'elaborazione di {pdf_path}: {e}")
        return {
            'file': pdf_path,
            'success': False,
            'confidence': 0.0,
            'data': None,
            'error': str(e)
        }


def process_multiple_pdfs(pdf_paths: List[str], output_dir: str = "output") -> List[Dict[str, Any]]:
    """Elabora multipli file PDF"""
    logger = logging.getLogger(__name__)
    results = []
    
    for pdf_path in pdf_paths:
        result = process_single_pdf(pdf_path, output_dir)
        results.append(result)
    
    # Crea report riassuntivo
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    logger.info(f"Elaborazione completata:")
    logger.info(f"  - File elaborati con successo: {len(successful)}")
    logger.info(f"  - File con errori: {len(failed)}")
    
    if successful:
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        logger.info(f"  - Confidence medio: {avg_confidence:.2%}")
    
    # Salva report riassuntivo
    output_path = Path(output_dir)
    summary_file = output_path / "extraction_summary.json"
    summary = {
        'total_files': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'average_confidence': sum(r['confidence'] for r in successful) / len(successful) if successful else 0,
        'results': results
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Report salvato in: {summary_file}")
    
    return results


def export_to_excel(results: List[Dict[str, Any]], output_file: str) -> None:
    """Esporta i risultati in un file Excel"""
    logger = logging.getLogger(__name__)
    
    # Prepara dati per Excel
    excel_data = []
    for result in results:
        if result['success'] and result['data']:
            row = result['data'].copy()
            row['pdf_filename'] = result['file']
            row['extraction_confidence'] = result['confidence']
            excel_data.append(row)
    
    if excel_data:
        df = pd.DataFrame(excel_data)
        df.to_excel(output_file, index=False)
        logger.info(f"Dati esportati in Excel: {output_file}")
    else:
        logger.warning("Nessun dato da esportare in Excel")


def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(
        description="Estrattore di dati da bollette del gas in PDF"
    )
    
    parser.add_argument(
        'input', 
        nargs='+',
        help='File PDF o cartella contenente PDF da elaborare'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='Cartella di output (default: output)'
    )
    
    parser.add_argument(
        '-l', '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Livello di logging (default: INFO)'
    )
    
    parser.add_argument(
        '--excel',
        help='Esporta risultati in un file Excel'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Cerca PDF ricorsivamente nelle sottocartelle'
    )
    
    args = parser.parse_args()
    
    # Configura logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Trova file PDF
    pdf_files = []
    for input_path in args.input:
        path = Path(input_path)
        
        if path.is_file() and path.suffix.lower() == '.pdf':
            pdf_files.append(str(path))
        elif path.is_dir():
            pattern = '**/*.pdf' if args.recursive else '*.pdf'
            pdf_files.extend([str(p) for p in path.glob(pattern)])
        else:
            logger.warning(f"Percorso non valido o non è un PDF: {input_path}")
    
    if not pdf_files:
        logger.error("Nessun file PDF trovato")
        sys.exit(1)
    
    logger.info(f"Trovati {len(pdf_files)} file PDF da elaborare")
    
    # Elabora file
    if len(pdf_files) == 1:
        results = [process_single_pdf(pdf_files[0], args.output)]
    else:
        results = process_multiple_pdfs(pdf_files, args.output)
    
    # Esporta in Excel se richiesto
    if args.excel:
        export_to_excel(results, args.excel)
    
    # Mostra statistiche finali
    successful = [r for r in results if r['success']]
    logger.info(f"\n=== RISULTATI FINALI ===")
    logger.info(f"File elaborati: {len(results)}")
    logger.info(f"Successi: {len(successful)}")
    logger.info(f"Errori: {len(results) - len(successful)}")
    
    if successful:
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        logger.info(f"Confidence medio: {avg_confidence:.2%}")


if __name__ == '__main__':
    main()
