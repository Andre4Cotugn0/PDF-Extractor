#!/usr/bin/env python3
"""
Test per l'estrattore di bollette gas
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

# Aggiungi src al path
sys.path.append(str(Path(__file__).parent.parent))

from src.models import GasBillData
from src.utils import TextProcessor


class TestTextProcessor(unittest.TestCase):
    """Test per TextProcessor"""
    
    def setUp(self):
        self.sample_text = """
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
        
        Consumo: 130 mc
        Consumo standard: 125 smc
        
        TOTALE DA PAGARE: €99,62
        """
    
    def test_extract_monetary_amount(self):
        """Test estrazione importi monetari"""
        amount = TextProcessor.extract_monetary_amount("€99,62")
        self.assertEqual(amount, 99.62)
        
        amount = TextProcessor.extract_monetary_amount("1.234,56")
        self.assertEqual(amount, 1234.56)
        
        amount = TextProcessor.extract_monetary_amount("nessun importo")
        self.assertIsNone(amount)
    
    def test_extract_date(self):
        """Test estrazione date"""
        date = TextProcessor.extract_date("15/05/2024")
        self.assertEqual(date, datetime(2024, 5, 15))
        
        date = TextProcessor.extract_date("30-06-24")
        self.assertEqual(date, datetime(2024, 6, 30))
    
    def test_extract_code_by_pattern(self):
        """Test estrazione codici"""
        # Test numero fattura
        fattura = TextProcessor.extract_code_by_pattern(self.sample_text, 'numero_fattura')
        self.assertEqual(fattura, 'FT123456789')
        
        # Test codice cliente
        cliente = TextProcessor.extract_code_by_pattern(self.sample_text, 'codice_cliente')
        self.assertEqual(cliente, 'CL987654321')
        
        # Test PDR
        pdr = TextProcessor.extract_code_by_pattern(self.sample_text, 'pdr')
        self.assertEqual(pdr, '12345678901234')
        
        # Test partita IVA
        piva = TextProcessor.extract_code_by_pattern(self.sample_text, 'partita_iva')
        self.assertEqual(piva, '12345678901')
    
    def test_extract_customer_info(self):
        """Test estrazione info cliente"""
        info = TextProcessor.extract_customer_info(self.sample_text)
        self.assertEqual(info['nome'], 'Mario')
        self.assertEqual(info['cognome'], 'Rossi')
        self.assertEqual(info['cap'], '20121')
    
    def test_extract_consumption_data(self):
        """Test estrazione dati consumo"""
        consumption = TextProcessor.extract_consumption_data(self.sample_text)
        self.assertEqual(consumption['consumo_mc'], 130.0)
        self.assertEqual(consumption['consumo_smc'], 125.0)
    
    def test_identify_supplier(self):
        """Test identificazione fornitore"""
        supplier = TextProcessor.identify_supplier(self.sample_text)
        self.assertEqual(supplier, 'ENEL')
    
    def test_extract_bill_amounts(self):
        """Test estrazione importi bolletta"""
        amounts = TextProcessor.extract_bill_amounts(self.sample_text)
        self.assertEqual(amounts['totale'], 99.62)


class TestGasBillData(unittest.TestCase):
    """Test per GasBillData"""
    
    def test_creation(self):
        """Test creazione modello"""
        bill = GasBillData()
        self.assertIsNone(bill.cliente_nome)
        self.assertIsNone(bill.importo_totale)
    
    def test_to_dict(self):
        """Test conversione a dizionario"""
        bill = GasBillData()
        bill.cliente_nome = "Mario"
        bill.importo_totale = 99.62
        bill.data_emissione = datetime(2024, 5, 15)
        
        data = bill.to_dict()
        self.assertEqual(data['cliente_nome'], "Mario")
        self.assertEqual(data['importo_totale'], 99.62)
        self.assertEqual(data['data_emissione'], "2024-05-15T00:00:00")
    
    def test_str_representation(self):
        """Test rappresentazione stringa"""
        bill = GasBillData()
        bill.cliente_nome = "Mario"
        bill.cliente_cognome = "Rossi"
        bill.numero_fattura = "FT123"
        bill.importo_totale = 99.62
        
        str_repr = str(bill)
        self.assertIn("Mario", str_repr)
        self.assertIn("Rossi", str_repr)
        self.assertIn("FT123", str_repr)
        self.assertIn("99.62", str_repr)


class TestCleanText(unittest.TestCase):
    """Test per pulizia testo"""
    
    def test_clean_text(self):
        """Test pulizia testo"""
        dirty_text = "  Testo    con   spazi   multipli  "
        clean = TextProcessor.clean_text(dirty_text)
        self.assertEqual(clean, "Testo con spazi multipli")
        
        dirty_text = "Testo@#$%con^&*caratteri()speciali"
        clean = TextProcessor.clean_text(dirty_text)
        self.assertNotIn("@#$%", clean)
        self.assertNotIn("^&*", clean)


def run_tests():
    """Esegue tutti i test"""
    print("🧪 Esecuzione test...")
    print("=" * 50)
    
    # Crea test suite
    suite = unittest.TestSuite()
    
    # Aggiungi test classes
    test_classes = [
        TestTextProcessor,
        TestGasBillData,
        TestCleanText
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Esegui test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostra risultati
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ Tutti i test sono passati!")
    else:
        print(f"❌ {len(result.failures)} test falliti, {len(result.errors)} errori")
        
        if result.failures:
            print("\nFallimenti:")
            for test, error in result.failures:
                print(f"  - {test}: {error}")
        
        if result.errors:
            print("\nErrori:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
