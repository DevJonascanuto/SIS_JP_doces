from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime


# ── Paleta JP Doces ─────────────────────────────────────────────────────────
PINK   = colors.HexColor('#e91e8c')
PURPLE = colors.HexColor('#6a0dad')
DARK   = colors.HexColor('#1a0533')
LIGHT  = colors.HexColor('#f8f0ff')
GRAY   = colors.HexColor('#6b7280')
WHITE  = colors.white
BLACK  = colors.black


def gerar_pdf_pedido(pedido, cliente, itens):
    """Gera PDF profissional do pedido e retorna bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Estilo título ────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=22, textColor=WHITE, alignment=TA_CENTER,
        fontName='Helvetica-Bold', spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#f3d0ff'),
        alignment=TA_CENTER, fontName='Helvetica'
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=9, textColor=GRAY, fontName='Helvetica-Bold'
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=10, textColor=DARK, fontName='Helvetica'
    )
    total_style = ParagraphStyle(
        'Total', parent=styles['Normal'],
        fontSize=14, textColor=WHITE, fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )

    # ── Cabeçalho colorido ───────────────────────────────────────────────────
    header_data = [[
        Paragraph('🍬 JP DOCES', title_style),
        Paragraph(f'PEDIDO Nº {pedido.numero}', title_style),
    ]]
    header_table = Table(header_data, colWidths=[9 * cm, 9 * cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PURPLE),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [PURPLE]),
        ('BOX', (0, 0), (-1, -1), 0, PURPLE),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)

    # linha rosa
    elements.append(HRFlowable(width='100%', thickness=4, color=PINK, spaceAfter=10))

    # ── Informações do pedido ────────────────────────────────────────────────
    data_fmt   = pedido.data.strftime('%d/%m/%Y %H:%M') if pedido.data else '-'
    status_map = {
        'pendente':   'Pendente',
        'confirmado': 'Confirmado',
        'entregue':   'Entregue',
        'cancelado':  'Cancelado',
    }
    status_txt = status_map.get(pedido.status, pedido.status.capitalize())

    info_data = [
        [
            Paragraph('CLIENTE', label_style),
            Paragraph(cliente.nome, value_style),
            Paragraph('DATA', label_style),
            Paragraph(data_fmt, value_style),
        ],
        [
            Paragraph('TELEFONE', label_style),
            Paragraph(cliente.telefone or '-', value_style),
            Paragraph('STATUS', label_style),
            Paragraph(status_txt, value_style),
        ],
        [
            Paragraph('CIDADE/UF', label_style),
            Paragraph(f"{cliente.cidade or '-'} / {cliente.estado or '-'}", value_style),
            Paragraph('CPF/CNPJ', label_style),
            Paragraph(cliente.cpf_cnpj or '-', value_style),
        ],
    ]
    if cliente.email:
        info_data.append([
            Paragraph('E-MAIL', label_style),
            Paragraph(cliente.email, value_style),
            Paragraph('', label_style),
            Paragraph('', value_style),
        ])

    info_table = Table(info_data, colWidths=[3 * cm, 7 * cm, 2.5 * cm, 5.5 * cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2c8ff')),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2c8ff')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Tabela de itens ──────────────────────────────────────────────────────
    th_style = ParagraphStyle(
        'TH', parent=styles['Normal'],
        fontSize=9, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    )
    td_style = ParagraphStyle(
        'TD', parent=styles['Normal'],
        fontSize=9, textColor=DARK, fontName='Helvetica'
    )
    td_right = ParagraphStyle(
        'TDR', parent=styles['Normal'],
        fontSize=9, textColor=DARK, fontName='Helvetica', alignment=TA_RIGHT
    )
    td_center = ParagraphStyle(
        'TDC', parent=styles['Normal'],
        fontSize=9, textColor=DARK, fontName='Helvetica', alignment=TA_CENTER
    )

    table_data = [[
        Paragraph('CÓD', th_style),
        Paragraph('PRODUTO', th_style),
        Paragraph('CATEGORIA', th_style),
        Paragraph('QTD', th_style),
        Paragraph('UN', th_style),
        Paragraph('VL. UNIT.', th_style),
        Paragraph('SUBTOTAL', th_style),
    ]]

    row_colors = []
    for i, item in enumerate(itens, start=1):
        prod = item.produto
        bg = colors.HexColor('#f8f0ff') if i % 2 == 0 else WHITE
        row_colors.append(('BACKGROUND', (0, i), (-1, i), bg))
        table_data.append([
            Paragraph(prod.codigo, td_center),
            Paragraph(prod.nome, td_style),
            Paragraph(prod.categoria, td_center),
            Paragraph(f'{float(item.quantidade):g}', td_center),
            Paragraph(prod.unidade, td_center),
            Paragraph(f'R$ {float(item.preco_unitario):.2f}', td_right),
            Paragraph(f'R$ {float(item.subtotal):.2f}', td_right),
        ])

    items_table = Table(
        table_data,
        colWidths=[2.2 * cm, 5.8 * cm, 2.8 * cm, 1.6 * cm, 1.2 * cm, 2.2 * cm, 2.2 * cm],
        repeatRows=1,
    )
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2c8ff')),
        ('BOX', (0, 0), (-1, -1), 0.8, PURPLE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ] + row_colors
    items_table.setStyle(TableStyle(style_cmds))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3 * cm))

    # ── Totais ───────────────────────────────────────────────────────────────
    desconto  = float(pedido.desconto or 0)
    subtotal  = sum(float(i.subtotal) for i in itens)
    total_val = float(pedido.total or 0)

    totals_data = []
    totals_data.append(['', Paragraph('Subtotal:', label_style), Paragraph(f'R$ {subtotal:.2f}', td_right)])
    if desconto > 0:
        totals_data.append(['', Paragraph('Desconto:', label_style), Paragraph(f'- R$ {desconto:.2f}', td_right)])
    totals_data.append(['', Paragraph('TOTAL GERAL:', ParagraphStyle('TG', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_RIGHT)), Paragraph(f'R$ {total_val:.2f}', ParagraphStyle('TV', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_RIGHT))])

    totals_table = Table(totals_data, colWidths=[9.5 * cm, 4 * cm, 4.5 * cm])
    last_row = len(totals_data) - 1
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, last_row), (-1, last_row), PINK),
        ('BACKGROUND', (0, 0), (-1, last_row - 1), LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, PINK),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(totals_table)

    # ── Observações ──────────────────────────────────────────────────────────
    if pedido.observacoes:
        elements.append(Spacer(1, 0.4 * cm))
        obs_style = ParagraphStyle(
            'Obs', parent=styles['Normal'],
            fontSize=9, textColor=DARK, fontName='Helvetica',
            leftIndent=6, rightIndent=6
        )
        obs_data = [[
            Paragraph('OBSERVAÇÕES:', label_style),
            Paragraph(pedido.observacoes, obs_style),
        ]]
        obs_table = Table(obs_data, colWidths=[3 * cm, 15 * cm])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2c8ff')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(obs_table)

    # ── Rodapé ───────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.6 * cm))
    elements.append(HRFlowable(width='100%', thickness=2, color=PINK, spaceAfter=6))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=GRAY, alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f'JP Doces  •  Documento gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}  •  Obrigado pela preferência! 🍬',
        footer_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
