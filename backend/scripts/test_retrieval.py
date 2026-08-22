import os
import sys

# Ensure parent directory is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.services.rag import hybrid_search

def main():
    queries = [
        "landlord not returning my deposit",
        "I want to file an RTI for my ration card status",
        "defective phone, shop won't refund me"
    ]

    print("Running manual retrieval tests...")
    for q in queries:
        print(f"\nQuery: '{q}'")
        results = hybrid_search(q, k=3)
        if not results:
            print("No results found.")
            continue
        
        top = results[0]
        print(f"Top Result Category: {top.get('category')}")
        print(f"Top Result Act Name: {top.get('act_name')}")
        print(f"Top Result Section: {top.get('section')}")
        print(f"Top Result Content: {top.get('content')[:120]}...")

if __name__ == "__main__":
    main()
