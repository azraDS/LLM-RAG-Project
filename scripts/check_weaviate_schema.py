from fashion_rag.clients import get_weaviate_client
client = get_weaviate_client(with_openai_key=False)
schema = client.schema.get("Product")
print("Schema is ready!")
print(schema["moduleConfig"]["text2vec-openai"])
