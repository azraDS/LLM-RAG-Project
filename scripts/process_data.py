"""Raw dataset -> cleaned JSON-lines file that is ingested into Weaviate."""
from fashion_rag.config import settings
from fashion_rag.data import read_jsonl, write_jsonl
from fashion_rag.processing import process_products

products = process_products(read_jsonl(settings.raw_data_path))
write_jsonl(settings.modified_data_path, products)

print(f"Processed {len(products)} products -> {settings.modified_data_path}")
