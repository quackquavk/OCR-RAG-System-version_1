from typing import Dict, Any
from .generator import ExcelGenerator
from app.core.logger import logger
from .base import find_items_in_data

class ReceiptTemplate:
    """Receipt template with complete data display"""

    @staticmethod
    def generate(data: Dict[str, Any], generator: ExcelGenerator) -> ExcelGenerator:
        """Generate a receipt format with all data"""
        # Set column widths
        generator.set_column_width('A', 8)   # S.N
        generator.set_column_width('B', 35)  # Items
        generator.set_column_width('C', 12)  # Quantity
        generator.set_column_width('D', 15)  # Price per Unit
        generator.set_column_width('E', 15)  # Total

        # Title
        generator.merge_and_write(
            'A1', 'E1', 'RECEIPT',
            font=generator.create_font(bold=True, size=20),
            alignment=generator.create_alignment(horizontal='center')
        )

        # Store/Vendor info
        row = 3
        vendor_name = data.get('vendor_name', data.get('store_name', ''))
        if vendor_name:
            generator.merge_and_write(f'A{row}', f'E{row}', vendor_name,
                                     font=generator.create_font(bold=True, size=14),
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1

        store_info = data.get('store_info', data.get('vendor_info', {}))
        if isinstance(store_info, dict):
            address = store_info.get('address', data.get('vendor_address', ''))
            phone = store_info.get('phone', data.get('vendor_phone', ''))
        else:
            address = data.get('vendor_address', '')
            phone = data.get('vendor_phone', '')

        if address:
            generator.merge_and_write(f'A{row}', f'E{row}', address,
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1
        if phone:
            generator.merge_and_write(f'A{row}', f'E{row}', phone,
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1

        # Receipt details on LEFT
        row += 1
        generator.write_cell(f'A{row}', 'DATE:', font=generator.create_font(bold=True))
        generator.write_cell(f'B{row}', generator.format_date(data.get('date', '')))

        row += 1
        receipt_num = data.get('receipt_number', data.get('receipt_id', ''))
        if receipt_num:
            generator.write_cell(f'A{row}', 'RECEIPT #:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', str(receipt_num))
            row += 1

        row += 1  # Spacing

        # Table header
        header_fill = generator.create_fill('E7E6E6')
        border = generator.create_border()

        generator.write_cell(f'A{row}', 'S.N', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='center'), fill=header_fill, border=border)
        generator.write_cell(f'B{row}', 'ITEMS', font=generator.create_font(bold=True), fill=header_fill, border=border)
        generator.write_cell(f'C{row}', 'QUANTITY', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='center'), fill=header_fill, border=border)
        generator.write_cell(f'D{row}', 'PRICE PER UNIT', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)
        generator.write_cell(f'E{row}', 'TOTAL', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)

        # Items
        items = find_items_in_data(data)
        if not items:
            logger.warning("No items found in receipt data")
            items = []

        row += 1
        sn = 1

        if items and isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    desc = item.get('description', item.get('item', item.get('name', '')))
                    quantity = item.get('quantity', item.get('qty', 1))
                    price = item.get('price', item.get('unit_price', 0))
                    total = item.get('total', item.get('amount', (float(price) * float(quantity)) if price and quantity else 0))

                    generator.write_cell(f'A{row}', str(sn), alignment=generator.create_alignment(horizontal='center'), border=border)
                    generator.write_cell(f'B{row}', desc, border=border)
                    generator.write_cell(f'C{row}', str(quantity), alignment=generator.create_alignment(horizontal='center'), border=border)
                    generator.write_cell(f'D{row}', generator.format_currency(price), alignment=generator.create_alignment(horizontal='right'), border=border)
                    generator.write_cell(f'E{row}', generator.format_currency(total), alignment=generator.create_alignment(horizontal='right'), border=border)
                    row += 1
                    sn += 1

        # Total
        row += 1
        total = data.get('total_amount', data.get('total', 0))
        generator.write_cell(f'D{row}', 'TOTAL:', font=generator.create_font(bold=True, size=12), alignment=generator.create_alignment(horizontal='right'), fill=generator.create_fill('E7E6E6'))
        generator.write_cell(f'E{row}', generator.format_currency(total), font=generator.create_font(bold=True, size=12), alignment=generator.create_alignment(horizontal='right'), fill=generator.create_fill('E7E6E6'))

        # Payment method
        row += 2
        payment_method = data.get('payment_method', '')
        if payment_method:
            generator.merge_and_write(f'A{row}', f'E{row}', f'Payment Method: {payment_method}',
                                     alignment=generator.create_alignment(horizontal='center'))

        return generator
