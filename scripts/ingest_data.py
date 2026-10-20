import json
import time
import uuid

from fashion_rag.clients import get_weaviate_client
from fashion_rag.config import PROJECT_ROOT, settings

settings.require_openai_key()
print("API key loaded")

# Set the OpenAI API key in the Weaviate client
client = get_weaviate_client(timeout_config=(10, 60))  # Increase timeout(to prevent error)

modified_data_path = settings.modified_data_path

# Load the modified data
with open(modified_data_path, "r") as f:
    data = [json.loads(line) for line in f]

# Add a UUID to each product(tp prevent duplicate embedings)
for product in data:
    product["uuid"] = str(uuid.uuid4())

# Retry mechanism for data ingestion
def create_product_with_retry(product, retries=3, delay=2):
    for attempt in range(retries):
        try:
            existing_object = client.data_object.get_by_id(product["uuid"], class_name="Product")
            if not existing_object:
                client.data_object.create(
                    data_object=product,
                    class_name="Product",
                    uuid=product["uuid"]  # Use the generated UUID
                )
            return
        except Exception as e:
            with open(PROJECT_ROOT / "ingest_errors.log", "a") as log_file:
                log_file.write(f"Attempt {attempt + 1} failed for product {product['pid']}: {e}\n")
            print(f"Attempt {attempt + 1} failed for product {product['pid']}: {e}")
            time.sleep(delay)
    raise Exception(f"All retry attempts failed for product {product['pid']}")

# Batch data ingestion
batch_size = 50
delay = 2  # Delay in seconds between batches
total_products = len(data)
start_time = time.time()

#save the progress
progress_file = PROJECT_ROOT / ".ingest_progress"
if progress_file.exists():
    with open(progress_file, "r") as f:
        last_ingested_index = int(f.read())
else:
    last_ingested_index = 0

for i in range(last_ingested_index, total_products, batch_size):
    batch = data[i:i + batch_size]
    for product in batch:
        create_product_with_retry(product)
    print(f"Ingested batch {i // batch_size + 1} ({(i + batch_size) / total_products * 100:.2f}% complete)")
    time.sleep(delay)
    with open(progress_file, "w") as f:
        f.write(str(i + batch_size))

end_time = time.time()
print("Data ingested into Weaviate successfully!")
print(f"Time taken for embedding {len(data)} rows: {end_time - start_time} seconds")

# Verify data ingestion
response = client.query.aggregate("Product").with_meta_count().do()
ingested_count = response["data"]["Aggregate"]["Product"][0]["meta"]["count"]
print(f"Expected {len(data)} rows, ingested {ingested_count} rows.")
print("Number of objects in 'Product' class:", response["data"]["Aggregate"]["Product"][0]["meta"]["count"])
