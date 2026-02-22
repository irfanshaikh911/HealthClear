from app.db.supabase import get_supabase
import asyncio

def run():
    client = get_supabase()
    res = client.table("doctor").select("*").execute()
    for row in res.data:
        print(row)
    print("Total:", len(res.data))

if __name__ == "__main__":
    run()
