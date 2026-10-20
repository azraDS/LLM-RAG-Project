from fashion_rag.clients import get_weaviate_client
client = get_weaviate_client(with_openai_key=False)
response = client.data_object.get(class_name="Product", limit=1)
print(response)
