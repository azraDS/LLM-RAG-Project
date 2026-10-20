# Fashion Assistant — RAG chatbot for an online fashion store

A Streamlit chat app that answers shopper questions with **retrieval-augmented generation**: an LLM router classifies each message, product questions are answered from a **Weaviate** vector database (hybrid BM25 + semantic search over 854 cleaned Flipkart products), store-policy questions are answered from a knowledge document, and everything else gets a polite small-talk reply.

![App flow](app/App_Flow_Schema.png)

> **Design & data processing:** see [docs/DESIGN.md](docs/DESIGN.md).

## Features
- **Intent routing** – `product_search`, `product_question`, `website_question`, `other`.
- **Hybrid retrieval** – Weaviate hybrid search (keyword + `text-embedding-3-small` vectors).
- **Grounded answers** – prompts instruct the model to use only retrieved products / the policy document.
- **Short-term memory** – recent turns are passed back as context.
- **Reproducible data pipeline** – raw JSON → cleaned JSON-lines → embedded in Weaviate.

## Quick start (Docker — recommended)
Prerequisites: [Docker](https://www.docker.com/products/docker-desktop/) and an OpenAI API key.

```bash
cp .env.example .env            # then put your OPENAI_API_KEY in .env
docker-compose up -d --build    # starts Weaviate + the app
```
Open http://localhost:8501 (set `APP_PORT=8502` in `.env` if 8501 is taken).

First run only — clean the data and build the vector index (`make pipeline`, or by hand):
```bash
docker-compose run --rm app python scripts/process_data.py
docker-compose run --rm app python scripts/create_schema.py
docker-compose run --rm app python scripts/ingest_data.py
```
The full dataset (854 products, ~4 min, a few cents of embeddings) is git-ignored. On a fresh clone
the pipeline automatically uses the committed 60-product sample in `data/sample/`, so everything
works out of the box; drop `balanced_data.json` into `data/` to use the full set.
Weaviate's state lives in `./weaviate_data/` (git-ignored) and survives restarts. Stop with `docker-compose down`.

## Local development (without Docker for the app)
Requires Python 3.10+ (tested on 3.12 and 3.13).
```bash
python -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -e ".[dev]"
docker-compose up -d weaviate                       # only the database
streamlit run app/streamlit_app.py
```

## Data pipeline
| Step | Command | What it does |
|------|---------|--------------|
| 1. Clean | `python scripts/process_data.py` | `data/balanced_data.json` → `data/modified_balanced_data.json` (flattens the nested `product_details` into text) |
| 2. Schema | `python scripts/create_schema.py` | Creates the `Product` class with the OpenAI vectorizer |
| 3. Ingest | `python scripts/ingest_data.py` | Embeds and loads the products (resumable) |

Exploration and the dataset-balancing work are in `notebooks/` (`pip install -e ".[notebooks]"`, see its README). Helper scripts: `check_openai_key.py`, `check_weaviate_schema.py`, `check_weaviate_data.py`, `check_search.py`, `delete_product_class.py`.

## Project layout
```
src/fashion_rag/   config.py (settings), clients.py, assistant.py (router + RAG), processing.py, data.py
app/               streamlit_app.py (UI only)
scripts/           pipeline + diagnostic CLIs
tests/             offline unit tests (fake OpenAI / Weaviate clients)
data/              website policy text + sample/ (full datasets are git-ignored)
notebooks/         data analysis & preprocessing (datasets git-ignored)
docs/              DESIGN.md — architecture, data processing, decisions
weaviate_data/     Weaviate persistence (git-ignored)
```

## Configuration
All settings are environment variables (see `.env.example`). Only `OPENAI_API_KEY` is required.
`WEAVIATE_URL` defaults to `http://localhost:8080`; Docker Compose sets it to `http://weaviate:8080` for the app container.

## Tests & quality
```bash
make test     # pytest — no network or API key needed
make lint     # ruff
```
CI runs both on every push.

## Deploying to EC2
Install Docker + the compose plugin, clone the repo, create `.env`, run `docker-compose up -d --build`, restore or rebuild the index (above), and open port 8501 in the security group. Put a reverse proxy (Caddy/nginx) with HTTPS in front before sharing it publicly, since the app spends your OpenAI credits.
