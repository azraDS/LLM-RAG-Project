"""Product data transformations (raw dataset -> flat records ready for Weaviate)."""
import logging

logger = logging.getLogger(__name__)


def flatten_product_details(details: list) -> str:
    """[{"Color": "Blue"}, {"Fit": "Slim"}] -> "Color: Blue, Fit: Slim".

    Items that are not dicts are skipped (and logged) instead of failing the run.
    """
    parts = []
    for item in details:
        if isinstance(item, dict):
            parts.extend(f"{key}: {value}" for key, value in item.items())
        else:
            logger.warning("Skipping malformed item: %r", item)
    return ", ".join(parts)


def process_products(products: list[dict]) -> list[dict]:
    """Return copies of ``products`` with ``product_details`` flattened to a string."""
    return [
        {**p, "product_details": flatten_product_details(p.get("product_details", []))}
        for p in products
    ]
