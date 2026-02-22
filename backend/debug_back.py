import asyncio
from app.db.supabase import get_supabase
from app.api.assistant import rag_chat
from app.schemas.assistant import RagChatMessage

async def run_debug():
    try:
        client = get_supabase()
        msg = RagChatMessage(patient_id=1, message="")
        res = rag_chat(msg, client=client)
        print("Success!", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
