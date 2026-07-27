import zipfile
import os
import time
import pandas as pd
import chromadb
from tqdm import tqdm

client_db = chromadb.PersistentClient(path="./chroma_db")

collection = client_db.get_or_create_collection("yc_startups")
user_collection = client_db.get_or_create_collection("user_generated_startups")

# FIX 5: New collection for Indian startup funding rounds
india_funding_collection = client_db.get_or_create_collection("india_funding_rounds")


# ==========================================
# FIX 5: INDIA FUNDING CSV LOADER & RETRIEVAL
# ==========================================

def load_india_funding_data():
    """
    Loads startup_funding.csv (3,044 Indian startup funding rounds) into ChromaDB.
    Each document contains: startup name, industry, city, investor, round type, and amount.
    """
    if india_funding_collection.count() > 0:
        print(f"[India Funding DB] Already loaded ({india_funding_collection.count()} rounds)")
        return

    csv_path = "startup_funding.csv"
    if not os.path.exists(csv_path):
        print(f"[India Funding DB] {csv_path} not found — skipping.")
        return

    try:
        df = pd.read_csv(csv_path, encoding="latin1")
        df = df.fillna("")

        documents = []
        ids = []

        for idx, row in df.iterrows():
            name = str(row.get("Startup Name", "")).strip()
            industry = str(row.get("Industry Vertical", "")).strip()
            subvertical = str(row.get("SubVertical", "")).strip()
            city = str(row.get("City  Location", "")).strip()
            investors = str(row.get("Investors Name", "")).strip()
            round_type = str(row.get("InvestmentnType", "")).strip()
            amount = str(row.get("Amount in USD", "")).strip()
            date = str(row.get("Date dd/mm/yyyy", "")).strip()

            if not name or name.startswith("http"):
                continue

            doc = (
                f"Indian Startup: {name}\n"
                f"Industry: {industry} | Sub-vertical: {subvertical}\n"
                f"City: {city}\n"
                f"Investors: {investors}\n"
                f"Round: {round_type} | Amount (USD): {amount}\n"
                f"Date: {date}"
            )
            documents.append(doc)
            ids.append(f"india_{idx}")

        batch_size = 100
        for i in tqdm(range(0, len(documents), batch_size), desc="Loading India funding DB"):
            batch_docs = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            india_funding_collection.add(documents=batch_docs, ids=batch_ids)

        print(f"[India Funding DB] Loaded {len(documents)} funding rounds.")
    except Exception as e:
        print(f"[India Funding DB] Error loading CSV: {e}")


def retrieve_india_funding(query, n_results=5):
    """
    Retrieves similar Indian startup funding rounds from the local ChromaDB.
    Used by Agent 2 to give grounded INR investor benchmarks.
    """
    try:
        count = india_funding_collection.count()
        if count == 0:
            load_india_funding_data()
        n = min(n_results, india_funding_collection.count())
        if n == 0:
            return []
        results = india_funding_collection.query(query_texts=[query], n_results=n)
        return results.get("documents", [[]])[0]
    except Exception as e:
        print(f"[India Funding DB] Query error: {e}")
        return []


def extract_dataset():
    if not os.path.exists("data/extracted"):
        os.makedirs("data/extracted", exist_ok=True)
        if os.path.exists("data/archive (1).zip"):
            with zipfile.ZipFile("data/archive (1).zip", "r") as zip_ref:
                zip_ref.extractall("data/extracted")
            print("Dataset Extracted")
        else:
            print("[WARN] data/archive (1).zip not found.")
    else:
        print("Dataset Already Extracted")


def load_data():
    extract_dataset()
    companies = pd.read_csv("data/extracted/companies.csv")
    industries = pd.read_csv("data/extracted/industries.csv")
    tags = pd.read_csv("data/extracted/tags.csv")
    return companies, industries, tags


def build_documents():
    companies, industries, tags = load_data()

    industry_grouped = (
        industries
        .groupby("id")["industry"]
        .apply(list)
        .reset_index()
    )

    tag_grouped = (
        tags
        .groupby("id")["tag"]
        .apply(list)
        .reset_index()
    )

    merged_df = (
        companies
        .merge(industry_grouped, on="id", how="left")
        .merge(tag_grouped, on="id", how="left")
    )

    merged_df = merged_df.fillna("")
    documents = []

    for _, row in merged_df.iterrows():
        industries_text = ""
        if isinstance(row["industry"], list):
            industries_text = ", ".join(row["industry"])

        tags_text = ""
        if isinstance(row["tag"], list):
            tags_text = ", ".join(row["tag"])

        doc = f"""
Startup Name: {row['name']}
Industries: {industries_text}
Tags: {tags_text}
One Liner: {row['oneLiner']}
Description: {row['longDescription']}
YC Batch: {row['batch']}
Status: {row['status']}
""".strip()
        documents.append(doc)

    return documents


def store_documents():
    if collection.count() > 0:
        print(f"Collection 'yc_startups' already contains {collection.count()} documents")
        return

    documents = build_documents()
    batch_size = 100

    for i in tqdm(range(0, len(documents), batch_size)):
        batch_docs = documents[i:i+batch_size]
        batch_ids = [str(x) for x in range(i, min(i+batch_size, len(documents)))]
        collection.add(documents=batch_docs, ids=batch_ids)

    print("Documents stored successfully")


def retrieve_startups(query, n_results=10):
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results.get("documents", [[]])[0]
    except Exception as e:
        print(f"[retrieve_startups] Error querying YC vector store: {e}")
        return []


# ==========================================
# USER STARTUP MEMORY (CACHING PROJECTS)
# ==========================================

def store_user_startup(blueprint, validation_score=None):
    """
    Saves a generated and validated startup blueprint into the local memory DB.
    Medium Fix 2: Checks for duplicates before storing — if a very similar startup
    already exists in the collection, it is skipped to prevent redundant entries.
    """
    if not blueprint or not isinstance(blueprint, dict):
        return

    name = blueprint.get("startup_name", "Unnamed Startup")
    problem = blueprint.get("problem_statement") or blueprint.get("problem", "")
    solution = blueprint.get("solution", "")
    target_users = blueprint.get("target_users", "")
    revenue_model = blueprint.get("revenue_model", "")

    mvp_features = blueprint.get("mvp_features", [])
    if isinstance(mvp_features, list):
        mvp_features_str = ", ".join(str(f) for f in mvp_features)
    else:
        mvp_features_str = str(mvp_features)

    skills = blueprint.get("skills", "")

    doc_text = f"""
[PAST HACKARENA PROJECT]
Startup Name: {name}
Problem Statement: {problem}
Solution: {solution}
Target Users: {target_users}
Revenue Model: {revenue_model}
MVP Features: {mvp_features_str}
Skills: {skills}
Validation Score: {validation_score or 'N/A'}
""".strip()

    # Medium Fix 2: Deduplication — check if a very similar project already exists
    try:
        count = user_collection.count()
        if count > 0:
            existing = user_collection.query(
                query_texts=[doc_text],
                n_results=1
            )
            existing_docs = existing.get("documents", [[]])[0]
            if existing_docs:
                # Check if the top result already matches this startup name closely
                top_doc = existing_docs[0]
                if f"Startup Name: {name}" in top_doc:
                    print(f"[MEMORY DB] Skipping duplicate — '{name}' already exists in memory collection.")
                    return
    except Exception as e:
        print(f"[MEMORY DB] Dedup check error (non-fatal): {e}")

    doc_id = f"user_{int(time.time())}_{name.replace(' ', '_').lower()[:30]}"

    metadata = {
        "name": str(name)[:100],
        "target_users": str(target_users)[:100],
        "timestamp": str(int(time.time()))
    }

    try:
        user_collection.add(
            documents=[doc_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        print(f"[MEMORY DB] Saved '{name}' to 'user_generated_startups' memory collection.")
    except Exception as e:
        print(f"[MEMORY DB] Error saving startup to memory DB: {e}")



def retrieve_similar_user_startups(query, n_results=3):
    """
    Retrieves similar past projects generated by HackArena founders from the memory DB.
    """
    try:
        count = user_collection.count()
        if count == 0:
            return []

        n = min(n_results, count)
        results = user_collection.query(
            query_texts=[query],
            n_results=n
        )
        return results.get("documents", [[]])[0]
    except Exception as e:
        print(f"[MEMORY DB] Error retrieving similar user startups: {e}")
        return []


if __name__ == "__main__":
    store_documents()
    startups = retrieve_startups("AI startup for students")
    print("\nRetrieved Startups:\n")
    for startup in startups[:2]:
        print(startup[:500])
        print("=" * 80)
