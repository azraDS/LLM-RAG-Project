from fashion_rag.clients import get_openai_client

client = get_openai_client()

try:
    response = client.embeddings.create(
        input="Hello, world!",
        model="text-embedding-3-small"
    )
    print(response)
except Exception as e:
    print(f"Error: {e}")