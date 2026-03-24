"""
PDF Statement Generator for Digital Wallet.

This module handles the generation of professional PDF statements using ReportLab.
Includes company branding, transaction history, and balance summaries.
"""

import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PDFStatementGenerator:
    """Generate professional PDF statements for wallet transactions."""

    def __init__(self, wallet, start_date: datetime, end_date: datetime):
        """
        Initialize the PDF generator.

        Args:
            wallet: Wallet instance to generate statement for
            start_date: Start of date range
            end_date: End of date range
        """
        self.wallet = wallet
        self.start_date = start_date
        self.end_date = end_date
        self.styles = getSampleStyleSheet()
        self.buffer = BytesIO()

    def _get_custom_styles(self):
        """Create custom paragraph styles for the document."""
        styles = {
            "header": ParagraphStyle(
                "CustomHeader",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#1a1a2e"),
                spaceAfter=12,
                alignment=1,  # Center
            ),
            "subheader": ParagraphStyle(
                "SubHeader",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=colors.HexColor("#16213e"),
                spaceAfter=6,
            ),
            "normal": ParagraphStyle(
                "CustomNormal",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#333333"),
            ),
            "balance": ParagraphStyle(
                "Balance",
                parent=self.styles["Heading3"],
                fontSize=14,
                textColor=colors.HexColor("#0f3460"),
                alignment=1,  # Center
            ),
        }
        return styles

    def _add_logo(self, elements):
        """Add company logo to the document."""
        logo_path = os.path.join(settings.BASE_DIR, "Digital_Wallet.png")

        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=1.5 * inch, height=1.5 * inch)
                logo.hAlign = "CENTER"
                elements.append(logo)
                elements.append(Spacer(1, 0.25 * inch))
            except Exception:
                # If logo fails, add spacer instead
                elements.append(Spacer(1, 0.5 * inch))
        else:
            elements.append(Spacer(1, 0.5 * inch))

    def _add_header(self, elements, custom_styles):
        """Add document header with title and account info."""
        # Title
        elements.append(Paragraph("Account Statement", custom_styles["header"]))

        # Account information
        client = self.wallet.client_profile
        account_info = [
            ["Account Holder:", client.full_name if client.full_name else "N/A"],
            ["Account Email:", client.user.email],
            [
                "Statement Period:",
                f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
            ],
            ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]

        info_table = Table(account_info, colWidths=[2 * inch, 3.5 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 0.25 * inch))

    def _add_balance_summary(self, elements, custom_styles):
        """Add current balance summary with opening balance calculation."""
        elements.append(Paragraph("Balance Summary", custom_styles["subheader"]))

        # Calculate Opening Balance = All deposits/incoming - All withdrawals/outgoing BEFORE start date
        opening_balance = Decimal("0.00")
        prior_transactions = self.wallet.transactions.filter(
            created_at__lt=self.start_date, status="COMPLETED"
        ).select_related("counterparty_wallet")

        for txn in prior_transactions:
            if txn.type == "DEPOSIT":
                opening_balance += txn.amount
            elif txn.type == "WITHDRAWAL":
                opening_balance -= txn.amount
            elif txn.type == "TRANSFER":
                # EXPLICIT LOGIC per requirements:
                # - If txn.wallet == self.wallet: OUTGOING (subtract)
                # - If txn.counterparty_wallet == self.wallet: INCOMING (add)
                if txn.wallet == self.wallet:
                    opening_balance -= txn.amount
                elif txn.counterparty_wallet == self.wallet:
                    opening_balance += txn.amount

        # Calculate net change during period
        net_change = Decimal("0.00")
        period_transactions = self.wallet.transactions.filter(
            created_at__gte=self.start_date, created_at__lte=self.end_date, status="COMPLETED"
        ).order_by("created_at")

        for txn in period_transactions:
            if txn.type == "DEPOSIT":
                net_change += txn.amount
            elif txn.type == "WITHDRAWAL":
                net_change -= txn.amount
            elif txn.type == "TRANSFER":
                # EXPLICIT LOGIC per requirements:
                # - If txn.wallet == self.wallet: OUTGOING (subtract)
                # - If txn.counterparty_wallet == self.wallet: INCOMING (add)
                if txn.wallet == self.wallet:
                    net_change -= txn.amount
                elif txn.counterparty_wallet == self.wallet:
                    net_change += txn.amount

        closing_balance = opening_balance + net_change

        balance_data = [
            ["Opening Balance", f"${opening_balance:,.2f}"],
            ["Net Change", f"${net_change:,.2f}"],
            ["Closing Balance", f"${closing_balance:,.2f}"],
        ]

        balance_table = Table(balance_data, colWidths=[3 * inch, 2.5 * inch])
        balance_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, -1), (1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8e8e8")),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        elements.append(balance_table)
        elements.append(Spacer(1, 0.5 * inch))

    def _add_transactions(self, elements, custom_styles):
        """Add transaction history table with running balance."""
        elements.append(Paragraph("Transaction History", custom_styles["subheader"]))
        elements.append(Spacer(1, 0.1 * inch))

        # Re-calculate opening balance for running balance
        opening_balance = Decimal("0.00")
        prior_transactions = self.wallet.transactions.filter(
            created_at__lt=self.start_date, status="COMPLETED"
        )
        for txn in prior_transactions:
            if txn.type == "DEPOSIT":
                opening_balance += txn.amount
            elif txn.type == "WITHDRAWAL":
                opening_balance -= txn.amount
            elif txn.type == "TRANSFER":
                if txn.wallet == self.wallet:
                    opening_balance -= txn.amount
                else:
                    opening_balance += txn.amount

        # Get transactions for the period - chronological for running balance calculation
        transactions = self.wallet.transactions.filter(
            created_at__gte=self.start_date, created_at__lte=self.end_date, status="COMPLETED"
        ).order_by("created_at")

        if not transactions.exists():
            elements.append(
                Paragraph("No transactions found for this period.", custom_styles["normal"])
            )
            return

        # Build transaction data
        data = [["Date", "Type", "Description", "Amount", "Balance"]]

        running_balance = opening_balance

        for txn in transactions:
            if txn.type == "DEPOSIT":
                amt = txn.amount
                amount_str = f"+${txn.amount:,.2f}"
            elif txn.type == "WITHDRAWAL":
                amt = -txn.amount
                amount_str = f"-${txn.amount:,.2f}"
            elif txn.type == "TRANSFER":
                # EXPLICIT LOGIC per requirements:
                # - If txn.wallet == self.wallet: OUTGOING (subtract)
                # - If txn.counterparty_wallet == self.wallet: INCOMING (add)
                if txn.wallet == self.wallet:
                    amt = -txn.amount
                    amount_str = f"-${txn.amount:,.2f}"
                elif txn.counterparty_wallet == self.wallet:
                    amt = txn.amount
                    amount_str = f"+${txn.amount:,.2f}"
                else:
                    amt = Decimal("0.00")
                    amount_str = f"${txn.amount:,.2f}"
            else:
                amt = Decimal("0.00")
                amount_str = f"${txn.amount:,.2f}"

            running_balance += amt

            data.append(
                [
                    txn.created_at.strftime("%Y-%m-%d"),
                    txn.get_type_display(),
                    (
                        txn.description[:25] + "..."
                        if len(txn.description or "") > 25
                        else (txn.description or "-")
                    ),
                    amount_str,
                    f"${running_balance:,.2f}",
                ]
            )

        # Reverse for display (most recent at top) but keep header at top
        header = data[0]
        rows = data[1:]
        rows.reverse()
        data = [header] + rows

        # Create table
        table = Table(data, colWidths=[1.1 * inch, 0.9 * inch, 2.2 * inch, 1.1 * inch, 1.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f5f5f5")],
                    ),
                ]
            )
        )

        elements.append(table)

    def _add_footer(self, elements):
        """Add footer with company information."""
        elements.append(Spacer(1, 0.5 * inch))

        footer_text = """
        <para alignment="center" fontSize="8" textColor="#666666">
        This is an official document of Digital Wallet. For questions, contact support.<br/>
        Generated securely via the Digital Wallet Platform.
        </para>
        """
        elements.append(Paragraph(footer_text, self.styles["Normal"]))

    def generate(self) -> BytesIO:
        """
        Generate the PDF statement.

        Returns:
            BytesIO buffer containing the PDF
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        elements = []
        custom_styles = self._get_custom_styles()

        # Build document sections
        self._add_logo(elements)
        self._add_header(elements, custom_styles)
        self._add_balance_summary(elements, custom_styles)
        self._add_transactions(elements, custom_styles)
        self._add_footer(elements)

        # Build PDF
        doc.build(elements)

        # Seek to beginning for reading
        self.buffer.seek(0)

        return self.buffer


def generate_statement_pdf_to_media(
    wallet, start_date: datetime, end_date: datetime, task_id: str
) -> str:
    """
    Generate PDF statement and save to media directory.

    Args:
        wallet: Wallet instance
        start_date: Start of date range
        end_date: End of date range
        task_id: Celery task ID for unique filename

    Returns:
        Relative path to the generated PDF file
    """
    # Create statements directory if it doesn't exist
    statements_dir = os.path.join(settings.MEDIA_ROOT, "statements")
    os.makedirs(statements_dir, exist_ok=True)

    # Generate PDF
    generator = PDFStatementGenerator(wallet, start_date, end_date)
    pdf_buffer = generator.generate()

    # Create descriptive filename: {user_name}_statement_{start_date}_to_{end_date}.pdf
    user_name = wallet.client_profile.full_name or wallet.client_profile.user.email.split("@")[0]
    # Sanitize user name for filename (replace spaces with underscores, remove special chars)
    user_name = user_name.replace(" ", "_").replace("-", "_")
    user_name = "".join(c for c in user_name if c.isalnum() or c == "_")

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    filename = f"{user_name}_statement_{start_str}_to_{end_str}.pdf"
    filepath = os.path.join(statements_dir, filename)

    # Write to file
    with open(filepath, "wb") as f:
        f.write(pdf_buffer.getvalue())

    # Return relative path
    relative_path = os.path.join("statements", filename)
    return relative_path
