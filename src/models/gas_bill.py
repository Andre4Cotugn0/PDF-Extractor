from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class GasBillData:
    """Modello per i dati estratti da una bolletta del gas"""
    
    # Informazioni cliente
    cliente_nome: Optional[str] = None
    cliente_cognome: Optional[str] = None
    cliente_codice: Optional[str] = None
    cliente_indirizzo: Optional[str] = None
    cliente_cap: Optional[str] = None
    cliente_citta: Optional[str] = None
    cliente_provincia: Optional[str] = None
    
    # Informazioni contratto
    numero_contratto: Optional[str] = None
    codice_cliente: Optional[str] = None
    codice_pdr: Optional[str] = None  # Punto di riconsegna
    codice_remi: Optional[str] = None  # Punto di riconsegna REMI
    
    # Informazioni bolletta
    numero_fattura: Optional[str] = None
    data_emissione: Optional[datetime] = None
    data_scadenza: Optional[datetime] = None
    periodo_fatturazione_inizio: Optional[datetime] = None
    periodo_fatturazione_fine: Optional[datetime] = None
    
    # Consumi
    lettura_precedente: Optional[float] = None
    lettura_attuale: Optional[float] = None
    data_lettura_precedente: Optional[datetime] = None
    data_lettura_attuale: Optional[datetime] = None
    consumo_mc: Optional[float] = None  # metri cubi
    consumo_smc: Optional[float] = None  # standard metri cubi
    coefficiente_c: Optional[float] = None
    
    # Importi
    importo_energia: Optional[float] = None
    importo_trasporto: Optional[float] = None
    importo_oneri_sistema: Optional[float] = None
    importo_accise: Optional[float] = None
    importo_iva: Optional[float] = None
    importo_totale: Optional[float] = None
    importo_ricalcoli: Optional[float] = None
    
    # Tariffe
    tariffa_tipo: Optional[str] = None
    classe_contatore: Optional[str] = None
    
    # Fornitore
    fornitore_nome: Optional[str] = None
    fornitore_partita_iva: Optional[str] = None
    
    # Dati tecnici
    matricola_contatore: Optional[str] = None
    pressione_erogazione: Optional[str] = None
    potere_calorifico: Optional[float] = None
    
    # Metadati estrazione
    pdf_filename: Optional[str] = None
    extraction_timestamp: Optional[datetime] = None
    extraction_confidence: Optional[float] = None
    extraction_method: Optional[str] = None  # Metodo di estrazione usato
    extraction_error: Optional[str] = None  # Errore durante estrazione
    raw_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte l'oggetto in un dizionario"""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, datetime):
                result[field_name] = field_value.isoformat() if field_value else None
            else:
                result[field_name] = field_value
        return result
    
    def __str__(self) -> str:
        return f"GasBillData(cliente: {self.cliente_nome} {self.cliente_cognome}, " \
               f"fattura: {self.numero_fattura}, totale: €{self.importo_totale})"
