from typing import Dict, Any, List, Optional
from app.core.logger import logger

def find_items_in_data(data: Dict[str, Any]) -> Optional[List[Dict]]:
    """
    Recursively search for line items in the data structure.
    Checks multiple possible field names and nested structures.

    Returns:
        List of item dictionaries or None if not found
    """
    
    # Direct top-level fields to check
    item_field_names = ['line_items', 'items', 'products', 'entries']

    for field_name in item_field_names:
        if field_name in data:
            items = data[field_name]
            if isinstance(items, list) and len(items) > 0:
                return items

    nested_field_names = ['invoice_details', 'receipt_details', 'extracted_data', 'details', 'data']

    for nested_field in nested_field_names:
        if nested_field in data and isinstance(data[nested_field], dict):
            nested_data = data[nested_field]
            for item_field in item_field_names:
                if item_field in nested_data:
                    items = nested_data[item_field]
                    if isinstance(items, list) and len(items) > 0:
                        return items

    if 'item_description' in data or 'description' in data:
        return [{
            'description': data.get('item_description', data.get('description', '')),
            'quantity': data.get('quantity', 1),
            'price': data.get('price', data.get('unit_price', data.get('total_amount', 0))),
            'total': data.get('total_amount', 0)
        }]

    return None
