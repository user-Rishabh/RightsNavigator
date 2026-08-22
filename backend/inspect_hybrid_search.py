import sys
import os
import traceback
from dotenv import load_dotenv

# Ensure backend root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.services.rag import hybrid_search

def test():
    try:
        fused = hybrid_search("pothole on my road", k=3)
        with open("C:/Users/Anil/.gemini/antigravity-ide/brain/88cc4b6e-8c2b-44f6-983c-7bb8e447a697/inspect_search.txt", "w") as f:
            f.write("=== FUSED DETAILS ===\n")
            for idx, doc in enumerate(fused, 1):
                f.write(f"Doc {idx}: Category={doc.get('category')}, Score={doc.get('similarity_score')}, text={doc.get('content')[:50]}\n")
    except Exception as e:
        with open("C:/Users/Anil/.gemini/antigravity-ide/brain/88cc4b6e-8c2b-44f6-983c-7bb8e447a697/inspect_search.txt", "w") as f:
            f.write(f"ERROR: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    test()
