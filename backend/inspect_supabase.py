import os
import sys
import traceback
from dotenv import load_dotenv

# Ensure backend root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.services.rag import get_supabase

def inspect():
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supabase_status.txt")
    try:
        supabase = get_supabase()
        
        # Test querying government_schemes
        try:
            res = supabase.table("government_schemes").select("*").limit(1).execute()
            data = res.data
            result_str = f"government_schemes table exists! Count response: {data}\n"
        except Exception as e_schemes:
            result_str = f"government_schemes table query failed: {e_schemes}\n"
            
        # Let's list schema if possible or check what RPC functions are available
        try:
            res_rpc = supabase.rpc("match_statute_chunks", {"query_embedding": [0]*384, "match_count": 1}).execute()
            result_str += f"match_statute_chunks RPC verified: {res_rpc.data is not None}\n"
        except Exception as e_rpc:
            result_str += f"RPC match_statute_chunks failed: {e_rpc}\n"

        with open(status_file, "w") as f:
            f.write(result_str)
            
    except Exception as e:
        with open(status_file, "w") as f:
            f.write(f"ERROR: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    inspect()
