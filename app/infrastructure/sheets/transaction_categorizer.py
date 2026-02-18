import re
from typing import Dict, Optional, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class TransactionCategorizer:
    """
    Service to determine if a transaction is a PURCHASE or SALE
    based on the selected company name and parsed document data.
    """

    # Common company suffixes to remove for matching
    COMPANY_SUFFIXES = [
        r"\bLtd\.?",
        r"\bLimited",
        r"\bPvt\.?\s*Ltd\.?",
        r"\bPrivate\s+Limited",
        r"\bInc\.?",
        r"\bIncorporated",
        r"\bLLC",
        r"\bCorp\.?",
        r"\bCorporation",
        r"\bCo\.?",
        r"\bCompany",
        r"\bP\.?L\.?C\.?",
    ]

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize the categorizer

        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0) to consider a match
        """
        self.similarity_threshold = similarity_threshold

    def normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for comparison

        Args:
            name: Company name to normalize

        Returns:
            Normalized company name
        """
        try:
            if not name:
                return ""

            normalized = name.lower().strip()

            # Remove common suffixes
            for suffix in self.COMPANY_SUFFIXES:
                normalized = re.sub(suffix, "", normalized, flags=re.IGNORECASE)

            # Remove extra whitespace
            normalized = re.sub(r"\s+", " ", normalized).strip()

            # Remove special characters except spaces
            normalized = re.sub(r"[^\w\s]", "", normalized)

            return normalized
        except Exception as e:
            logger.error(
                f"normalize_company_name failed for '{name}': {e}", exc_info=True
            )
            return ""

    def fuzzy_match(self, company_name: str, document_name: str) -> float:
        """
        Calculate similarity score between two company names

        Args:
            company_name: The company name to match
            document_name: The name found in the document

        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            if not company_name or not document_name:
                return 0.0

            # Normalize both names
            norm_company = self.normalize_company_name(company_name)
            norm_document = self.normalize_company_name(document_name)

            if not norm_company or not norm_document:
                return 0.0

            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, norm_company, norm_document).ratio()

            # Bonus for exact match after normalization
            if norm_company == norm_document:
                return 1.0

            # Bonus for substring match
            if norm_company in norm_document or norm_document in norm_company:
                similarity = max(similarity, 0.85)

            return similarity
        except Exception as e:
            logger.error(
                f"fuzzy_match failed for '{company_name}' vs '{document_name}': {e}",
                exc_info=True,
            )
            return 0.0

    def find_company_match(
        self, company_name: str, doc_data: Dict
    ) -> Tuple[Optional[str], float, str]:
        """
        Find if and where the company appears in the document

        Args:
            company_name: Company name to search for
            doc_data: Parsed document data

        Returns:
            Tuple of (role, confidence, matched_name)
            role: 'issuer', 'receiver', or None
            confidence: similarity score
            matched_name: the actual name that was matched
        """
        # Fields to check for issuer
        issuer_fields = [
            "issuer_name",
            "vendor_name",
            "store_name",
            "merchant_name",
            "seller_name",
            "from_company",
        ]

        # Fields to check for receiver
        receiver_fields = [
            "receiver_name",
            "customer_name",
            "client_name",
            "buyer_name",
            "to_company",
            "bill_to",
        ]

        try:
            best_issuer_match = 0.0
            best_issuer_name = ""

            best_receiver_match = 0.0
            best_receiver_name = ""

            for field in issuer_fields:
                value = doc_data.get(field)
                if value:
                    # Handle nested dictionaries
                    if isinstance(value, dict):
                        value = value.get("name", "")

                    if isinstance(value, str):
                        similarity = self.fuzzy_match(company_name, value)
                        if similarity > best_issuer_match:
                            best_issuer_match = similarity
                            best_issuer_name = value

            # Check receiver fields
            for field in receiver_fields:
                value = doc_data.get(field)
                if value:
                    # Handle nested dictionaries
                    if isinstance(value, dict):
                        value = value.get("name", "")

                    if isinstance(value, str):
                        similarity = self.fuzzy_match(company_name, value)
                        if similarity > best_receiver_match:
                            best_receiver_match = similarity
                            best_receiver_name = value

            # Determine role based on best match
            if (
                best_issuer_match >= self.similarity_threshold
                and best_issuer_match > best_receiver_match
            ):
                return ("issuer", best_issuer_match, best_issuer_name)
            elif best_receiver_match >= self.similarity_threshold:
                return ("receiver", best_receiver_match, best_receiver_name)
            else:
                return (None, max(best_issuer_match, best_receiver_match), "")
        except Exception as e:
            logger.error(
                f"find_company_match failed for '{company_name}': {e}", exc_info=True
            )
            return (None, 0.0, "")

    def categorize_transaction(self, doc_data: Dict, company_name: str) -> Dict:
        """
        Categorize a transaction as PURCHASE or SALE

        Args:
            doc_data: Parsed document data
            company_name: The selected company name

        Returns:
            Dict with:
                - category: 'purchase', 'sale', or None
                - confidence: 0.0 to 1.0
                - reason: explanation of the categorization
                - matched_name: the name that was matched in the document
        """
        try:
            if not company_name:
                return {
                    "category": None,
                    "confidence": 0.0,
                    "reason": "No company name provided",
                    "matched_name": "",
                }

            # Find company match in document
            role, confidence, matched_name = self.find_company_match(
                company_name, doc_data
            )

            if role == "issuer":
                # Company issued the document → SALE
                return {
                    "category": "sale",
                    "confidence": confidence,
                    "reason": f"Company '{company_name}' is the issuer/seller",
                    "matched_name": matched_name,
                }
            elif role == "receiver":
                # Company received the document → PURCHASE
                return {
                    "category": "purchase",
                    "confidence": confidence,
                    "reason": f"Company '{company_name}' is the receiver/buyer",
                    "matched_name": matched_name,
                }
            else:
                # Could not determine
                return {
                    "category": None,
                    "confidence": confidence,
                    "reason": f"Could not find company '{company_name}' in document (best match: {confidence:.2%})",
                    "matched_name": matched_name,
                }
        except Exception as e:
            logger.error(
                f"categorize_transaction failed for '{company_name}': {e}",
                exc_info=True,
            )
            return {
                "category": None,
                "confidence": 0.0,
                "reason": "Error during categorization",
                "matched_name": "",
            }
