from app.config.settings import init_firebase
from firebase_admin import db
from dotenv import load_dotenv
import csv
import io
from typing import List, Dict, Any, Optional

load_dotenv()


class FirebaseToCSV:
    def __init__(self):
        self.firebase = init_firebase()

    # ----------------------------------------------------------------------
    def flatten_for_csv(self, data: Any, parent_key: str = '', sep: str = '_') -> List[Dict[str, Any]]:
        """
        Recursively flatten nested dictionaries/lists into rows for CSV.
        - Nested dicts are expanded with key prefixes.
        - Lists of dicts generate multiple rows (item-based).
        - Lists of primitives are joined as comma-separated string.
        """
        rows = [{}]

        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k

                if isinstance(v, dict):
                    sub_rows = self.flatten_for_csv(v, new_key, sep)
                    rows = self._expand_rows(rows, sub_rows)

                elif isinstance(v, list):
                    if v and all(isinstance(i, dict) for i in v):
                        new_rows = []
                        for item in v:
                            sub_rows = self.flatten_for_csv(item, new_key, sep)
                            new_rows.extend(self._expand_rows(rows, sub_rows))
                        rows = new_rows
                    else:
                        for row in rows:
                            row[new_key] = ", ".join(map(str, v))
                else:
                    for row in rows:
                        row[new_key] = v
        else:
            for row in rows:
                row[parent_key] = data

        return rows

    @staticmethod
    def _expand_rows(base_rows: List[Dict[str, Any]], new_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Helper function to expand rows when nested lists/dicts exist"""
        combined = []
        for base in base_rows:
            for new in new_rows:
                combined.append({**base, **new})
        return combined

    # ----------------------------------------------------------------------
    def generate_csv_from_rows(self, rows: List[Dict[str, Any]], exclude_fields: Optional[List[str]] = None) -> Optional[str]:
        """
        Generate CSV text from flattened rows safely with all possible keys

        Args:
            rows: List of dictionaries representing CSV rows
            exclude_fields: List of field names to exclude from CSV (optional)

        Returns:
            CSV text as string
        """
        if not rows:
            return None

        # Collect all unique keys across all rows
        all_keys = set()
        for row in rows:
            all_keys.update(row.keys())

        # Exclude specified fields
        if exclude_fields:
            all_keys = all_keys - set(exclude_fields)

        fieldnames = sorted(list(all_keys))  # Sort for consistent column order

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
