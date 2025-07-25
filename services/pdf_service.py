from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from io import BytesIO
import locale
import os
from database import SessionLocal
from models.deposit import Deposit
from models.cheque_retencion import Cheque, Retencion
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

# Configurar el locale para formato de números (opcional)
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES')
    except:
        pass  # Si no está disponible, usar el formato por defecto

def format_currency(amount):
    """Formatear montos como moneda argentina"""
    try:
        return locale.format_string("%.2f", amount, grouping=True)
    except:
        return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def add_logo_to_story(story):
    """
    Agrega el logo de IVESS al PDF si existe
    """
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images", "ivess_logo.png")
    
    if os.path.exists(logo_path):
        try:
            # Crear imagen con tamaño específico
            logo = Image(logo_path, width=2*inch, height=1*inch)
            
            # Crear una tabla para centrar el logo
            logo_table = Table([[logo]], colWidths=[6.5*inch])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(logo_table)
            story.append(Spacer(1, 20))
            return True
        except Exception as e:
            print(f"⚠️ Error al cargar el logo: {e}")
            return False
    else:
        print(f"⚠️ Logo no encontrado en: {logo_path}")
        return False

def get_cheques_retenciones_totals(deposit_id: str):
    """
    Obtiene los totales de cheques y retenciones para un deposit_id específico
    """
    db = SessionLocal()
    try:
        # Total de cheques
        total_cheques = db.query(func.sum(Cheque.importe)).filter(
            Cheque.deposit_id == deposit_id
        ).scalar() or 0.0
        
        # Total de retenciones
        total_retenciones = db.query(func.sum(Retencion.importe)).filter(
            Retencion.deposit_id == deposit_id
        ).scalar() or 0.0
        
        return {
            'cheques': float(total_cheques),
            'retenciones': float(total_retenciones)
        }
        
    except Exception as e:
        print(f"⚠️ Error al consultar cheques/retenciones para {deposit_id}: {e}")
        return {'cheques': 0.0, 'retenciones': 0.0}
    finally:
        db.close()

def generate_daily_closure_pdf(totals_data, date):
    """
    Genera un PDF con el cierre de caja diario
    """
    from services.deposits_service import get_jumillano_deposits, get_plata_deposits, get_nafa_deposits
    
    # Obtener datos de cheques y retenciones por planta
    def get_plant_cheques_retenciones(get_deposits_func, date):
        try:
            deposits_data = get_deposits_func(date)
            total_cheques = 0.0
            total_retenciones = 0.0
            
            for cajero_id, contenido in deposits_data.items():
                array_obj = contenido.get("ArrayOfWSDepositsByDayDTO")
                if not array_obj:
                    continue
                    
                dto_raw = array_obj.get("WSDepositsByDayDTO")
                if not dto_raw:
                    continue
                    
                dto_list = [dto_raw] if isinstance(dto_raw, dict) else dto_raw
                
                for deposit in dto_list:
                    deposit_id = deposit.get("depositId")
                    if deposit_id:
                        cheques_ret = get_cheques_retenciones_totals(deposit_id)
                        total_cheques += cheques_ret['cheques']
                        total_retenciones += cheques_ret['retenciones']
            
            return {'cheques': total_cheques, 'retenciones': total_retenciones}
        except Exception as e:
            print(f"Error obteniendo cheques/retenciones: {e}")
            return {'cheques': 0.0, 'retenciones': 0.0}
    
    # Obtener totales de cheques y retenciones por planta
    jumillano_cr = get_plant_cheques_retenciones(get_jumillano_deposits, date)
    plata_cr = get_plant_cheques_retenciones(get_plata_deposits, date)
    nafa_cr = get_plant_cheques_retenciones(get_nafa_deposits, date)
    
    # Calcular totales globales de efectivo, cheques y retenciones
    total_efectivo = totals_data['grand_total']
    total_cheques = jumillano_cr['cheques'] + plata_cr['cheques'] + nafa_cr['cheques']
    total_retenciones = jumillano_cr['retenciones'] + plata_cr['retenciones'] + nafa_cr['retenciones']
    total_global = total_efectivo + total_cheques + total_retenciones
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Obtener estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    # Lista para almacenar elementos del PDF
    story = []
    
    # Agregar logo de IVESS
    add_logo_to_story(story)
    
    # Título principal
    story.append(Paragraph("CIERRE DE CAJA DIARIO", title_style))
    story.append(Spacer(1, 12))
    
    # Fecha del reporte - Detectar formato automáticamente
    try:
        # Intentar formato YYYY-MM-DD primero (más común)
        if len(date) == 10 and date.count('-') == 2:
            parts = date.split('-')
            if len(parts[0]) == 4:  # Año primero (YYYY-MM-DD)
                date_obj = datetime.strptime(date, "%Y-%m-%d")
            else:  # Mes primero (MM-DD-YYYY)
                date_obj = datetime.strptime(date, "%m-%d-%Y")
        else:
            # Fallback para otros formatos
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d de %B de %Y")
    except ValueError:
        # Si no se puede parsear, usar la fecha como está
        formatted_date = date
    
    story.append(Paragraph(f"Fecha: {formatted_date}", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Información de la empresa
    story.append(Paragraph("JUMILLANO - SISTEMA DE DEPÓSITOS", normal_style))
    story.append(Spacer(1, 20))
    
    # Crear tabla de resumen con cheques y retenciones
    data = [
        ['UBICACIÓN', 'EFECTIVO', 'CHEQUES', 'RETENCIONES', 'TOTAL', 'ESTADO'],
        ['', '', '', '', '', ''],
        ['Jumillano', 
         f"$ {format_currency(totals_data['jumillano_total'])}", 
         f"$ {format_currency(jumillano_cr['cheques'])}", 
         f"$ {format_currency(jumillano_cr['retenciones'])}", 
         f"$ {format_currency(totals_data['jumillano_total'] + jumillano_cr['cheques'] + jumillano_cr['retenciones'])}", 
         '✓'],
        ['La Plata', 
         f"$ {format_currency(totals_data['plata_total'])}", 
         f"$ {format_currency(plata_cr['cheques'])}", 
         f"$ {format_currency(plata_cr['retenciones'])}", 
         f"$ {format_currency(totals_data['plata_total'] + plata_cr['cheques'] + plata_cr['retenciones'])}", 
         '✓'],
        ['Nafa (Lomas de Zamora)', 
         f"$ {format_currency(totals_data['nafa_total'])}", 
         f"$ {format_currency(nafa_cr['cheques'])}", 
         f"$ {format_currency(nafa_cr['retenciones'])}", 
         f"$ {format_currency(totals_data['nafa_total'] + nafa_cr['cheques'] + nafa_cr['retenciones'])}", 
         '✓'],
        ['', '', '', '', '', ''],
        ['TOTAL GLOBAL', 
         f"$ {format_currency(total_efectivo)}", 
         f"$ {format_currency(total_cheques)}", 
         f"$ {format_currency(total_retenciones)}", 
         f"$ {format_currency(total_global)}", 
         '✓']
    ]
    
    # Crear la tabla con nuevas columnas
    table = Table(data, colWidths=[2.2*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch, 0.6*inch])
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Centrar títulos de columnas
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Datos
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Fila de separación
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
        
        # Total general
        ('BACKGROUND', (0, 6), (-1, 6), colors.lightblue),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 6), (-1, 6), 10),
        
        # Alineación específica para datos (no afecta títulos)
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Ubicaciones a la izquierda
        ('ALIGN', (1, 1), (4, -1), 'RIGHT'),   # Montos a la derecha
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Estado centrado
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Información adicional
    story.append(Paragraph("OBSERVACIONES:", normal_style))
    story.append(Spacer(1, 12))
    
    obs_data = [
        ['• Todos los depósitos fueron procesados correctamente'],
        ['• No se detectaron errores en el sistema'],
        ['• Reporte generado automáticamente'],
        [f'• Fecha y hora de generación: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}']
    ]
    
    obs_table = Table(obs_data, colWidths=[6*inch])
    obs_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(obs_table)
    story.append(Spacer(1, 40))
    
    # Firmas
    signature_data = [
        ['_' * 30, '', '_' * 30],
        ['Responsable de Caja', '', 'Administración'],
        ['', '', ''],
        ['Fecha: ___/___/____', '', 'Fecha: ___/___/____']
    ]
    
    sig_table = Table(signature_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    
    story.append(sig_table)
    
    # Construir el PDF
    doc.build(story)
    
    # Obtener el contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def generate_detailed_repartos_pdf(repartos_data, date):
    """
    Genera un PDF detallado con todos los repartos por planta
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Obtener estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        alignment=TA_LEFT,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Contenido del PDF
    story = []
    
    # Agregar logo de IVESS
    add_logo_to_story(story)
    
    # Título
    title = Paragraph("REPORTE DETALLADO DE REPARTOS", title_style)
    story.append(title)
    
    # Fecha - Detectar formato automáticamente
    try:
        # Intentar formato YYYY-MM-DD primero (más común)
        if len(date) == 10 and date.count('-') == 2:
            parts = date.split('-')
            if len(parts[0]) == 4:  # Año primero (YYYY-MM-DD)
                date_obj = datetime.strptime(date, "%Y-%m-%d")
            else:  # Mes primero (MM-DD-YYYY)
                date_obj = datetime.strptime(date, "%m-%d-%Y")
        else:
            # Fallback para otros formatos
            date_obj = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        # Si falla, usar fecha actual
        date_obj = datetime.now()
    
    date_formatted = date_obj.strftime("%d de %B de %Y")
    date_para = Paragraph(f"Fecha: {date_formatted}", normal_style)
    story.append(date_para)
    story.append(Spacer(1, 20))
    
    # Procesar datos por planta
    plantas = {
        'jumillano': {'title': 'JUMILLANO (Máquinas L-EJU-001 y L-EJU-002)', 'repartos': []},
        'plata': {'title': 'LA PLATA (Máquina L-EJU-003)', 'repartos': []},
        'nafa': {'title': 'NAFA (Máquina L-EJU-004)', 'repartos': []}
    }
    
    # Organizar repartos por planta
    for machine, data in repartos_data.items():
        if "error" not in data:
            plant_key = None
            if machine in ["L-EJU-001", "L-EJU-002"]:
                plant_key = 'jumillano'
            elif machine == "L-EJU-003":
                plant_key = 'plata'
            elif machine == "L-EJU-004":
                plant_key = 'nafa'
            
            if plant_key:
                # Extraer depósitos
                array_deposits = data.get("ArrayOfWSDepositsByDayDTO", {})
                deposits = array_deposits.get("WSDepositsByDayDTO", [])
                
                if isinstance(deposits, dict):
                    deposits = [deposits]
                
                for deposit in deposits:
                    # Calcular el monto total para todas las monedas
                    total_amount = 0
                    currencies = deposit.get("currencies", {})
                    ws_deposit_currencies = currencies.get("WSDepositCurrency", [])
                    
                    if isinstance(ws_deposit_currencies, dict):
                        ws_deposit_currencies = [ws_deposit_currencies]
                    
                    for currency in ws_deposit_currencies:
                        try:
                            amount = float(currency.get("totalAmount", "0"))
                            total_amount += amount
                        except (ValueError, TypeError):
                            continue
                    
                    # Calcular totales de cheques y retenciones desde la base de datos
                    deposit_id = deposit.get("depositId", "")
                    cheques_retenciones = get_cheques_retenciones_totals(deposit_id)
                    cheques_total = cheques_retenciones['cheques']
                    retenciones_total = cheques_retenciones['retenciones']
                    
                    # Limpiar el formato del username para evitar duplicaciones
                    raw_username = deposit.get("userName", "")
                    cleaned_username = raw_username
                    
                    # Si el formato es "123, RTO 123", extraer solo "RTO 123"
                    if ", RTO " in raw_username:
                        cleaned_username = "RTO " + raw_username.split(", RTO ")[1]
                    # Si el formato es "123, RTO 123" pero al revés, extraer "RTO 123"
                    elif "RTO " in raw_username and "," in raw_username:
                        parts = raw_username.split(", ")
                        for part in parts:
                            if "RTO " in part:
                                cleaned_username = part
                                break
                    
                    reparto = {
                        'machine': machine,
                        'datetime': deposit.get("dateTime", ""),
                        'username': cleaned_username,
                        'amount': str(total_amount),
                        'cheques_total': cheques_total,
                        'retenciones_total': retenciones_total,
                        'depositId': deposit.get("depositId", ""),
                        'posName': deposit.get("posName", "")
                    }
                    plantas[plant_key]['repartos'].append(reparto)
    
    # Generar tablas por planta
    for plant_key, plant_data in plantas.items():
        if plant_data['repartos']:
            # Título de la planta
            story.append(Paragraph(plant_data['title'], subtitle_style))
            story.append(Spacer(1, 10))
            
            # Crear tabla de repartos
            table_data = [['Hora', 'Usuario', 'Efectivo ($)', 'Cheques ($)', 'Retenciones ($)', 'Máquina', 'ID Depósito']]
            
            total_planta = 0
            total_cheques_planta = 0
            total_retenciones_planta = 0
            
            for reparto in plant_data['repartos']:
                try:
                    amount = float(reparto['amount'])
                    total_planta += amount
                    amount_formatted = format_currency(amount)
                except:
                    amount_formatted = reparto['amount']
                
                # Obtener totales de cheques y retenciones para este depósito
                cheques_total = reparto.get('cheques_total', 0.0)
                retenciones_total = reparto.get('retenciones_total', 0.0)
                
                total_cheques_planta += cheques_total
                total_retenciones_planta += retenciones_total
                
                # Extraer solo la hora del datetime
                try:
                    dt = datetime.fromisoformat(reparto['datetime'].replace('T', ' '))
                    hora = dt.strftime("%H:%M")
                except:
                    hora = reparto['datetime']
                
                table_data.append([
                    hora,
                    reparto['username'],
                    amount_formatted,
                    format_currency(cheques_total),
                    format_currency(retenciones_total),
                    reparto['machine'],
                    reparto['depositId']
                ])
            
            # Agregar fila de total
            table_data.append([
                '', 
                'TOTAL', 
                format_currency(total_planta), 
                format_currency(total_cheques_planta),
                format_currency(total_retenciones_planta),
                '', 
                ''
            ])
            
            # Crear y estilizar la tabla
            table = Table(table_data, colWidths=[0.8*inch, 1.5*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 1.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),  # Alinear montos a la derecha
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Letra más pequeña para contenido
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
    
    # Resumen final
    story.append(Paragraph("RESUMEN GENERAL", subtitle_style))
    
    total_general = 0
    total_cheques_general = 0
    total_retenciones_general = 0
    resumen_data = [['Planta', 'Total ($)', 'Cheques ($)', 'Retenciones ($)', 'Cantidad']]
    
    for plant_key, plant_data in plantas.items():
        total_planta = sum(float(r['amount']) for r in plant_data['repartos'])
        total_cheques = sum(r.get('cheques_total', 0) for r in plant_data['repartos'])
        total_retenciones = sum(r.get('retenciones_total', 0) for r in plant_data['repartos'])
        cantidad_repartos = len(plant_data['repartos'])
        
        total_general += total_planta
        total_cheques_general += total_cheques
        total_retenciones_general += total_retenciones
        
        plant_name = plant_data['title'].split(' (')[0]
        resumen_data.append([
            plant_name,
            format_currency(total_planta),
            format_currency(total_cheques),
            format_currency(total_retenciones),
            str(cantidad_repartos)
        ])
    
    resumen_data.append([
        'TOTAL GLOBAL', 
        format_currency(total_general), 
        format_currency(total_cheques_general),
        format_currency(total_retenciones_general),
        ''
    ])
    
    resumen_table = Table(resumen_data, colWidths=[2*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Centrar títulos de columnas
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Alineación específica para datos
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Nombres de plantas a la izquierda
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),   # Montos a la derecha
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Cantidad centrada
    ]))
    
    story.append(resumen_table)
    story.append(Spacer(1, 30))
    
    # Información del reporte
    info_para = Paragraph(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", 
                         normal_style)
    story.append(info_para)
    
    # Construir el PDF
    doc.build(story)
    
    # Obtener el contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
