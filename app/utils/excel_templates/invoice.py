from typing import Dict, Any
from .generator import ExcelGenerator
from app.core.logger import logger
from .base import find_items_in_data

class InvoiceTemplate:
    """Professional invoice template with complete data display"""

    @staticmethod
    def generate(data: Dict[str, Any], generator: ExcelGenerator) -> ExcelGenerator:
        """Generate a beautifully formatted invoice with all data"""
        ws = generator.ws

        # Debug: Print data structure to understand what fields are available
        if isinstance(data, dict):
            logger.debug(f"📊 Invoice data keys: {list(data.keys())}")
            
            if 'invoice_details' in data:
                 logger.debug(f"📊 invoice_details keys: {list(data['invoice_details'].keys()) if isinstance(data['invoice_details'], dict) else type(data['invoice_details'])}")

        # Set column widths
        generator.set_column_width('A', 8)   # S.N
        generator.set_column_width('B', 35)  # Items
        generator.set_column_width('C', 12)  # Quantity
        generator.set_column_width('D', 15)  # Price per Unit
        generator.set_column_width('E', 15)  # Total

        # Title - INVOICE
        generator.merge_and_write(
            'A1', 'E1', 'INVOICE',
            font=generator.create_font(bold=True, size=24),
            alignment=generator.create_alignment(horizontal='center', vertical='center')
        )

        # Company/Vendor Information (Top)
        row = 3
        vendor_name = (
            data.get('vendor_name') or
            data.get('supplier_name') or
            data.get('company_name') or
            data.get('store_name') or
            data.get('business_name') or
            data.get('seller_name') or
            data.get('from_company') or
            ''
        )

        if not vendor_name:
            vendor_info_obj = data.get('vendor_info', data.get('supplier_info', {}))
            if isinstance(vendor_info_obj, dict):
                vendor_name = (
                    vendor_info_obj.get('name') or
                    vendor_info_obj.get('company_name') or
                    vendor_info_obj.get('business_name') or
                    ''
                )

            if not vendor_name and 'invoice_details' in data:
                invoice_details = data.get('invoice_details', {})
                if isinstance(invoice_details, dict):
                    vendor_name = (
                        invoice_details.get('vendor_name') or
                        invoice_details.get('from') or
                        invoice_details.get('issued_by') or
                        ''
                    )

        if vendor_name:
            generator.merge_and_write(f'A{row}', f'E{row}', vendor_name,
                                     font=generator.create_font(bold=True, size=14),
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1

        vendor_info = data.get('vendor_info', data.get('supplier_info', {}))
        if isinstance(vendor_info, dict):
            vendor_address = vendor_info.get('address', data.get('vendor_address', ''))
            vendor_phone = vendor_info.get('phone', data.get('vendor_phone', ''))
            vendor_email = vendor_info.get('email', data.get('vendor_email', ''))
        else:
            vendor_address = data.get('vendor_address', '')
            vendor_phone = data.get('vendor_phone', '')
            vendor_email = data.get('vendor_email', '')

        if vendor_address:
            generator.merge_and_write(f'A{row}', f'E{row}', vendor_address,
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1
        if vendor_phone:
            generator.merge_and_write(f'A{row}', f'E{row}', vendor_phone,
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1
        if vendor_email:
            generator.merge_and_write(f'A{row}', f'E{row}', vendor_email,
                                     alignment=generator.create_alignment(horizontal='center'))
            row += 1

        row += 1  # Spacing

        generator.write_cell(f'A{row}', 'DATE:', font=generator.create_font(bold=True))
        generator.write_cell(f'B{row}', generator.format_date(data.get('date', '')))
        row += 1
        invoice_num = data.get('invoice_number', data.get('invoice_id', data.get('invoice_no', '')))
        if invoice_num:
            generator.write_cell(f'A{row}', 'INVOICE #:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', str(invoice_num))
            row += 1

        generator.write_cell(f'A{row}', 'BILL TO:', font=generator.create_font(bold=True))
        generator.write_cell(f'B{row}', data.get('customer_name', ''))
        row += 1

        customer_info = data.get('customer_info', {})
        if isinstance(customer_info, dict):
            customer_address = customer_info.get('address', '')
            customer_phone = customer_info.get('phone', '')
            customer_email = customer_info.get('email', '')
        else:
            customer_address = data.get('customer_address', '')
            customer_phone = data.get('customer_phone', '')
            customer_email = data.get('customer_email', '')

        if customer_address:
            generator.write_cell(f'A{row}', 'Address:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', customer_address)
            row += 1
        if customer_phone:
            generator.write_cell(f'A{row}', 'Phone:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', customer_phone)
            row += 1
        if customer_email:
            generator.write_cell(f'A{row}', 'Email:', font=generator.create_font(bold=True))
            generator.write_cell(f'B{row}', customer_email)
            row += 1

        row += 1  # Spacing before table

        header_fill = generator.create_fill('E7E6E6')
        border = generator.create_border()

        generator.write_cell(f'A{row}', 'S.N', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='center'), fill=header_fill, border=border)
        generator.write_cell(f'B{row}', 'ITEMS', font=generator.create_font(bold=True), fill=header_fill, border=border)
        generator.write_cell(f'C{row}', 'QUANTITY', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='center'), fill=header_fill, border=border)
        generator.write_cell(f'D{row}', 'PRICE PER UNIT', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)
        generator.write_cell(f'E{row}', 'TOTAL', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'), fill=header_fill, border=border)

        items = find_items_in_data(data)
        if not items:
            logger.warning("⚠️ No line items found in invoice data")
            items = []

        row += 1
        sn = 1

        if items and isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    desc = item.get('description', item.get('item', item.get('name', '')))
                    quantity = item.get('quantity', item.get('qty', 1))
                    price = item.get('price', item.get('unit_price', item.get('rate', 0)))
                    total = item.get('total', item.get('amount', (float(price) * float(quantity)) if price and quantity else 0))

                    generator.write_cell(f'A{row}', str(sn), alignment=generator.create_alignment(horizontal='center'), border=border)
                    generator.write_cell(f'B{row}', desc, border=border)
                    generator.write_cell(f'C{row}', str(quantity), alignment=generator.create_alignment(horizontal='center'), border=border)
                    generator.write_cell(f'D{row}', generator.format_currency(price), alignment=generator.create_alignment(horizontal='right'), border=border)
                    generator.write_cell(f'E{row}', generator.format_currency(total), alignment=generator.create_alignment(horizontal='right'), border=border)
                    row += 1
                    sn += 1

        row += 1
        subtotal = data.get('subtotal', data.get('total_amount', 0))
        tax_rate = data.get('tax_rate', 0)
        tax = data.get('tax', data.get('sales_tax', 0))
        other = data.get('other', data.get('other_charges', 0))
        total = data.get('total_amount', data.get('total', 0))

        generator.write_cell(f'D{row}', 'SUBTOTAL:', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'))
        generator.write_cell(f'E{row}', generator.format_currency(subtotal), alignment=generator.create_alignment(horizontal='right'))

        row += 1
        generator.write_cell(f'D{row}', 'TAX RATE:', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'))
        generator.write_cell(f'E{row}', f'{tax_rate}%' if tax_rate else '0.00%', alignment=generator.create_alignment(horizontal='right'))

        row += 1
        generator.write_cell(f'D{row}', 'SALES TAX:', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'))
        generator.write_cell(f'E{row}', generator.format_currency(tax), alignment=generator.create_alignment(horizontal='right'))

        if other:
            row += 1
            generator.write_cell(f'D{row}', 'OTHER:', font=generator.create_font(bold=True), alignment=generator.create_alignment(horizontal='right'))
            generator.write_cell(f'E{row}', generator.format_currency(other), alignment=generator.create_alignment(horizontal='right'))

        row += 1
        generator.write_cell(f'D{row}', 'TOTAL:', font=generator.create_font(bold=True, size=12), alignment=generator.create_alignment(horizontal='right'), fill=generator.create_fill('E7E6E6'))
        generator.write_cell(f'E{row}', generator.format_currency(total), font=generator.create_font(bold=True, size=12), alignment=generator.create_alignment(horizontal='right'), fill=generator.create_fill('E7E6E6'))

        row += 2
        payment_note = data.get('payment_instructions', f'Make all checks payable to {vendor_name}.')
        generator.merge_and_write(f'A{row}', f'E{row}', payment_note, font=generator.create_font(size=9))

        row += 1
        generator.merge_and_write(f'A{row}', f'E{row}', 'THANK YOU FOR YOUR BUSINESS!', font=generator.create_font(bold=True, size=11), alignment=generator.create_alignment(horizontal='center'))

        return generator
