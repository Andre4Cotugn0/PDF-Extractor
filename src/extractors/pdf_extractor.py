import pdfplumber
import PyPDF2
import pandas as pd
import re
import fitz  # PyMuPDF
import tabula
import camelot
from pdfminer.high_level import extract_text as pdfminer_extract_text
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

from ..models.gas_bill import GasBillData
from ..utils.text_processor import TextProcessor


class BasePDFExtractor(ABC):
    """Classe base per l'estrazione di dati da PDF con multiple librerie"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"File PDF non trovato: {pdf_path}")
    
    @abstractmethod
    def extract_data(self) -> GasBillData:
        """Metodo astratto per estrarre i dati"""
        pass
    
    def extract_text_multi_library(self) -> Dict[str, str]:
        """Estrae testo usando multiple librerie per confronto"""
        texts = {}
        
        # 1. PDFPlumber
        try:
            text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            texts['pdfplumber'] = TextProcessor.clean_text(text)
        except Exception as e:
            self.logger.warning(f"PDFPlumber fallito: {e}")
            texts['pdfplumber'] = ""
        
        # 2. PyPDF2
        try:
            text = ""
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            texts['pypdf2'] = TextProcessor.clean_text(text)
        except Exception as e:
            self.logger.warning(f"PyPDF2 fallito: {e}")
            texts['pypdf2'] = ""
        
        # 3. PyMuPDF (fitz)
        try:
            text = ""
            doc = fitz.open(self.pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            texts['pymupdf'] = TextProcessor.clean_text(text)
        except Exception as e:
            self.logger.warning(f"PyMuPDF fallito: {e}")
            texts['pymupdf'] = ""
        
        # 4. PDFMiner
        try:
            text = pdfminer_extract_text(str(self.pdf_path))
            texts['pdfminer'] = TextProcessor.clean_text(text)
        except Exception as e:
            self.logger.warning(f"PDFMiner fallito: {e}")
            texts['pdfminer'] = ""
        
        return texts
    
    def get_best_text(self) -> Tuple[str, str]:
        """Ottiene il miglior testo estratto e il metodo usato"""
        texts = self.extract_text_multi_library()
        
        # Valuta la qualità di ogni estrazione
        best_text = ""
        best_method = "none"
        best_score = 0
        
        for method, text in texts.items():
            score = self._evaluate_text_quality(text)
            self.logger.debug(f"{method}: {len(text)} caratteri, score: {score:.2f}")
            
            if score > best_score:
                best_score = score
                best_text = text
                best_method = method
        
        self.logger.info(f"Miglior estrazione: {best_method} (score: {best_score:.2f})")
        return best_text, best_method
    
    def _evaluate_text_quality(self, text: str) -> float:
        """Valuta la qualità di un testo estratto"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Lunghezza del testo
        length_score = min(len(text) / 1000, 1.0)
        score += length_score * 0.3
        
        # Presenza di parole chiave importanti
        keywords = ['fattura', 'bolletta', 'cliente', 'importo', 'gas', 'consumo', 'mc', 'euro', '€']
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        keyword_score = keyword_count / len(keywords)
        score += keyword_score * 0.4
        
        # Presenza di pattern numerici (date, importi, codici)
        numeric_patterns = [
            r'\d{2}[/\-\.]\d{2}[/\-\.]\d{4}',  # Date
            r'\d+[,\.]\d{2}',  # Importi
            r'[A-Z0-9]{8,}',   # Codici
        ]
        pattern_count = 0
        for pattern in numeric_patterns:
            if re.search(pattern, text):
                pattern_count += 1
        pattern_score = pattern_count / len(numeric_patterns)
        score += pattern_score * 0.3
        
        return score
    
    def extract_tables_multi_library(self) -> List[pd.DataFrame]:
        """Estrae tabelle usando multiple librerie"""
        all_tables = []
        
        # 1. PDFPlumber
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 1:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df.name = f"pdfplumber_page_{page_num}_table_{table_num}"
                            all_tables.append(df)
        except Exception as e:
            self.logger.warning(f"PDFPlumber tabelle fallito: {e}")
        
        # 2. Tabula
        try:
            tabula_tables = tabula.read_pdf(str(self.pdf_path), pages='all', multiple_tables=True)
            for i, table in enumerate(tabula_tables):
                if not table.empty:
                    table.name = f"tabula_table_{i}"
                    all_tables.append(table)
        except Exception as e:
            self.logger.warning(f"Tabula fallito: {e}")
        
        # 3. Camelot
        try:
            camelot_tables = camelot.read_pdf(str(self.pdf_path), pages='all')
            for i, table in enumerate(camelot_tables):
                df = table.df
                if not df.empty:
                    df.name = f"camelot_table_{i}"
                    all_tables.append(df)
        except Exception as e:
            self.logger.warning(f"Camelot fallito: {e}")
        
        self.logger.info(f"Estratte {len(all_tables)} tabelle totali")
        return all_tables


class GasBillExtractor(BasePDFExtractor):
    """Estrattore specializzato per bollette del gas con multiple librerie"""
    
    def extract_data(self) -> GasBillData:
        """Estrae i dati dalla bolletta del gas usando multiple librerie"""
        # Inizializza il modello dati
        bill_data = GasBillData()
        
        # Estrae il miglior testo disponibile
        text, extraction_method = self.get_best_text()
        bill_data.raw_text = text
        bill_data.pdf_filename = self.pdf_path.name
        bill_data.extraction_timestamp = datetime.now()
        bill_data.extraction_method = extraction_method  # Aggiunge campo metodo
        
        if not text:
            self.logger.warning("Nessun testo estratto dal PDF con nessun metodo")
            return bill_data
        
        # Estrae dati usando tutti i metodi disponibili e li confronta
        extracted_data = self._extract_all_methods(text)
        
        # Popola il modello dati con i migliori risultati
        self._populate_bill_data(bill_data, extracted_data)
        
        # Estrae dati dalle tabelle se disponibili
        self._extract_from_tables_enhanced(bill_data)
        
        # Calcola confidence score migliorato
        bill_data.extraction_confidence = self._calculate_enhanced_confidence(bill_data, extracted_data)
        
        return bill_data
    
    def _extract_all_methods(self, text: str) -> Dict[str, Any]:
        """Estrae dati usando tutti i metodi e li aggrega"""
        extracted = {
            'customer_info': [],
            'codes': [],
            'dates': [],
            'consumption': [],
            'amounts': [],
            'suppliers': []
        }
        
        # Metodo 1: TextProcessor originale
        try:
            customer_info = TextProcessor.extract_customer_info(text)
            extracted['customer_info'].append(('original', customer_info))
            
            codes = {
                'codice_cliente': TextProcessor.extract_code_by_pattern(text, 'codice_cliente'),
                'numero_fattura': TextProcessor.extract_code_by_pattern(text, 'numero_fattura'),
                'codice_pdr': TextProcessor.extract_code_by_pattern(text, 'pdr'),
                'codice_remi': TextProcessor.extract_code_by_pattern(text, 'remi'),
                'matricola_contatore': TextProcessor.extract_code_by_pattern(text, 'matricola_contatore'),
                'fornitore_partita_iva': TextProcessor.extract_code_by_pattern(text, 'partita_iva')
            }
            extracted['codes'].append(('original', codes))
            
            consumption = TextProcessor.extract_consumption_data(text)
            extracted['consumption'].append(('original', consumption))
            
            amounts = TextProcessor.extract_bill_amounts(text)
            extracted['amounts'].append(('original', amounts))
            
            supplier = TextProcessor.identify_supplier(text)
            extracted['suppliers'].append(('original', supplier))
            
        except Exception as e:
            self.logger.error(f"Errore metodo originale: {e}")
        
        # Metodo 2: Pattern più aggressivi
        try:
            enhanced_data = self._extract_enhanced_patterns(text)
            for key, value in enhanced_data.items():
                if key in extracted:
                    extracted[key].append(('enhanced', value))
        except Exception as e:
            self.logger.error(f"Errore metodi enhanced: {e}")
        
        # Metodo 3: Estrazione date migliorata
        try:
            dates = self._extract_dates_enhanced(text)
            extracted['dates'].append(('enhanced', dates))
        except Exception as e:
            self.logger.error(f"Errore estrazione date: {e}")
        
        return extracted
    
    def _extract_enhanced_patterns(self, text: str) -> Dict[str, Any]:
        """Pattern di estrazione più aggressivi e flessibili"""
        enhanced = {}
        
        # Pattern più flessibili per codici
        enhanced_patterns = {
            'codice_cliente': [
                r'(?:cod(?:ice)?\s*client[ei]|client[ei]\s*cod(?:ice)?|cod\.\s*client[ei])[:\s]*([A-Z0-9]{4,20})',
                r'cliente[:\s]*([A-Z0-9]{6,15})',
                r'codice[:\s]*([A-Z0-9]{6,15})'
            ],
            'numero_fattura': [
                r'(?:fattura|bolletta|n[°.]?\s*fattura)\s*(?:n[°.]?\s*)?([A-Z0-9]{6,25})',
                r'documento[:\s]*([A-Z0-9]{8,20})',
                r'riferimento[:\s]*([A-Z0-9]{8,20})'
            ],
            'importo_totale': [
                r'(?:totale|da\s*pagare|importo\s*(?:totale|fattura)|€\s*totale)[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)',
                r'pagare[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)',
                r'saldo[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)'
            ],
            'consumo_mc': [
                r'consumo[:\s]*(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:mc|m³|metri\s*cubi)',
                r'gas\s*consumato[:\s]*(\d{1,6}(?:[.,]\d{1,3})?)',
                r'volume[:\s]*(\d{1,6}(?:[.,]\d{1,3})?)\s*mc'
            ]
        }
        
        codes = {}
        for field, patterns in enhanced_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not codes.get(field):
                    value = match.group(1)
                    if field in ['importo_totale', 'consumo_mc']:
                        try:
                            # Converte i valori numerici
                            value = float(value.replace('.', '').replace(',', '.'))
                        except:
                            continue
                    codes[field] = value
                    break
        
        enhanced['codes'] = codes
        return enhanced
    
    def _extract_dates_enhanced(self, text: str) -> Dict[str, Any]:
        """Estrazione date migliorata"""
        dates = {}
        
        # Pattern per date più flessibili
        date_contexts = {
            'emissione': [
                r'(?:data\s*emissione|emessa\s*il|del)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'emissione[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'fattura\s*del[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
            ],
            'scadenza': [
                r'(?:data\s*scadenza|scade\s*il|entro\s*il|scadenza)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'pagamento\s*entro[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
            ],
            'periodo_inizio': [
                r'(?:dal|periodo\s*dal|fatturazione\s*dal)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'consumi\s*dal[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
            ],
            'periodo_fine': [
                r'(?:al|fino\s*al|periodo\s*al)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'consumi\s*al[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
            ]
        }
        
        for date_type, patterns in date_contexts.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not dates.get(date_type):
                    date_obj = TextProcessor.extract_date(match.group(1))
                    if date_obj:
                        dates[date_type] = date_obj
                        break
        
        return dates
    
    def _populate_bill_data(self, bill_data: GasBillData, extracted_data: Dict[str, Any]) -> None:
        """Popola il modello dati con i migliori risultati estratti"""
        
        # Customer info - prende il primo disponibile
        for method, customer_info in extracted_data.get('customer_info', []):
            if customer_info:
                if not bill_data.cliente_nome and customer_info.get('nome'):
                    bill_data.cliente_nome = customer_info['nome']
                if not bill_data.cliente_cognome and customer_info.get('cognome'):
                    bill_data.cliente_cognome = customer_info['cognome']
                if not bill_data.cliente_indirizzo and customer_info.get('indirizzo'):
                    bill_data.cliente_indirizzo = customer_info['indirizzo']
                if not bill_data.cliente_cap and customer_info.get('cap'):
                    bill_data.cliente_cap = customer_info['cap']
        
        # Codes - confronta e prende il migliore
        all_codes = {}
        for method, codes in extracted_data.get('codes', []):
            for key, value in codes.items():
                if value and (key not in all_codes or not all_codes[key]):
                    all_codes[key] = value
        
        # Assegna i codici al bill_data
        code_mapping = {
            'codice_cliente': 'codice_cliente',
            'numero_fattura': 'numero_fattura',
            'codice_pdr': 'codice_pdr',
            'codice_remi': 'codice_remi',
            'matricola_contatore': 'matricola_contatore',
            'fornitore_partita_iva': 'fornitore_partita_iva',
            'importo_totale': 'importo_totale',
            'consumo_mc': 'consumo_mc'
        }
        
        for key, attr_name in code_mapping.items():
            if all_codes.get(key) and not getattr(bill_data, attr_name):
                setattr(bill_data, attr_name, all_codes[key])
        
        # Dates
        for method, dates in extracted_data.get('dates', []):
            for date_type, date_obj in dates.items():
                attr_name = f'data_{date_type}' if date_type in ['emissione', 'scadenza'] else f'periodo_fatturazione_{date_type}'
                if not getattr(bill_data, attr_name, None):
                    setattr(bill_data, attr_name, date_obj)
        
        # Consumption
        for method, consumption in extracted_data.get('consumption', []):
            for key, value in consumption.items():
                if value and not getattr(bill_data, key, None):
                    setattr(bill_data, key, value)
        
        # Amounts
        for method, amounts in extracted_data.get('amounts', []):
            amount_mapping = {
                'energia': 'importo_energia',
                'trasporto': 'importo_trasporto',
                'oneri_sistema': 'importo_oneri_sistema',
                'accise': 'importo_accise',
                'iva': 'importo_iva',
                'totale': 'importo_totale'
            }
            for key, attr_name in amount_mapping.items():
                if amounts.get(key) and not getattr(bill_data, attr_name):
                    setattr(bill_data, attr_name, amounts[key])
        
        # Suppliers
        for method, supplier in extracted_data.get('suppliers', []):
            if supplier and not bill_data.fornitore_nome:
                bill_data.fornitore_nome = supplier
    
    
    def _extract_from_tables_enhanced(self, bill_data: GasBillData) -> None:
        """Estrae dati dalle tabelle usando multiple librerie"""
        try:
            tables = self.extract_tables_multi_library()
            
            for table in tables:
                if table.empty:
                    continue
                
                self.logger.debug(f"Analizzando tabella: {getattr(table, 'name', 'unnamed')}")
                
                # Cerca dati di consumo nelle tabelle
                self._extract_consumption_from_table_enhanced(table, bill_data)
                
                # Cerca importi nelle tabelle
                self._extract_amounts_from_table_enhanced(table, bill_data)
                
                # Cerca codici nelle tabelle
                self._extract_codes_from_table(table, bill_data)
                
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione da tabelle: {e}")
    
    def _extract_consumption_from_table_enhanced(self, table: pd.DataFrame, bill_data: GasBillData) -> None:
        """Estrazione consumo migliorata dalle tabelle"""
        # Converte tutte le celle in stringhe per l'analisi
        table_str = table.astype(str)
        
        for row_idx, row in table_str.iterrows():
            for col_idx, value in row.items():
                if pd.isna(value) or str(value) == 'nan':
                    continue
                
                value_str = str(value).lower()
                
                # Cerca pattern di consumo
                consumption_patterns = [
                    r'(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:mc|m³)',
                    r'consumo[:\s]*(\d{1,6}(?:[.,]\d{1,3})?)',
                    r'volume[:\s]*(\d{1,6}(?:[.,]\d{1,3})?)'
                ]
                
                for pattern in consumption_patterns:
                    match = re.search(pattern, value_str)
                    if match and not bill_data.consumo_mc:
                        try:
                            bill_data.consumo_mc = float(match.group(1).replace(',', '.'))
                            self.logger.debug(f"Consumo trovato in tabella: {bill_data.consumo_mc}")
                        except ValueError:
                            continue
    
    def _extract_amounts_from_table_enhanced(self, table: pd.DataFrame, bill_data: GasBillData) -> None:
        """Estrazione importi migliorata dalle tabelle"""
        table_str = table.astype(str)
        
        # Mapping di pattern per diversi tipi di importi
        amount_patterns = {
            'importo_totale': [r'totale[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)', 
                              r'da\s*pagare[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)'],
            'importo_energia': [r'energia[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)',
                               r'gas[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)'],
            'importo_trasporto': [r'trasporto[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)',
                                 r'distribuzione[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)'],
            'importo_iva': [r'iva[:\s]*€?\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)']
        }
        
        for row_idx, row in table_str.iterrows():
            for col_idx, value in row.items():
                if pd.isna(value) or str(value) == 'nan':
                    continue
                
                value_str = str(value).lower()
                
                for field_name, patterns in amount_patterns.items():
                    if getattr(bill_data, field_name):  # Skip se già valorizzato
                        continue
                        
                    for pattern in patterns:
                        match = re.search(pattern, value_str)
                        if match:
                            try:
                                amount = float(match.group(1).replace('.', '').replace(',', '.'))
                                setattr(bill_data, field_name, amount)
                                self.logger.debug(f"{field_name} trovato in tabella: {amount}")
                                break
                            except ValueError:
                                continue
    
    def _extract_codes_from_table(self, table: pd.DataFrame, bill_data: GasBillData) -> None:
        """Estrae codici dalle tabelle"""
        table_str = table.astype(str)
        
        code_patterns = {
            'codice_cliente': [r'cliente[:\s]*([A-Z0-9]{6,20})', r'cod\.?\s*client[ei][:\s]*([A-Z0-9]{6,20})'],
            'numero_fattura': [r'fattura[:\s]*([A-Z0-9]{8,25})', r'bolletta[:\s]*([A-Z0-9]{8,25})'],
            'codice_pdr': [r'pdr[:\s]*([0-9]{14})', r'punto\s*riconsegna[:\s]*([0-9]{14})'],
            'matricola_contatore': [r'matricola[:\s]*([A-Z0-9]{6,15})', r'contatore[:\s]*([A-Z0-9]{6,15})']
        }
        
        for row_idx, row in table_str.iterrows():
            for col_idx, value in row.items():
                if pd.isna(value) or str(value) == 'nan':
                    continue
                
                value_str = str(value).lower()
                
                for field_name, patterns in code_patterns.items():
                    if getattr(bill_data, field_name):  # Skip se già valorizzato
                        continue
                        
                    for pattern in patterns:
                        match = re.search(pattern, value_str, re.IGNORECASE)
                        if match:
                            setattr(bill_data, field_name, match.group(1))
                            self.logger.debug(f"{field_name} trovato in tabella: {match.group(1)}")
                            break
    
    def _calculate_enhanced_confidence(self, bill_data: GasBillData, extracted_data: Dict[str, Any]) -> float:
        """Calcola un punteggio di confidenza migliorato"""
        score = 0.0
        total_weight = 0.0
        
        # Campi critici con pesi
        critical_fields = {
            'numero_fattura': 0.20,
            'importo_totale': 0.20,
            'codice_cliente': 0.15,
            'cliente_nome': 0.10,
            'consumo_mc': 0.15,
            'data_emissione': 0.10,
            'fornitore_nome': 0.10
        }
        
        # Valuta campi critici
        for field_name, weight in critical_fields.items():
            total_weight += weight
            value = getattr(bill_data, field_name)
            if value is not None:
                # Bonus se il valore sembra valido
                field_score = weight
                if field_name == 'importo_totale' and isinstance(value, (int, float)) and value > 0:
                    field_score *= 1.1  # Bonus per importi positivi
                elif field_name == 'consumo_mc' and isinstance(value, (int, float)) and 0 < value < 10000:
                    field_score *= 1.1  # Bonus per consumi ragionevoli
                elif field_name in ['numero_fattura', 'codice_cliente'] and len(str(value)) >= 6:
                    field_score *= 1.1  # Bonus per codici di lunghezza adeguata
                
                score += field_score
        
        # Bonus per coerenza tra metodi di estrazione
        consistency_bonus = self._calculate_consistency_bonus(extracted_data)
        score += consistency_bonus * 0.1
        
        # Bonus per qualità del testo estratto
        if hasattr(bill_data, 'extraction_method'):
            method_bonus = {'pdfplumber': 0.05, 'pymupdf': 0.04, 'pypdf2': 0.03, 'pdfminer': 0.02}
            score += method_bonus.get(bill_data.extraction_method, 0)
        
        # Normalizza il punteggio
        normalized_score = min(score / total_weight, 1.0) if total_weight > 0 else 0.0
        
        return normalized_score
    
    def _calculate_consistency_bonus(self, extracted_data: Dict[str, Any]) -> float:
        """Calcola bonus per coerenza tra diversi metodi di estrazione"""
        consistency_score = 0.0
        
        # Controlla coerenza dei codici
        all_codes = extracted_data.get('codes', [])
        if len(all_codes) > 1:
            for field in ['numero_fattura', 'codice_cliente']:
                values = [codes.get(field) for method, codes in all_codes if codes.get(field)]
                if len(set(values)) == 1 and values[0]:  # Tutti uguali e non None
                    consistency_score += 0.2
        
        # Controlla coerenza degli importi
        all_amounts = extracted_data.get('amounts', [])
        if len(all_amounts) > 1:
            for field in ['totale']:
                values = [amounts.get(field) for method, amounts in all_amounts if amounts.get(field)]
                if len(values) > 1:
                    # Se i valori sono simili (differenza < 5%), bonus
                    max_val, min_val = max(values), min(values)
                    if max_val > 0 and (max_val - min_val) / max_val < 0.05:
                        consistency_score += 0.2
        
        return min(consistency_score, 1.0)
