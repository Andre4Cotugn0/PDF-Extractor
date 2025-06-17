import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser


class TextProcessor:
    """Classe per l'elaborazione e l'estrazione di dati dal testo"""
    
    # Pattern regex per diversi tipi di dati
    PATTERNS = {
        'importo': r'(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
        'codice_cliente': r'(?:cod(?:ice)?\s*client[ei]|client[ei]\s*cod(?:ice)?)[:\s]*([A-Z0-9]{6,20})',
        'numero_fattura': r'(?:fattura|bolletta)\s*n[°.]?\s*([A-Z0-9]{8,20})',
        'pdr': r'(?:PDR|pdr)[:\s]*([0-9]{14})',
        'remi': r'(?:REMI|remi)[:\s]*([0-9A-Z]{8,15})',
        'matricola_contatore': r'(?:matricola|contatore)[:\s]*([A-Z0-9]{6,15})',
        'consumo_mc': r'(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:mc|m³|metri\s*cubi)',
        'consumo_smc': r'(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:smc|sm³|standard\s*metri\s*cubi)',
        'data': r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        'cap': r'\b(\d{5})\b',
        'partita_iva': r'(?:p\.?\s*iva|partita\s*iva)[:\s]*([0-9]{11})',
    }
    
    # Fornitori comuni di gas
    FORNITORI_COMUNI = [
        'ENEL', 'ENI', 'A2A', 'HERA', 'IREN', 'ACEA', 'EDISON', 'SORGENIA',
        'GREEN NETWORK', 'WEKIWI', 'PLENITUDE', 'OCTOPUS', 'ILLUMIA',
        'GAS NATURAL', 'ITALGAS', 'TOSCANA ENERGIA'
    ]
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Pulisce il testo rimuovendo caratteri indesiderati"""
        if not text:
            return ""
        
        # Rimuove caratteri speciali ma mantiene spazi, lettere, numeri e punteggiatura comune
        cleaned = re.sub(r'[^\w\s\.,;:()\-/€°]+', ' ', text)
        # Normalizza spazi multipli
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    @staticmethod
    def extract_monetary_amount(text: str) -> Optional[float]:
        """Estrae un importo monetario dal testo"""
        pattern = r'(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1)
            # Converte formato italiano (1.234,56) in float
            amount_str = amount_str.replace('.', '').replace(',', '.')
            try:
                return float(amount_str)
            except ValueError:
                return None
        return None
    
    @staticmethod
    def extract_date(text: str) -> Optional[datetime]:
        """Estrae una data dal testo"""
        # Pattern per date in formato italiano
        date_patterns = [
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2})',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                day, month, year = match.groups()
                try:
                    # Se l'anno è a 2 cifre, assumiamo 20xx
                    if len(year) == 2:
                        year = '20' + year
                    
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj
                except (ValueError, TypeError):
                    continue
        
        # Prova con il parser di dateutil per formati più flessibili
        try:
            return date_parser.parse(text, dayfirst=True)
        except:
            return None
    
    @staticmethod
    def extract_code_by_pattern(text: str, pattern_name: str) -> Optional[str]:
        """Estrae un codice usando un pattern specifico"""
        if pattern_name not in TextProcessor.PATTERNS:
            return None
        
        pattern = TextProcessor.PATTERNS[pattern_name]
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_customer_info(text: str) -> Dict[str, Optional[str]]:
        """Estrae informazioni del cliente dal testo"""
        info = {
            'nome': None,
            'cognome': None,
            'indirizzo': None,
            'cap': None,
            'citta': None,
            'provincia': None
        }
        
        # Pattern per nome e cognome
        name_patterns = [
            r'(?:intestatario|cliente)[:\s]+([A-Z][a-z]+)\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+([A-Z][a-z]+)(?:\s+via|\s+viale|\s+piazza)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['nome'] = match.group(1)
                info['cognome'] = match.group(2)
                break
        
        # Estrae CAP
        cap_match = re.search(r'\b(\d{5})\b', text)
        if cap_match:
            info['cap'] = cap_match.group(1)
        
        return info
    
    @staticmethod
    def extract_consumption_data(text: str) -> Dict[str, Optional[float]]:
        """Estrae dati di consumo dal testo"""
        consumption = {
            'lettura_precedente': None,
            'lettura_attuale': None,
            'consumo_mc': None,
            'consumo_smc': None
        }
        
        # Pattern per letture contatore
        lettura_patterns = [
            r'(?:lettura\s*precedente|prec\.?)[:\s]*(\d{1,8}(?:[.,]\d{1,3})?)',
            r'(?:lettura\s*attuale|att\.?)[:\s]*(\d{1,8}(?:[.,]\d{1,3})?)',
        ]
        
        # Estrae consumo in metri cubi
        mc_match = re.search(r'(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:mc|m³|metri\s*cubi)', text, re.IGNORECASE)
        if mc_match:
            consumption['consumo_mc'] = float(mc_match.group(1).replace(',', '.'))
        
        # Estrae consumo in standard metri cubi
        smc_match = re.search(r'(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:smc|sm³)', text, re.IGNORECASE)
        if smc_match:
            consumption['consumo_smc'] = float(smc_match.group(1).replace(',', '.'))
        
        return consumption
    
    @staticmethod
    def identify_supplier(text: str) -> Optional[str]:
        """Identifica il fornitore dal testo"""
        for supplier in TextProcessor.FORNITORI_COMUNI:
            if re.search(r'\b' + re.escape(supplier) + r'\b', text, re.IGNORECASE):
                return supplier
        return None
    
    @staticmethod
    def extract_bill_amounts(text: str) -> Dict[str, Optional[float]]:
        """Estrae gli importi della bolletta"""
        amounts = {
            'energia': None,
            'trasporto': None,
            'oneri_sistema': None,
            'accise': None,
            'iva': None,
            'totale': None
        }
        
        # Pattern per diversi tipi di importi
        amount_patterns = {
            'energia': r'(?:energia|gas|materia\s*prima)[:\s]*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            'trasporto': r'(?:trasporto|distribuzione|rete)[:\s]*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            'oneri_sistema': r'(?:oneri\s*sistema|oneri)[:\s]*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            'accise': r'(?:accise|imposte)[:\s]*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            'iva': r'(?:iva|i\.v\.a\.)[:\s]*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            'totale': r'(?:totale|da\s*pagare|importo\s*fattura)[:\s]*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        }
        
        for key, pattern in amount_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    amounts[key] = float(amount_str)
                except ValueError:
                    continue
        
        return amounts
