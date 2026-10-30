import io
import os
import qrcode
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_ticket_pdf(booking):
    """
    Generates a PDF ticket for a booking using ReportLab,
    complete with customer details, parking information, and a scannable QR code for SmartPark.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    brand_style = ParagraphStyle(
        'BrandTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#0E5E6F'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#0E5E6F'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155'),
        leading=13
    )

    # 1. Header with Brand & Ticket Meta
    story.append(Paragraph("<b>SMARTPARK</b> - Smart Mobility Ticket", brand_style))
    story.append(Paragraph(f"Official Reservation Receipt &bull; Booking Ref: <b>#{booking.booking_id}</b>", subtitle_style))
    story.append(Spacer(1, 10))

    # 2. Generate Scannable QR Code
    qr_data = f"SMARTPARK_GATE_VALIDATION|ID:{booking.booking_id}|LOT:{booking.parking_lot.name}|SLOT:{booking.slot.slot_number}|DATE:{booking.date}"
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=1,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0E5E6F", back_color="white")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    reportlab_qr = Image(qr_buffer, width=1.4 * inch, height=1.4 * inch)

    # 3. Two-Column Table: Reservation Details & QR Code
    info_text = f"""
    <b>Customer:</b> {booking.customer_name or (booking.user.username if booking.user else 'Guest')}<br/>
    <b>Email:</b> {booking.booking_email or (booking.user.email if booking.user else 'N/A')}<br/>
    <b>Phone:</b> {booking.customer_phone or 'N/A'}<br/>
    <b>Vehicle:</b> {booking.vehicle_type.upper()} ({booking.vehicle_number or 'Not Specified'})<br/>
    <br/>
    <b>Parking Facility:</b> {booking.parking_lot.name}<br/>
    <b>Location:</b> {booking.parking_lot.address}, {booking.parking_lot.city} - {booking.parking_lot.pincode}<br/>
    <b>Slot Number:</b> <font color="#0E5E6F"><b>{booking.slot.slot_number}</b></font><br/>
    <b>Date:</b> {booking.date.strftime('%d %B %Y')}<br/>
    <b>Duration:</b> {booking.time_slot_id} ({booking.booking_duration_minutes} minutes)
    """

    header_table = Table(
        [[Paragraph(info_text, body_style), reportlab_qr]],
        colWidths=[4.2 * inch, 2.0 * inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # 4. Itemized Bill Table
    story.append(Paragraph("Payment & Billing Summary", section_heading))
    bill_data = [
        ['Description', 'Vehicle Type', 'Slot', 'Rate Type', 'Amount (INR)'],
        [
            f"Parking Space Reservation at {booking.parking_lot.name}",
            booking.vehicle_type.capitalize(),
            booking.slot.slot_number,
            'Hourly / Prorated',
            f"₹{booking.price:.2f}"
        ],
        ['', '', '', 'Total Paid:', f"₹{booking.price:.2f}"]
    ]

    bill_table = Table(bill_data, colWidths=[2.6 * inch, 1.0 * inch, 0.8 * inch, 1.0 * inch, 1.1 * inch])
    bill_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E5E6F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F1F5F9')),
        ('FONTNAME', (3, 2), (-1, 2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (4, 2), (4, 2), colors.HexColor('#0E5E6F')),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 20))

    # 5. Terms & Gate Entry Instructions
    terms_text = """
    <b>Gate Entry Guidelines:</b><br/>
    1. Present this digital ticket or printed copy at the entrance kiosk or to the security attendant.<br/>
    2. The attendant will scan the QR code to verify your slot reservation and mark vehicle check-in.<br/>
    3. Extensions can be requested online via your dashboard if additional time is needed and the slot remains available.<br/>
    4. For emergency support or queries, contact <b>support@smartpark.com</b>.
    """
    story.append(Paragraph(terms_text, body_style))
    story.append(Spacer(1, 25))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor('#94A3B8'),
        alignment=1
    )
    story.append(Paragraph("This is an electronically generated receipt for SmartPark Smart Mobility. No physical signature required.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
