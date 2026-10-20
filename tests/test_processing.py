import pytest

from fashion_rag.config import settings
from fashion_rag.data import read_jsonl
from fashion_rag.processing import flatten_product_details, process_products


def test_flatten_joins_key_value_pairs():
    details = [{"Color": "Blue"}, {"Fit": "Slim", "Fabric": "Cotton"}]
    assert flatten_product_details(details) == "Color: Blue, Fit: Slim, Fabric: Cotton"


def test_flatten_skips_malformed_items():
    assert flatten_product_details([{"Color": "Blue"}, "oops", None]) == "Color: Blue"


def test_flatten_empty():
    assert flatten_product_details([]) == ""


def test_process_products_does_not_mutate_input_and_handles_missing_details():
    original = [{"pid": "A", "product_details": [{"Color": "Red"}]}, {"pid": "B"}]
    result = process_products(original)
    assert result[0]["product_details"] == "Color: Red"
    assert result[1]["product_details"] == ""
    assert original[0]["product_details"] == [{"Color": "Red"}]


@pytest.mark.skipif(
    not settings.modified_data_path.exists(),
    reason="processed dataset not present (run scripts/process_data.py)",
)
def test_pipeline_reproduces_processed_dataset():
    """Golden test: raw data run through the pipeline must equal the processed file on disk."""
    raw = read_jsonl(settings.raw_data_path)
    assert process_products(raw) == read_jsonl(settings.modified_data_path)
