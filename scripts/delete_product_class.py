from fashion_rag.clients import get_weaviate_client
client = get_weaviate_client(with_openai_key=False)
client.schema.delete_class("Product")
print("'Product' class deleted.")


