from fashion_rag.clients import get_weaviate_client

client = get_weaviate_client()

def retrieve_from_weaviate(query, num_results=5):
    try:
        response = client.query.get("Product", ["title","category", "sub_category", "product_category","pid"]) \
            .with_near_text({"concepts": [query]}) \
            .with_limit(num_results) \
            .do()
        
        # Debugging the response to ensure we are getting the expected data
        if response and 'data' in response and 'Get' in response['data']:
            results = response['data']['Get'].get('Product', [])
        else:
            print("No data found or response is malformed.")
            return []

        return results
    
    except Exception as e:
        print(f"Error during Weaviate query: {e}")
        return []

# Example query to retrieve relevant products
query = "What are the best track pants for men?"
results = retrieve_from_weaviate(query)

# Handle case where no results were found
if not results:
    print("No results returned from Weaviate.")
else:
   
    for res in results:
        print(f"Title: {res.get('title', 'N/A')}")
        print(f"Category: {res.get('category', 'N/A')}")
        print(f"Sub category: {res.get('sub_category', 'N/A')}")
        print(f"product_category: {res.get('product_category', 'N/A')}")
        print(f"Product id: {res.get('pid', 'N/A')}")
        print("-" * 50)


















