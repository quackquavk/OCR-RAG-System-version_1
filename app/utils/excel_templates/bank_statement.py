from typing import Dict, Any
from .generator import ExcelGenerator

class BankStatementTemplate:
    """Bank statement template with complete transaction data"""

    @staticmethod
    def generate(data: Dict[str, Any], generator: ExcelGenerator) -> ExcelGenerator:
        """Generate a bank statement format"""

        # Set column widths
        generator.set_column_width('A', 15)  # Date
        generator.set_column_width('B', 40)  # Description
        generator.set_column_width('C', 15)  # Debit
        generator.set_column_width('D', 15)  # Credit
        generator.set_column_width('E', 15)  # Balance

        # Title
        generator.merge_and_write(
            'A1', 'E1', 'BANK STATEMENT',
            font=generator.create_font(bold=True, size=20),
            alignment=generator.create_alignment(horizontal='center')
        )

        # Bank info
        row = 3
        bank_name = data.get('bank_name', '')
        if bank_name:
            generator.merge_and_write(f'A{row}', f'E{row}', bank_name,
                                     font=generator.create_font(bold=True, size=14),
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1

        # Account details on LEFT
        row += 1
        account_number = data.get('account_number', '')
        if account_number:
            generator.write_cell(f'A{row}', 'ACCOUNT #:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', str(account_number))
            row += 1

        account_holder = data.get('account_holder', data.get('customer_name', ''))
        if account_holder:
            generator.write_cell(f'A{row}', 'ACCOUNT HOLDER:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', account_holder)
            row += 1

        statement_period = data.get('statement_period', '')
        if statement_period:
            generator.write_cell(f'A{row}', 'PERIOD:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', statement_period)
            row += 1

        row += 1  # Spacing

        # Table header
        header_fill = generator.create_fill('E7E6E6')
        border = generator.create_border()

        generator.write_cell(f'A{row}', 'DATE', font=generator.create_font(bold=True), fill=header_fill, border=border)
        generator.write_cell(f'B{row}', 'DESCRIPTION', font=generator.create_font(bold=True), fill=header_fill, border=border)
        generator.write_cell(f'C{row}', 'DEBIT', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)
        generator.write_cell(f'D{row}', 'CREDIT', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)
        generator.write_cell(f'E{row}', 'BALANCE', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)

        # Transactions
        transactions = data.get('transactions', [])
        row += 1

        if transactions and isinstance(transactions, list):
            for txn in transactions:
                if isinstance(txn, dict):
                    generator.write_cell(f'A{row}', generator.format_date(txn.get('date', '')), border=border)
                    generator.write_cell(f'B{row}', txn.get('description', ''), border=border)
                    generator.write_cell(f'C{row}', generator.format_currency(txn.get('debit', 0)), alignment=generator.create_alignment(horizontal='right'), border=border)
                    generator.write_cell(f'D{row}', generator.format_currency(txn.get('credit', 0)), alignment=generator.create_alignment(horizontal='right'), border=border)
                    generator.write_cell(f'E{row}', generator.format_currency(txn.get('balance', 0)), alignment=generator.create_alignment(horizontal='right'), border=border)
                    row += 1

        # Final balance
        row += 1
        final_balance = data.get('final_balance', data.get('closing_balance', 0))
        generator.write_cell(f'D{row}', 'FINAL BALANCE:', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=generator.create_fill('E7E6E6'))
        generator.write_cell(f'E{row}', generator.format_currency(final_balance), font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=generator.create_fill('E7E6E6'))

        return generator
