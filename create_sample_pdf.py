#!/usr/bin/env python3
"""
Crea un PDF di esempio per testare l'estrattore
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from pathlib import Path


def create_sample_gas_bill_pdf():
    """Crea un PDF di esempio di bolletta gas"""
    
    # Crea cartella se non esiste
    Path("sample_pdfs").mkdir(exist_ok=True)
    
    # Crea il documento
    filename = "sample_pdfs/bolletta_esempio.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Intestazione
    story.append(Paragraph("ENEL ENERGIA SPA", title_style))
    story.append(Paragraph("Via della Libertà 123 - 00100 Roma", styles['Normal']))
    story.append(Paragraph("Partita IVA: 12345678901", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Informazioni fattura
    story.append(Paragraph("<b>FATTURA N. FT123456789</b>", styles['Heading2']))
    story.append(Paragraph("Data emissione: 15/05/2024", styles['Normal']))
    story.append(Paragraph("Data scadenza: 30/06/2024", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Dati cliente
    story.append(Paragraph("<b>INTESTATARIO CONTRATTO</b>", styles['Heading3']))
    story.append(Paragraph("Mario Rossi", styles['Normal']))
    story.append(Paragraph("Via Roma 123", styles['Normal']))
    story.append(Paragraph("20121 Milano (MI)", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Dati contratto
    story.append(Paragraph("<b>DATI CONTRATTO</b>", styles['Heading3']))
    contract_data = [
        ["Codice Cliente:", "CL987654321"],
        ["PDR:", "12345678901234"],
        ["REMI:", "REMI12345"],
        ["Matricola Contatore:", "ABC123456"]
    ]
    
    contract_table = Table(contract_data, colWidths=[2*inch, 2*inch])
    contract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(contract_table)
    story.append(Spacer(1, 20))
    
    # Periodo fatturazione
    story.append(Paragraph("<b>PERIODO DI FORNITURA</b>", styles['Heading3']))
    story.append(Paragraph("Dal 01/04/2024 al 30/04/2024", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Consumi
    story.append(Paragraph("<b>CONSUMI</b>", styles['Heading3']))
    consumption_data = [
        ["", "Data", "Lettura", "Consumo"],
        ["Lettura precedente:", "01/04/2024", "1250 mc", ""],
        ["Lettura attuale:", "30/04/2024", "1380 mc", ""],
        ["Consumo effettivo:", "", "", "130 mc"],
        ["Consumo standard:", "", "", "125 smc"]
    ]
    
    consumption_table = Table(consumption_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
    consumption_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(consumption_table)
    story.append(Spacer(1, 20))
    
    # Dettaglio importi
    story.append(Paragraph("<b>DETTAGLIO IMPORTI</b>", styles['Heading3']))
    amounts_data = [
        ["Descrizione", "Importo"],
        ["Spesa per la materia energia", "€45,20"],
        ["Spesa per il trasporto e gestione del contatore", "€12,30"],
        ["Oneri di sistema", "€8,50"],
        ["Accise", "€15,60"],
        ["IVA 22%", "€18,02"],
        ["", ""],
        ["TOTALE DA PAGARE", "€99,62"]
    ]
    
    amounts_table = Table(amounts_data, colWidths=[4*inch, 1.5*inch])
    amounts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black)
    ]))
    story.append(amounts_table)
    
    # Costruisce PDF
    doc.build(story)
    
    print(f"✅ PDF di esempio creato: {filename}")
    return filename


if __name__ == "__main__":
    try:
        pdf_file = create_sample_gas_bill_pdf()
        print(f"\n🔍 Ora puoi testare l'estrattore con:")
        print(f"python main.py {pdf_file}")
        print(f"python example.py")
    except ImportError as e:
        print("❌ Errore: reportlab non installato")
        print("Installa con: pip install reportlab")
    except Exception as e:
        print(f"❌ Errore nella creazione del PDF: {e}")
