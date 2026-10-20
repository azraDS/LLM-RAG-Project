from fashion_rag.clients import get_weaviate_client

# Initialize the client
client = get_weaviate_client(with_openai_key=False)

# Define the schema
schema = {
    "classes": [
        {
            "class": "Product",
            "description": "A product in the e-commerce store",
            "vectorizer": "text2vec-openai",  # Enable vectorization using OpenAI's text embeddings
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-3-small",  # Model for embeddings, customizable
                    "type": "text",
                    "vectorizeClassName": True,
                    "modelVersion": "latest"
                }
            },
            "properties": [
                {
                    "name": "category",
                    "dataType": ["string"],  # Category should always be a single string
                    "description": "Category of the product (e.g., 'Footwear', 'Apparel')",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False
                        }
                    }
                },
                {
                    "name": "description",
                    "dataType": ["text"],  # 'text' type for longer product descriptions
                    "description": "Detailed description of the product",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True  
                        }
                    }
                },
                {
                    "name": "pid",
                    "dataType": ["string"],  # String for product IDs
                    "description": "Unique Product ID",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True  # Skip vectorization since IDs aren't semantically meaningful
                        }
                    }
                },
                {
                    "name": "product_details",
                    "dataType": ["text"],  # Store the product details as a JSON string
                    "description": "Additional product details stored as a JSON string (e.g., sizes, colors)",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True  # Skip vectorization for raw JSON data
                        }
                    }
                },
                {
                    "name": "sub_category",
                    "dataType": ["string"],  # Sub-category is a single string
                    "description": "Sub-category of the product (e.g., 'Men's Shoes', 'Women's Tops')",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False
                        }
                    }
                },
                {
                    "name": "title",
                    "dataType": ["text"],  # String for product titles
                    "description": "Title of the product (e.g., 'Men's Running Shoes')",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True  # Enable embeddings for semantic search using titles
                        }
                    }
                },
                {
                    "name": "product_category",
                    "dataType": ["string"],  # Single string for specific product categories
                    "description": "Specific product type under a sub-category (e.g., 'Running Shoes', 'Formal Wear')",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False  # Enable embeddings for granular product categorization
                        }
                    }
                }
            ]
        }
    ]
}

# Create the schema in Weaviate
client.schema.create(schema)

print("Schema created successfully!")
