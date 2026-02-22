import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/assistant/rag-chat"

def send_msg(payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print("Response Body:", e.read().decode('utf-8'))
        return {}
    except Exception as e:
        print("Error:", e)
        return {}

def test_doctor_pathway():
    print("🚀 Initializing new RAG Session...")
    res = send_msg({"patient_id": 1})
    session_id = res.get("session_id")
    print(f"Session ID: {session_id}")
    print(f"AI: {res.get('reply')}")
    print(f"Options: {res.get('suggested_options')}")

    steps = [
        "I have a mild headache",
        "It started a few days ago",
        "Pune",
        "Under ₹1,000",
        "No insurance",
        "No, first time",
        "Cheapest"
    ]

    for answer in steps:
        print(f"\nUser: {answer}")
        res = send_msg({
            "session_id": session_id,
            "message": answer
        })
        print(f"AI: {res.get('reply')}")
        print(f"Options: {res.get('suggested_options')}")
        
        if res.get("is_complete"):
            print("\n✅ Session Complete!")
            doc_res = res.get("doctor_result")
            if doc_res:
                print(f"Recommendation Type: {res.get('recommendation_type')}")
                print(f"Specialization: {doc_res.get('specialization')}")
                for d in doc_res.get("doctors", []):
                    print(f"  - Dr. {d.get('doctor_name')} ({d.get('consultation_fee')})")
            else:
                print("❌ No doctor_result found in response!")
            break
        
        time.sleep(1)

if __name__ == "__main__":
    test_doctor_pathway()
