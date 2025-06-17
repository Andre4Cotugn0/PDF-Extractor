import pdfplumber
import PyPDF2
import pandas as pd
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from ..models.gas_bill import GasBillData
from ..utils.text_processor import TextProcessor


class BasePDFExtractor(ABC):
    """Classe base per l'estrazione di dati da PDF"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"File PDF non trovato: {pdf_path}")
    
    @abstractmethod
    def extract_data(self) -> GasBillData:
        """Metodo astratto per estrarre i dati"""
        pass
    
    def extract_text_with_pdfplumber(self) -> str:
        """Estrae tutto il testo usando pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione con pdfplumber: {e}")
        
        return TextProcessor.clean_text(text)
    
    def extract_text_with_pypdf2(self) -> str:
        """Estrae tutto il testo usando PyPDF2"""
        text = ""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione con PyPDF2: {e}")
        
        return TextProcessor.clean_text(text)
    
    def extract_tables_with_pdfplumber(self) -> List[pd.DataFrame]:
        """Estrae le tabelle usando pdfplumber"""
        tables = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables):
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df.name = f"page_{page_num}_table_{table_num}"
                            tables.append(df)
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione tabelle: {e}")
        
        return tables
    
    def get_text_content(self) -> str:
        """Ottiene il contenuto testuale del PDF provando diversi metodi"""
        # Prova prima con pdfplumber
        text = self.extract_text_with_pdfplumber()
        
        # Se pdfplumber non ha estratto abbastanza testo, prova PyPDF2
        if len(text.strip()) < 100:
            text = self.extract_text_with_pypdf2()
        
        return text


class GasBillExtractor(BasePDFExtractor):
    """Estrattore specializzato per bollette del gas"""
    
    def extract_data(self) -> GasBillData:
        """Estrae i dati dalla bolletta del gas"""
        # Inizializza il modello dati
        bill_data = GasBillData()
        
        # Estrae il testo
        text = self.get_text_content()
        bill_data.raw_text = text
        bill_data.pdf_filename = self.pdf_path.name
        bill_data.extraction_timestamp = datetime.now()
        
        if not text:
            self.logger.warning("Nessun testo estratto dal PDF")
            return bill_data
        
        # Estrae informazioni cliente
        customer_info = TextProcessor.extract_customer_info(text)
        bill_data.cliente_nome = customer_info.get('nome')
        bill_data.cliente_cognome = customer_info.get('cognome')
        bill_data.cliente_indirizzo = customer_info.get('indirizzo')
        bill_data.cliente_cap = customer_info.get('cap')
        bill_data.cliente_citta = customer_info.get('citta')
        bill_data.cliente_provincia = customer_info.get('provincia')
        
        # Estrae codici e identificatori
        bill_data.codice_cliente = TextProcessor.extract_code_by_pattern(text, 'codice_cliente')
        bill_data.numero_fattura = TextProcessor.extract_code_by_pattern(text, 'numero_fattura')
        bill_data.codice_pdr = TextProcessor.extract_code_by_pattern(text, 'pdr')
        bill_data.codice_remi = TextProcessor.extract_code_by_pattern(text, 'remi')
        bill_data.matricola_contatore = TextProcessor.extract_code_by_pattern(text, 'matricola_contatore')
        
        # Estrae date
        self._extract_dates(text, bill_data)
        
        # Estrae dati di consumo
        consumption_data = TextProcessor.extract_consumption_data(text)
        bill_data.consumo_mc = consumption_data.get('consumo_mc')
        bill_data.consumo_smc = consumption_data.get('consumo_smc')
        bill_data.lettura_precedente = consumption_data.get('lettura_precedente')
        bill_data.lettura_attuale = consumption_data.get('lettura_attuale')
        
        # Estrae importi
        amounts = TextProcessor.extract_bill_amounts(text)
        bill_data.importo_energia = amounts.get('energia')
        bill_data.importo_trasporto = amounts.get('trasporto')
        bill_data.importo_oneri_sistema = amounts.get('oneri_sistema')
        bill_data.importo_accise = amounts.get('accise')
        bill_data.importo_iva = amounts.get('iva')
        bill_data.importo_totale = amounts.get('totale')
        
        # Identifica fornitore
        bill_data.fornitore_nome = TextProcessor.identify_supplier(text)
        
        # Estrae partita IVA
        bill_data.fornitore_partita_iva = TextProcessor.extract_code_by_pattern(text, 'partita_iva')
        
        # Calcola confidence score
        bill_data.extraction_confidence = self._calculate_confidence(bill_data)
        
        # Estrae dati dalle tabelle se disponibili
        self._extract_from_tables(bill_data)
        
        return bill_data
    
    def _extract_dates(self, text: str, bill_data: GasBillData) -> None:
        """Estrae le date dal testo"""
        # Pattern per identificare diversi tipi di date
        date_patterns = {
            'emissione': r'(?:data\s*emissione|emessa\s*il)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            'scadenza': r'(?:data\s*scadenza|scade\s*il|entro\s*il)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            'periodo_inizio': r'(?:dal|periodo\s*dal)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            'periodo_fine': r'(?:al|fino\s*al)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        }
        
        for date_type, pattern in date_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_obj = TextProcessor.extract_date(match.group(1))
                if date_obj:
                    if date_type == 'emissione':
                        bill_data.data_emissione = date_obj
                    elif date_type == 'scadenza':
                        bill_data.data_scadenza = date_obj
                    elif date_type == 'periodo_inizio':
                        bill_data.periodo_fatturazione_inizio = date_obj
                    elif date_type == 'periodo_fine':
                        bill_data.periodo_fatturazione_fine = date_obj
    
    def _extract_from_tables(self, bill_data: GasBillData) -> None:
        """Estrae dati aggiuntivi dalle tabelle"""
        try:
            tables = self.extract_tables_with_pdfplumber()
            
            for table in tables:
                if table.empty:
                    continue
                
                # Cerca dati di consumo nelle tabelle
                self._extract_consumption_from_table(table, bill_data)
                
                # Cerca importi nelle tabelle
                self._extract_amounts_from_table(table, bill_data)
                
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione da tabelle: {e}")
    
    def _extract_consumption_from_table(self, table: pd.DataFrame, bill_data: GasBillData) -> None:
        """Estrae dati di consumo dalle tabelle"""
        # Cerca colonne che potrebbero contenere dati di consumo
        for col in table.columns:
            if col and any(keyword in str(col).lower() for keyword in ['consumo', 'mc', 'm³', 'lettura']):
                for value in table[col]:
                    if pd.isna(value):
                        continue
                    
                    # Prova a estrarre valori numerici
                    if isinstance(value, (int, float)):
                        if 'consumo' in str(col).lower() and not bill_data.consumo_mc:
                            bill_data.consumo_mc = float(value)
                    elif isinstance(value, str):
                        num_value = TextProcessor.extract_monetary_amount(value)
                        if num_value and 'consumo' in str(col).lower() and not bill_data.consumo_mc:
                            bill_data.consumo_mc = num_value
    
    def _extract_amounts_from_table(self, table: pd.DataFrame, bill_data: GasBillData) -> None:
        """Estrae importi dalle tabelle"""
        for col in table.columns:
            if col and any(keyword in str(col).lower() for keyword in ['importo', 'euro', '€', 'prezzo']):
                for value in table[col]:
                    if pd.isna(value):
                        continue
                    
                    amount = None
                    if isinstance(value, (int, float)):
                        amount = float(value)
                    elif isinstance(value, str):
                        amount = TextProcessor.extract_monetary_amount(value)
                    
                    if amount:
                        # Cerca di categorizzare l'importo basandosi sul contesto
                        col_lower = str(col).lower()
                        if 'totale' in col_lower and not bill_data.importo_totale:
                            bill_data.importo_totale = amount
                        elif 'energia' in col_lower and not bill_data.importo_energia:
                            bill_data.importo_energia = amount
                        elif 'trasporto' in col_lower and not bill_data.importo_trasporto:
                            bill_data.importo_trasporto = amount
    
    def _calculate_confidence(self, bill_data: GasBillData) -> float:
        """Calcola un punteggio di confidenza basato sui dati estratti"""
        score = 0.0
        total_fields = 0
        
        # Campi critici con peso maggiore
        critical_fields = [
            ('numero_fattura', 0.2),
            ('importo_totale', 0.2),
            ('codice_cliente', 0.15),
            ('cliente_nome', 0.1),
            ('consumo_mc', 0.15),
            ('data_emissione', 0.1),
            ('fornitore_nome', 0.1)
        ]
        
        for field_name, weight in critical_fields:
            total_fields += weight
            if getattr(bill_data, field_name) is not None:
                score += weight
        
        return score / total_fields if total_fields > 0 else 0.0
