from typing import Dict, Any
from .generator import ExcelGenerator

class GenericTemplate:
    """Generic template for other document types"""

    @staticmethod
    def generate(data: Dict[str, Any], generator: ExcelGenerator) -> ExcelGenerator:
        """Generate a generic formatted document with all data"""

        # Set column widths
        generator.set_column_width('A', 30)
        generator.set_column_width('B', 50)

        # Title
        doc_type = data.get('document_type', 'Document').upper()
        generator.merge_and_write(
            'A1', 'B1', doc_type,
            font=generator.create_font(bold=True, size=18),
            alignment=generator.create_alignment(horizontal='center')
        )

        # Exclude internal fields
        exclude_fields = [
            'company_id', 'image_url', 'document_key',
            'user_id', 'created_at', 'document_type'
        ]

        row = 3
        border = generator.create_border()

        # Header
        generator.write_cell(f'A{row}', 'FIELD', font=generator.create_font(bold=True), fill=generator.create_fill('E7E6E6'), border=border)
        generator.write_cell(f'B{row}', 'VALUE', font=generator.create_font(bold=True), fill=generator.create_fill('E7E6E6'), border=border)

        row += 1

        # Flatten and display all data
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    items.append((new_key, ', '.join(map(str, v))))
                else:
                    items.append((new_key, v))
            return dict(items)

        flattened = flatten_dict(data)

        for key, value in sorted(flattened.items()):
            if key not in exclude_fields:
                generator.write_cell(f'A{row}', key.replace('_', ' ').title(), font=generator.create_font(bold=True), border=border)
                generator.write_cell(f'B{row}', str(value), border=border)
                row += 1

        return generator
