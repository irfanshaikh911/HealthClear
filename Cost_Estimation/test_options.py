import sys
import io
import json
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── Start session ─────────────────────────────────────
r = post("/rag-chat", {})
sid = r["session_id"]
print(f"START: next_field={r['next_field']}  options_count={len(r['suggested_options'])}")
print("Options:", r["suggested_options"][:4])

# ── Simulate button-clicks for each field ─────────────
steps = [
    "Knee Replacement",          # selected_procedure
    "46-60",                     # age bucket (maps to 53)
    "Male",                      # gender
    "Pune",                      # city (free text, LLM handles)
    "Diabetes",                  # comorbidities
    "No, I don't smoke",         # smoking option
    "Private Insurance",         # insurance_status option
    "\u20b91,00,000 \u2013 \u20b92,00,000",   # budget option
    "Private Room",              # room_preference option
]

for msg in steps:
    r2 = post("/rag-chat", {"session_id": sid, "message": msg})
    print(
        f"msg [{msg[:28]:28}] -> next={str(r2.get('next_field')):20} "
        f"collected={len(r2.get('collected',{}))} "
        f"opts={r2.get('suggested_options',[])[:2]}"
    )
    if r2.get("is_complete"):
        print("\n[DONE] is_complete=True!")
        res = r2.get("result") or {}
        ps = res.get("personalized_summary", {})
        print("  cost_range:", ps.get("estimated_cost_range"))
        print("  budget_fit:", ps.get("budget_fit"))
        hospitals = res.get("hospital_comparison", [])
        print("  top 3 hospitals:")
        for h in hospitals[:3]:
            print(f"    {h['hospital_name']}: Rs{h['personalized_cost']:,.0f}  score={h['value_score']:.2f}")
        break

print("\nDone.")
