import os
import json
import sys
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# Ensure parent directory is in path if running from script folder
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load env from backend/.env
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
        sys.exit(1)

    print("Initializing Supabase client...")
    supabase: Client = create_client(supabase_url, supabase_key)

    print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    corpus_path = os.path.join(os.path.dirname(__file__), "..", "app", "data", "statute_corpus.json")
    if not os.path.exists(corpus_path):
        print(f"Error: Statute corpus not found at {corpus_path}")
        sys.exit(1)

    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    print(f"Loaded {len(chunks)} chunks from corpus.")

    # Filter to only ingest rti, consumer_protection, tenant_rights
    allowed_categories = ["rti", "consumer_protection", "tenant_rights"]
    chunks = [c for c in chunks if c["category"] in allowed_categories]
    print(f"Filtered to {len(chunks)} chunks for categories: {allowed_categories}")

    # Group chunks by category to perform idempotent deletes
    categories_to_delete = set(c["category"] for c in chunks)
    for cat in categories_to_delete:
        print(f"Clearing existing database entries for category: {cat}...")
        try:
            supabase.table("statute_chunks").delete().eq("category", cat).execute()
        except Exception as e:
            print(f"Warning during delete for category {cat}: {e}")

    success_count = 0
    for idx, chunk in enumerate(chunks, 1):
        print(f"Processing chunk {idx} of {len(chunks)} ({chunk['category']} - {chunk['act_name']})...")
        
        # Generate embedding
        content = chunk["content"]
        embedding = model.encode(content).tolist()

        # Insert row
        row = {
            "category": chunk["category"],
            "act_name": chunk["act_name"],
            "section": chunk.get("section"),
            "applicable_states": chunk.get("applicable_states", ["all"]),
            "content": content,
            "embedding": embedding
        }

        try:
            supabase.table("statute_chunks").insert(row).execute()
            success_count += 1
        except Exception as e:
            print(f"Error inserting chunk {idx}: {e}")

    print(f"\nIngestion finished successfully. Inserted {success_count} of {len(chunks)} chunks.")

if __name__ == "__main__":
    main()
