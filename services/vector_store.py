import zipfile
import os

import pandas as pd
import chromadb

from tqdm import tqdm

client_db = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client_db.get_or_create_collection(
    "yc_startups"
)

def extract_dataset():

    if not os.path.exists(
        "data/extracted"
    ):

        os.makedirs(
            "data/extracted",
            exist_ok=True
        )

        with zipfile.ZipFile(
            "data/archive (1).zip",
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                "data/extracted"
            )

        print("Dataset Extracted")

    else:

        print(
            "Dataset Already Extracted"
        )

def load_data():

    extract_dataset()

    companies = pd.read_csv(
        "data/extracted/companies.csv"
    )

    industries = pd.read_csv(
        "data/extracted/industries.csv"
    )

    tags = pd.read_csv(
        "data/extracted/tags.csv"
    )

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
        .merge(
            industry_grouped,
            on="id",
            how="left"
        )
        .merge(
            tag_grouped,
            on="id",
            how="left"
        )
    )

    merged_df = merged_df.fillna("")

    documents = []

    for _, row in merged_df.iterrows():

        industries_text = ""

        if isinstance(
            row["industry"],
            list
        ):
            industries_text = ", ".join(
                row["industry"]
            )

        tags_text = ""

        if isinstance(
            row["tag"],
            list
        ):
            tags_text = ", ".join(
                row["tag"]
            )

        doc = f"""
Startup Name:
{row['name']}

Industries:
{industries_text}

Tags:
{tags_text}

One Liner:
{row['oneLiner']}

Description:
{row['longDescription']}

YC Batch:
{row['batch']}

Status:
{row['status']}
"""

        documents.append(doc)

    return documents

def store_documents():

    if collection.count() > 0:

        print(
            f"Collection already contains {collection.count()} documents"
        )

        return

    documents = build_documents()

    batch_size = 100

    for i in tqdm(
        range(
            0,
            len(documents),
            batch_size
        )
    ):

        batch_docs = documents[
            i:i+batch_size
        ]

        batch_ids = [
            str(x)
            for x in range(
                i,
                min(
                    i+batch_size,
                    len(documents)
                )
            )
        ]

        collection.add(
            documents=batch_docs,
            ids=batch_ids
        )

    print(
        "Documents stored successfully"
    )

def retrieve_startups(
    query,
    n_results=10
):

    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    return results["documents"][0]


if __name__ == "__main__":

    store_documents()

    startups = retrieve_startups(
        "AI startup for students"
    )

    print(
        "\nRetrieved Startups:\n"
    )

    for startup in startups:

        print(startup[:500])

        print("=" * 80)

