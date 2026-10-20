"""Intent-routed fashion store assistant: Weaviate retrieval + OpenAI generation."""
import logging
from datetime import datetime

from .clients import get_openai_client, get_weaviate_client
from .config import settings as default_settings

logger = logging.getLogger(__name__)


class FashionAssistant:
    def __init__(self, df, weaviate_client=None, openai_client=None, settings=default_settings):
        self.weaviate_client = weaviate_client or get_weaviate_client(settings)
        self.openai_client = openai_client or get_openai_client(settings)
        self.model_name = settings.model_name
        self.chat_history = []

        # Load filters from DataFrame(to be used for routing)
        self.categories = df['category'].dropna().unique().tolist()
        self.product_categories = df['product_category'].dropna().str.strip().unique().tolist()
        self.sub_categories = df['sub_category'].dropna().unique().tolist()

        # File path for website info
        self.website_info_path = settings.website_info_path


    # memory related functions
    def add_to_history(self, role, content):
        """Add a message to chat history with timestamp"""
        self.chat_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

    def get_recent_history(self, n=2):
        """Get the n most recent messages from chat history"""
        return self.chat_history[-n:] if self.chat_history else []

    def format_history_for_context(self, n=3):
        """Format recent chat history for context in prompts"""
        recent = self.get_recent_history(n)
        if not recent:
            return ""

        formatted = "\nRecent conversation history:\n"
        for msg in recent:
            formatted += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return formatted

    def clear_history(self):
        """Clear the chat history"""
        self.chat_history = []




    # main language model function
    def _generate_llm_response(self, prompt, system_msg=None):
        """Enhanced LLM response generator with conversation history"""

        context = self.format_history_for_context()

        messages = [
            {"role": "system", "content": system_msg or "You're a helpful fashion assistant."}
        ]

        if context:
            messages.append({
                "role": "system",
                "content": f"Here is the recent conversation context:\n{context}"
            })

        messages.append({"role": "user", "content": prompt})

        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        response_content = response.choices[0].message.content

        # Add the interaction to chat history
        self.add_to_history('user', prompt)
        self.add_to_history('assistant', response_content)

        return response_content




    #parser function fto generate filters
    def _parse_query_filters(self, query):
        """Use DataFrame-derived filters to extract category, sub_category, and product_category from the query."""
        # Create lowercase versions for matching
        categories_lower = [c.lower() for c in self.categories]
        sub_categories_lower = [sc.lower() for sc in self.sub_categories]
        product_categories_lower = [pc.lower() for pc in self.product_categories]

        filters = {}

        # Combine all known categories, sub-categories, and product categories into a single list
        all_categories = categories_lower + sub_categories_lower + product_categories_lower

        # Convert the query to lowercase for case-insensitive matching
        query_lower = query.lower()

        # Check for multi-word phrases in the query
        for category in all_categories:
            if category in query_lower:
                if category in categories_lower:
                    idx = categories_lower.index(category)
                    filters['category'] = self.categories[idx]
                elif category in sub_categories_lower:
                    idx = sub_categories_lower.index(category)
                    filters['sub_category'] = self.sub_categories[idx]
                elif category in product_categories_lower:
                    idx = product_categories_lower.index(category)
                    filters['product_category'] = self.product_categories[idx]

        return filters


    # initiates database client to fetch data based on query
    def _retrieve_from_weaviate(self, query, num_results=5, max_distance=0.5): #adjust the max distance accordingly
        """Weaviate retrieval with enhanced filtering and LLM response generation"""
        try:

            # Get filters from query
            filters = self._parse_query_filters(query)
            logger.debug("Filters: %s", filters)

            if filters:

                # Build base query
                query_builder = self.weaviate_client.query.get(
                    "Product",
                    ["title", "pid", "product_category", "category", "sub_category","product_details"]
                ).with_hybrid(query=query, alpha=0.5)
                ## alpha=1 pure semantic, alpha=1 pure keywords search
                # query_properties > the keyword search will look into this property only
                #.with_near_text({"concepts": [query]}) > semantic search only
                #with_bm25(query="comfortable summer dresses")> key word only


                response = query_builder.with_limit(num_results).do()
                logger.debug("Weaviate response: %s", response)

                # Check if the response contains products
                if response and "data" in response and "Get" in response["data"]:
                    products = response["data"]["Get"].get("Product", [])

                    #debugging
                    logger.debug("Found %d products", len(products))


                    # Generate product list for the prompt
                    product_list = "\n".join(
                    f"{idx+1}. ID: {p['pid']} - TITLE: {p['title']}\n   PRODUCT CATEGORY: {p['product_category']} \n PRODUCT DETAILS {p['product_details']}"
                    for idx, p in enumerate(products)
                    )

                    # debug
                    logger.debug("%s", product_list)

                    prompt = f"""
                    Found {len(products)} products matching your query.
                    Create a friendly response mentioning relevant items.
                    Respond using all of these products:
                    {product_list}
                    Here is the original query
                    {query}

                    Rules:
                    1. List the products in the following format:
                        1. **Title:** [Product Title]
                            - **ID:** [Product ID]
                            - **Product Category:** [Product Category]
                            - **Product Details:** [Product Details]
                        2. **Title:** [Product Title]
                            - **ID:** [Product ID]
                            - **Product Category:** [Product Category]
                            - **Product Details:** [Product Details]
                        ...
                    2. If no matches, say "I couldn't find exact matches, but I can help you with other options."
                    3. Never invent products."""

                    # Pass the prompt to the LLM and return its response
                    llm_response = self._generate_llm_response(prompt)
                    return llm_response

                # If no products are found, return a default message
                no_product_prompt = """No product found matching the user query. Kindly offer searching for different products"""
                llm_response = self._generate_llm_response(no_product_prompt)
                return llm_response

            else: return self.answer_product_questions(query)



        except Exception:
            logger.exception("Weaviate error")
            return "Sorry, I encountered an error while searching for products. Please try again."


    def answer_product_questions(self, query):
        """
        Use LLM to answer questions about the types of products available on the e-commerce website.
        Dynamically includes categories, subcategories, and specific product categories in the LLM prompt.
        """
        # Create a system message to provide context to the LLM
        system_msg = (
            "You are a knowledgeable fashion assistant with up-to-date information "
            "about an e-commerce website's available general categories, subcategories, and specific product categories"
            "Answer user queries based on the following available options."
        )

        # Generate the context dynamically and give the available lists loaded from dataset
        context = (
            f"Here is the list of general product categories available: {', '.join(self.categories)}.\n"
            f"The subcategories are: {', '.join(self.sub_categories)}.\n"
            f"And the available product types are: {', '.join(self.product_categories)}.\n"
            "Answer user queries accordingly, being concise and informative."
        )

        prompt = f"{context}\n\nUser's query: {query}"

        response = self._generate_llm_response(prompt, system_msg)
        return response


    # helper function for the below llm
    def _load_website_info(self):
        """Load website info from the file."""
        try:
            with open(self.website_info_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("File '%s' not found.", self.website_info_path)
            return ""
        except Exception:
            logger.exception("Error loading website info")
            return ""

    # uses Fashionista_Websito_Info dummy txt file. If the information not provided, instructed to answer kindly.
    def handle_website_question(self, query):
        """Answer using website info document."""
        website_info = self._load_website_info()
        if not website_info:
            return "Sorry, I couldn't load the website information. Please try again later."

        prompt = f"""
        You are a helpful assistant for an online fashion store. Use the following website information to answer the user's question. If the information is not available, say "I don't know."

        Website Information:
        {website_info}

        Question: {query}

        Rules:
        1. Answer the question using ONLY the provided website information.
        2. If the information is not available, say "I don't have this information at the moment, but you can check the official website for more details."
        3. Keep your response concise and relevant.
        """

        return self._generate_llm_response(prompt)

    # built to greet and interact with user if any irrelant queries have been sent
    def handle_natural_conversation(self, query):
        """Answer user queries, handle greetings, and manage irrelevant questions."""

        prompt = f"""
        You are a helpful assistant for an online fashion store. Your role is to assist users with questions related to the website, available products, or store information. Follow these rules:

        1. If the user greets you (e.g., "Hi", "Hello"), respond with a friendly greeting and remind them of your capabilities.
        2. If the user asks an irrelevant question (e.g., about unrelated topics, personal opinions, or non-store-related queries), kindly explain that you are a store assistant and can only help with questions about the website or available products.
        3. Keep your responses polite, concise, and relevant.

        Question: {query}
        """

        return self._generate_llm_response(prompt)

    #Router function, the query always classified first, and redirected accordingly
    def classify_intent(self, query):
        """Classify user intent into one of three categories"""
        prompt = f"""Classify this fashion e-commerce query:
        Options:
        - product_search (looking for specific items)
        - product_question (about products/types)
        - website_question (about company/policies/refunds/orders)
        - other (unrelated)

        Query: {query}
        Classification:"""

        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=20
        )
        return response.choices[0].message.content.lower()

    # After query classification, initiates the relevant functions.
    def process_query(self, query):
        """Main processing pipeline"""
        intent = self.classify_intent(query)

        if "product_search" in intent:
            return self._retrieve_from_weaviate(query)
        elif "product_question" in intent:
            return self.answer_product_questions(query)
        elif "website_question" in intent:
            return self.handle_website_question(query)
        return self.handle_natural_conversation(query)  # "other" or an unexpected label
