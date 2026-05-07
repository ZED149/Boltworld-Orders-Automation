from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import os


# ── Brand Palette ──────────────────────────────────────────────────────────
INK         = colors.HexColor('#0D0D0D')
STEEL       = colors.HexColor('#0D0D0D')
ACCENT      = colors.HexColor('#2563EB')
DANGER      = colors.HexColor('#DC2626')
MUTED       = colors.HexColor('#6B7280')
RULE        = colors.HexColor('#E5E7EB')
SUCCESS_BG  = colors.HexColor('#EFF6FF')
FAIL_BG     = colors.HexColor('#FEF2F2')
WHITE       = colors.white
OFF_WHITE   = colors.HexColor('#F0EDE8')
TH_BG       = colors.HexColor('#334155')
TH_TEXT     = colors.HexColor('#F8FAFC')


def _base_doc(filepath, title):
    return SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=8*mm,
        rightMargin=8*mm,
        topMargin=8*mm,
        bottomMargin=8*mm,
        title=title,
    )


def _styles():
    return {
        'company': ParagraphStyle(
            'company',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#9CA3AF'),
            leading=12,
            spaceAfter=1,
        ),
        'doc_title': ParagraphStyle(
            'doc_title',
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=WHITE,
            leading=26,
            spaceAfter=2,
        ),
        'doc_subtitle': ParagraphStyle(
            'doc_subtitle',
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#CBD5E1'),
            leading=13,
            alignment=TA_RIGHT,
        ),
        'meta_label': ParagraphStyle(
            'meta_label',
            fontName='Helvetica',
            fontSize=8,
            textColor=MUTED,
            leading=12,
        ),
        'meta_value': ParagraphStyle(
            'meta_value',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=INK,
            leading=12,
        ),
        'section': ParagraphStyle(
            'section',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=MUTED,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
            letterSpacing=1.2,
        ),
        'cell': ParagraphStyle(
            'cell',
            fontName='Helvetica',
            fontSize=8.5,
            textColor=INK,
            leading=11,
        ),
        'cell_bold': ParagraphStyle(
            'cell_bold',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            textColor=INK,
            leading=11,
        ),
        'cell_muted': ParagraphStyle(
            'cell_muted',
            fontName='Helvetica',
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
        'th': ParagraphStyle(
            'th',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=TH_TEXT,
            leading=11,
            letterSpacing=0.6,
        ),
        'footer': ParagraphStyle(
            'footer',
            fontName='Helvetica',
            fontSize=7.5,
            textColor=MUTED,
            leading=10,
            alignment=TA_CENTER,
        ),
        'tag_success': ParagraphStyle(
            'tag_success',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            textColor=ACCENT,
            leading=10,
        ),
        'tag_fail': ParagraphStyle(
            'tag_fail',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            textColor=DANGER,
            leading=10,
        ),
        'summary_num': ParagraphStyle(
            'summary_num',
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=WHITE,
            leading=24,
            alignment=TA_CENTER,
        ),
        'summary_label': ParagraphStyle(
            'summary_label',
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#CBD5E1'),
            leading=11,
            alignment=TA_CENTER,
        ),
        'note': ParagraphStyle(
            'note',
            fontName='Helvetica',
            fontSize=8,
            textColor=MUTED,
            leading=12,
        ),
    }


class _ClickableLogo(Image):
    """
    Image subclass that adds a PDF link annotation over itself
    so the logo is clickable and shows a hand cursor in PDF viewers.
    """
    def __init__(self, path, width, height, url):
        super().__init__(path, width=width, height=height)
        self._url = url

    def draw(self):
        super().draw()
        # Add link annotation over the drawn image area
        self.canv.linkURL(
            self._url,
            (0, 0, self.drawWidth, self.drawHeight),
            relative=1,
        )


def _header_block(story, s, title_text, subtitle_text,
                  generated_at, page_width, logo_path=None):

    LOGO_SIZE = 28 * mm
    LOGO_COL  = LOGO_SIZE + 8 * mm
    RIGHT_COL = page_width - LOGO_COL

    # Logo cell — clickable via _ClickableLogo
    if logo_path and os.path.exists(logo_path):
        logo_cell = _ClickableLogo(
            logo_path,
            width=LOGO_SIZE,
            height=LOGO_SIZE,
            url='https://zed149.com/lander',
        )
    else:
        logo_cell = Paragraph('Z', s['company'])

    # Right cell: company name, title, subtitle stacked
    right_content = [
        Paragraph('ZED MANAGEMENT SYSTEMS', s['company']),
        Spacer(1, 2),
        Paragraph(title_text,    s['doc_title']),
        Spacer(1, 2),
        Paragraph(subtitle_text, s['doc_subtitle']),
    ]

    banner_data = [[ logo_cell, right_content ]]
    banner_tbl  = Table(banner_data, colWidths=[LOGO_COL, RIGHT_COL])
    banner_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), STEEL),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (0,  -1), 6),
        ('RIGHTPADDING',  (0, 0), (0,  -1), 4),
        ('LEFTPADDING',   (1, 0), (1,  -1), 10),
        ('RIGHTPADDING',  (1, 0), (1,  -1), 10),
    ]))
    story.append(banner_tbl)

    # Blue accent stripe
    accent = Table([['']], colWidths=[page_width])
    accent.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), ACCENT),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(accent)

    # Meta bar
    meta_data = [[
        Paragraph('Generated',    s['meta_label']),
        Paragraph('Reference',    s['meta_label']),
        Paragraph('Module',       s['meta_label']),
    ],[
        Paragraph(generated_at,   s['meta_value']),
        Paragraph(f'BWA-{datetime.now().strftime("%Y%m%d%H%M")}', s['meta_value']),
        Paragraph('Order Processing', s['meta_value']),
    ]]
    meta_tbl = Table(meta_data, colWidths=[page_width / 3] * 3)
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('LINEBELOW',     (0, 1), (-1, 1),  0.5, RULE),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 4*mm))


def _summary_cards(story, s, cards, page_width):
    n     = len(cards)
    col_w = page_width / n

    top = Table(
        [[Paragraph(str(c['value']), s['summary_num']) for c in cards]],
        colWidths=[col_w] * n,
    )
    top.setStyle(TableStyle(
        [('BACKGROUND', (i, 0), (i, 0), cards[i]['color']) for i in range(n)] +
        [('TOPPADDING',    (0,0),(-1,-1), 10),
         ('BOTTOMPADDING', (0,0),(-1,-1), 2),
         ('ALIGN',         (0,0),(-1,-1), 'CENTER')]
    ))

    bot = Table(
        [[Paragraph(c['label'], s['summary_label']) for c in cards]],
        colWidths=[col_w] * n,
    )
    bot.setStyle(TableStyle(
        [('BACKGROUND', (i, 0), (i, 0), cards[i]['color']) for i in range(n)] +
        [('TOPPADDING',    (0,0),(-1,-1), 2),
         ('BOTTOMPADDING', (0,0),(-1,-1), 10),
         ('ALIGN',         (0,0),(-1,-1), 'CENTER')]
    ))

    story.append(top)
    story.append(bot)
    story.append(Spacer(1, 5*mm))


def _footer(story, s, page_width, doc_type):
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=RULE))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f'Automatically generated by <b>ZED</b> Management Systems  ·  '
        f'<a href="https://zed149.com/lander" color="#2563EB">zed149.com</a>  ·  '
        f'{doc_type}  ·  Confidential — Internal Use Only',
        s['footer'],
    ))


def _order_table(table_data, col_widths, row_bg):
    row_styles = [
        ('BACKGROUND',    (0, 0), (-1, 0),  TH_BG),
        ('TOPPADDING',    (0, 0), (-1, 0),  8),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 9),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
        ('TOPPADDING',    (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.4, RULE),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for i in range(1, len(table_data)):
        bg = row_bg if i % 2 == 1 else WHITE
        row_styles.append(('BACKGROUND', (0, i), (-1, i), bg))

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(row_styles))
    return tbl


# ── PUBLIC: Failed Orders Report ──────────────────────────────────────────
def generate_failed_report(failed_orders, output_dir, logo_path=None):
    if not failed_orders:
        return None

    os.makedirs(output_dir, exist_ok=True)
    timestamp    = datetime.now().strftime('%d-%m-%Y__%H-%M-%S')
    filepath     = os.path.join(output_dir, f'Failed_Orders_Report__{timestamp}.pdf')
    generated_at = datetime.now().strftime('%d %b %Y, %H:%M:%S')

    doc        = _base_doc(filepath, 'Failed Orders Report')
    s          = _styles()
    story      = []
    page_width = A4[0] - 16 * mm

    _header_block(
        story, s,
        title_text    = 'Failed Orders Report',
        subtitle_text = 'Requires manual processing',
        generated_at  = generated_at,
        page_width    = page_width,
        logo_path     = logo_path,
    )

    _summary_cards(story, s, [
        {'label': 'Orders Failed',   'value': len(failed_orders), 'color': DANGER},
        {'label': 'Action Required', 'value': 'Manual Print',     'color': colors.HexColor('#7F1D1D')},
    ], page_width)

    story.append(Paragraph('FAILED ORDER DETAILS', s['section']))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=RULE))
    story.append(Spacer(1, 2*mm))

    col_widths = [page_width*0.18, page_width*0.15,
                  page_width*0.47, page_width*0.20]

    table_data = [[
        Paragraph('ORDER',   s['th']),
        Paragraph('POST ID', s['th']),
        Paragraph('REASON',  s['th']),
        Paragraph('ACTION',  s['th']),
    ]]
    for o in failed_orders:
        table_data.append([
            Paragraph(o['order_number'],       s['cell_bold']),
            Paragraph(f"post-{o['post_id']}",  s['cell_muted']),
            Paragraph(o['reason'],             s['cell']),
            Paragraph('Manual Print',          s['tag_fail']),
        ])

    story.append(_order_table(table_data, col_widths, FAIL_BG))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'All orders above require manual invoice and packing slip printing. '
        'Please process them at your earliest convenience.',
        s['note'],
    ))
    _footer(story, s, page_width, 'Failed Orders Report')
    doc.build(story)
    print(f"  Failed report saved: {filepath}")
    return filepath


# ── PUBLIC: Success Report ────────────────────────────────────────────────
def generate_success_report(success_orders, output_dir, logo_path=None):
    if not success_orders:
        return None

    os.makedirs(output_dir, exist_ok=True)
    timestamp    = datetime.now().strftime('%d-%m-%Y__%H-%M-%S')
    filepath     = os.path.join(output_dir, f'Downloaded_Orders_Report__{timestamp}.pdf')
    generated_at = datetime.now().strftime('%d %b %Y, %H:%M:%S')

    doc        = _base_doc(filepath, 'Downloaded Orders Report')
    s          = _styles()
    story      = []
    page_width = A4[0] - 16 * mm

    _header_block(
        story, s,
        title_text    = 'Downloaded Orders Report',
        subtitle_text = 'Invoice & packing slip processed',
        generated_at  = generated_at,
        page_width    = page_width,
        logo_path     = logo_path,
    )

    _summary_cards(story, s, [
        {'label': 'Orders Processed',    'value': len(success_orders), 'color': ACCENT},
        {'label': 'Invoices Downloaded', 'value': len(success_orders), 'color': colors.HexColor('#1D4ED8')},
        {'label': 'Packing Slips',       'value': len(success_orders), 'color': colors.HexColor('#1E40AF')},
    ], page_width)

    story.append(Paragraph('PROCESSED ORDER DETAILS', s['section']))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=RULE))
    story.append(Spacer(1, 2*mm))

    col_widths = [page_width*0.22, page_width*0.18,
                  page_width*0.35, page_width*0.25]

    table_data = [[
        Paragraph('ORDER NO.',   s['th']),
        Paragraph('POST ID',     s['th']),
        Paragraph('NOTE MARKED', s['th']),
        Paragraph('STATUS',      s['th']),
    ]]
    for o in success_orders:
        table_data.append([
            Paragraph(o['order_number'],       s['cell_bold']),
            Paragraph(f"post-{o['post_id']}",  s['cell_muted']),
            Paragraph('@ PRINTED',             s['tag_success']),
            Paragraph('Downloaded',            s['tag_success']),
        ])

    story.append(_order_table(table_data, col_widths, SUCCESS_BG))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'All orders above have been successfully downloaded. '
        'Their WooCommerce order notes have been marked with @ PRINTED.',
        s['note'],
    ))
    _footer(story, s, page_width, 'Downloaded Orders Report')
    doc.build(story)
    print(f"  Success report saved: {filepath}")
    return filepath