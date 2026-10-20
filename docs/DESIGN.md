# Design & Data Processing

How the Fashion Assistant is built and why. For setup and running see the [README](../README.md).

## 1. Problem
Shoppers ask free-form questions ("blue slim-fit shirt for men", "what is your refund policy?").
A plain LLM would invent products and policies, so answers must be **grounded** in the store's own
catalogue and policy text.

## 2. Architecture
![App flow](../app/App_Flow_Schema.png)

| Component | Where | Responsibility |
|-----------|-------|----------------|
| Streamlit UI | `app/streamlit_app.py` | Chat interface only; no business logic |
| Assistant | `src/fashion_rag/assistant.py` | Intent routing, retrieval, prompt building, memory |
| Config | `src/fashion_rag/config.py` | The single place env vars and paths are read |
| Clients | `src/fashion_rag/clients.py` | The single place OpenAI / Weaviate clients are built |
| Processing | `src/fashion_rag/processing.py`, `data.py` | Pure data transformations and JSON-lines I/O |
| Vector DB | Weaviate (`docker-compose.yml`) | Stores products, embeds with `text-embedding-3-small` |

### Request flow
1. `classify_intent` asks the LLM (low temperature, 20 tokens) for one of
   `product_search`, `product_question`, `website_question`, `other`.
2. The router dispatches:
   - **product_search** → category / sub-category / product-category keywords are matched against
     the values present in the dataset. The filter acts as a **gate**: if something matches,
     Weaviate **hybrid search** (`alpha=0.5`, BM25 and vector equally weighted, top 5) runs and the
     LLM formats the hits in a fixed template; if nothing matches (e.g. "skirts" in a menswear
     catalogue), the query falls through to `product_question`, so the LLM can say the item is
     unavailable and suggest what exists instead of returning loosely-similar products.
   - **product_question** → retrieval-augmented answer limited to retrieved products.
   - **website_question** → answered from `data/Fashionista_Website_Info.txt` only.
   - **other** → short, polite small-talk reply.
3. The last few turns are passed back as context (short-term memory).

### Design decisions
- **Dependency injection for clients.** `FashionAssistant` accepts clients as arguments, so the
  tests run offline with fakes (no API key, no network).
- **One config module.** No `os.getenv` or client construction scattered through the code.
- **Hybrid search** because product queries mix exact terms (colour, fabric) and fuzzy intent.
- **Docker Compose for the whole stack** so the app resolves Weaviate by service name and anyone can
  run it with one command.
- **Datasets stay out of git.** The full data is large; a 60-product sample is committed and used as
  an automatic fallback so a fresh clone still runs.

## 3. Data
Source: [Kaggle – Flipkart Fashion Products Dataset](https://www.kaggle.com/datasets/aaditshukla/flipkart-fasion-products-dataset)
(setup in [notebooks/README.md](../notebooks/README.md)).

### Processing stages
| Stage | Artifact | Produced by |
|-------|----------|-------------|
| Raw | `notebooks/flipkart_fashion_products_dataset.json` | download |
| Cleaned & feature-engineered | `preprocessed_data.json` | `notebooks/data_analysis.ipynb` |
| Availability filter | `data_ready.json` | notebook |
| Class-balanced subset (854 products) | `data/balanced_data.json` | notebook |
| Flattened `product_details` | `data/modified_balanced_data.json` | `scripts/process_data.py` |
| Embedded + indexed | Weaviate `Product` class | `scripts/create_schema.py`, `scripts/ingest_data.py` |

Why the last cleaning step lives in `scripts/` and not the notebook: it is deterministic, tested
(`tests/test_processing.py`), and must run in the app's pipeline.

## 4. Data analysis report
Full exploration is in `notebooks/data_analysis.ipynb`; the main findings and decisions:

**Data quality**
- Hidden duplicates appear once the unique `url`, `_id` and `crawled_at` columns are dropped;
  28,080 unique `pid`s vs 29,089 rows after de-duplication (the gap is likely a handful of
  near-identical listings and was not investigated further).
- Some products have no brand or description (no pattern → likely scraping gaps); these were left empty.
- `average_rating` is empty only for new sellers, products with too few ratings, or out-of-stock items,
  which is consistent. `selling_price` is missing in a single out-of-stock row; price should stay
  visible even when out of stock (e.g. for "notify me" features).
- `seller` has 1,643 missing values and 535 unique sellers.

**Feature engineering**
- Seller information was turned into boolean flags (new seller, not enough ratings, etc.) because a
  zero rating count means something different for a new seller than for a poor one.
- `product_details` keys are not uniform across products (colour, fabric, pocket type, ...); empty
  keys were cleaned. Normalising them (e.g. colour) would enable proper filtering and makes
  keyword search a good complement to semantic search.
- Sub-categories were grouped and renamed to clearer display names.

**Deriving `product_category`** (no labelled data was available)
1. Embed titles together with the descriptive and hierarchical columns.
2. Reduce dimensions with PCA, then cluster with K-means (silhouette score 0.99).
3. Inspect each cluster manually, write regex patterns per product type, merge them, and apply to
   the dataset to create `product_category`.

Alternative: fine-tune a BERT-style token/sequence classifier on a labelled set. Using the regex
output as labels, a model was fine-tuned in `notebooks/fine_tunning.ipynb` (Kaggle GPU). It is not
yet evaluated or deployed; it could also extract `product_category` from a user query before
retrieval.

**Serving subset.** To keep embedding time and cost low, a **balanced 854-product subset** covering
all categories/features was created (end of the notebook), then `product_details` was flattened
from a dict into text so it fits the Weaviate schema. Only category, sub-category and
product-category are vectorised; all other fields are returned from the DB but are not part of the
semantic search.

### Issues and trade-offs found during development
| Topic | Behaviour | Possible fix |
|-------|-----------|--------------|
| Typos / plurals | Filters need exact keyword matches, so a typo falls through to `product_question`, where the LLM corrects it. Plurals can slip past semantic search. | A query-normalising LLM step before the DB |
| Multi-word categories | "football shoes" may match only "shoes" | Longest-match filter |
| Misleading sub-categories | "Bags, Wallets & Belts" suggests bags exist, but no `product_category` is "bag" | Better labelling / schema |
| "Show more" | Weaviate is stateless, so a repeat query returns the same top 5 | Track seen `pid`s, or fetch all and paginate in the UI |
| Limited attribute search | Colour, length, etc. are not filterable | Normalise attributes, add structured filters |
| Website questions | Answered from a mock policy text; unknown answers redirect to the website | Real site content |

### Improvements with more time
Fine-tuned or open-source embedding and chat models (cost), richer filtering (brand, seller,
rating, price, discount), a query-processing LLM, user feedback capture, evaluation of retrieval
and the fine-tuned classifier, and cloud deployment (Docker + Weaviate + open-source models) for scale.

### Technology choices
- **Weaviate**: open source, native hybrid search (vector + keyword + attribute filters), GraphQL
  querying, built-in `text2vec-openai` module, class-based schema, persistent storage.
- **OpenAI** (`text-embedding-3-small` + chat): chosen for the seamless Weaviate module integration.
- **Docker**: reproducible, isolated services that are easy to share and deploy.
- **Streamlit / pandas**: fast interactive UI and data handling.

## 5. Testing & quality
- `pytest` unit tests with fake OpenAI/Weaviate clients (`tests/conftest.py`).
- `ruff` lint; both run in GitHub Actions on every push (`.github/workflows/ci.yml`).

## 6. Known limitations / next steps
- Filter extraction is substring matching on known category names (see the issues table above).
- Uses `weaviate-client` v3 API; migrating to v4 is a future task.
- No evaluation set yet for retrieval quality (precision@k) or answer faithfulness.
