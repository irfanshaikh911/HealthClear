import sys
import io
import json
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return json.loads(r.read())


def sep(label):
    print()
    print("=" * 55)
    print(f"  {label}")
    print("=" * 55)


# ── TEST 1: /chat anonymous start ────────────────────────────────────────────
sep("TEST 1: /chat - anonymous session start")
r = post("/chat", {})
print("session_id :", r["session_id"][:8] + "...")
print("question   :", r.get("question"))
print("options    :", r.get("options", []))
sid = r["session_id"]

# ── TEST 2: /chat answer first question ──────────────────────────────────────
sep("TEST 2: /chat - answer procedure question")
r2 = post("/chat", {"session_id": sid, "answer": "Knee Replacement"})
print("next question :", r2.get("question"))
print("question_key  :", r2.get("question_key"))

# ── TEST 3: /rag-chat start ───────────────────────────────────────────────────
sep("TEST 3: /rag-chat - start anonymous session")
r3 = post("/rag-chat", {})
rsid = r3["session_id"]
print("session_id    :", rsid[:8] + "...")
print("reply         :", r3["reply"][:180])
print("missing count :", len(r3["missing_fields"]))

# ── TEST 4: /rag-chat natural turn 1 ─────────────────────────────────────────
sep("TEST 4: /rag-chat - rich natural message")
r4 = post(
    "/rag-chat",
    {
        "session_id": rsid,
        "message": (
            "I need knee replacement surgery in Pune. "
            "I am 52 years old male. I have diabetes and I don't smoke."
        ),
    },
)
print("reply     :", r4["reply"][:220])
print("collected :", r4["collected"])
print("missing   :", r4["missing_fields"])

# ── TEST 5: /rag-chat turn 2 ─────────────────────────────────────────────────
sep("TEST 5: /rag-chat - turn 2 (remaining fields)")
r5 = post(
    "/rag-chat",
    {
        "session_id": rsid,
        "message": "I have private insurance, budget around 2 lakh, I prefer a private room",
    },
)
print("reply        :", r5["reply"][:220])
print("collected    :", r5["collected"])
print("missing      :", r5["missing_fields"])
print("is_complete  :", r5["is_complete"])

current = r5
for turn_num in range(3, 7):
    if current["is_complete"]:
        break
    sep(f"TEST 5.{turn_num}: /rag-chat - extra turn {turn_num}")
    extra = post("/rag-chat", {"session_id": rsid, "message": "private insurance, 200000 budget, private room"})
    print("reply    :", extra["reply"][:200])
    print("collected:", extra["collected"])
    print("missing  :", extra["missing_fields"])
    print("complete :", extra["is_complete"])
    current = extra

# ── Print final result if we got one ─────────────────────────────────────────
if current.get("result"):
    sep("FINAL RESULT")
    res = current["result"]
    ps = res.get("personalized_summary", {})
    print("cost_range           :", ps.get("estimated_cost_range"))
    print("budget_fit           :", ps.get("budget_fit"))
    print("insured_hospital_cnt :", ps.get("insurance_accepted_count", 0))
    print("insurance_note       :", ps.get("insurance_note", ""))
    print()
    print("Hospital ranking (with insurance breakdown):")
    for h in res.get("hospital_comparison", []):
        ins_flag = "✅" if h.get("insurance_accepted") else "❌"
        print(
            f"  {h['hospital_name']:<35} "
            f"total=₹{h['personalized_cost']:>9,.0f}  "
            f"covered=₹{h.get('amount_covered', 0):>9,.0f}  "
            f"out-of-pocket=₹{h.get('patient_out_of_pocket', h['personalized_cost']):>9,.0f}  "
            f"ins={ins_flag}  score={h['value_score']:.2f}"
        )
    print()
    print("AI explanation:", res.get("ai_explanation", "")[:300])
else:
    print("\n[!] No final result yet — collected:", current.get("collected"))

# ── TEST 6: history route collision check ─────────────────────────────────────
sep("TEST 6: GET /history/patient/999 (should 404)")
try:
    get("/history/patient/999")
    print("ERROR: should have returned 404")
except urllib.error.HTTPError as e:
    print("Correctly 404d:", e.code)

sep("TEST 7: GET /history/<session_id>")
try:
    h = get(f"/history/{rsid}")
    print("session_id :", h.get("session_id", "")[:8])
    print("messages   :", len(h.get("messages", [])), "turns")
    print("answers    :", list(h.get("answers", {}).keys()))
    print("has_result :", bool(h.get("result")))
except urllib.error.HTTPError as e:
    print("ERROR:", e.code, e.reason)

print()
print("ALL TESTS DONE")
