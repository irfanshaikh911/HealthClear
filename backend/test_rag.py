import httpx
import json

base_url = "http://127.0.0.1:8000/api/assistant/rag-chat"

def test_flow():
    out = {}
    print("Starting session with patient_id 1...", flush=True)
    resp = httpx.post(base_url, json={"patient_id": 1, "message": ""}, timeout=120.0)
    data = resp.json()
    session_id = data.get("session_id")
    out["step1"] = data

    print("Sending 'i have thyriod and need to treat it'", flush=True)
    resp2 = httpx.post(base_url, json={"session_id": session_id, "message": "i have thyriod and need to treat it"}, timeout=120.0)
    data2 = resp2.json()
    out["step2"] = data2

    print("Sending 'Find a doctor for me'", flush=True)
    resp3 = httpx.post(base_url, json={"session_id": session_id, "message": "Find a doctor for me"}, timeout=120.0)
    data3 = resp3.json()
    out["step3"] = data3

    print("Sending 'started today - very urgent'", flush=True)
    resp4 = httpx.post(base_url, json={"session_id": session_id, "message": "started today - very urgent"}, timeout=120.0)
    data4 = resp4.json()
    out["step4"] = data4

    print("Sending 'im in Pune'", flush=True)
    resp5 = httpx.post(base_url, json={"session_id": session_id, "message": "im in Pune"}, timeout=120.0)
    data5 = resp5.json()
    out["step5"] = data5

    print("Sending 'budget is 1000_10000, have no insurance'", flush=True)
    resp6 = httpx.post(base_url, json={"session_id": session_id, "message": "budget is 1000_10000, have no insurance"}, timeout=120.0)
    data6 = resp6.json()
    out["step6"] = data6
    
    print("Sending 'highly experienced'", flush=True)
    resp7 = httpx.post(base_url, json={"session_id": session_id, "message": "highly experienced"}, timeout=120.0)
    data7 = resp7.json()
    out["step7"] = data7
    
    print("Sending 'No, first time seeking help'", flush=True)
    resp8 = httpx.post(base_url, json={"session_id": session_id, "message": "No, first time seeking help"}, timeout=120.0)
    data8 = resp8.json()
    out["step8"] = data8

    with open("test_out.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Success! Wrote to test_out.json")

if __name__ == "__main__":
    test_flow()
