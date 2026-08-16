import json
import re
import sys
import time
from pathlib import Path

from src.agent import MaintenanceAgent

QUESTIONS_PATH = Path(__file__).parent / "questions.json"
_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")

def _numbers_in(text: str):
    return [float(n.replace(",", "")) for n in _NUMBER_RE.findall(text)]

def _check_numeric(answer: str, expected: float, tolerance: float) -> bool:
    for n in _numbers_in(answer):
        if abs(n - expected) <= tolerance:
            return True
        if abs(n / 100 - expected) <= tolerance:
            return True
    return False

def _check_contains_any(answer: str, options) -> bool:
    lowered = answer.lower()
    return any(opt.lower() in lowered for opt in options)

def main():
    if not QUESTIONS_PATH.exists():
        print(f"Error: {QUESTIONS_PATH} not found.")
        return 1

    questions = json.loads(QUESTIONS_PATH.read_text())
    session_map = {}
    results = []

    print(f"Starting evaluation suite ({len(questions)} test cases)...\n")

    for i, q in enumerate(questions):
        if i > 0:
            time.sleep(6)  # Pacing to protect free-tier rate limits

        # Handle multi-turn session chaining
        ref = q.get("session_ref")
        if ref and ref in session_map:
            agent = session_map[ref]
        else:
            agent = MaintenanceAgent()
            
        session_map[q["id"]] = agent

        start_time = time.time()
        answer = agent.ask(q["question"])
        latency = round(time.time() - start_time, 2)

        # Evaluate checks
        checks = {}
        if "expected_numeric" in q:
            checks["numeric"] = _check_numeric(answer, q["expected_numeric"], q["tolerance"])
        if "expected_contains_any" in q:
            checks["contains"] = _check_contains_any(answer, q["expected_contains_any"])

        passed = all(checks.values()) if checks else True
        results.append({
            "id": q["id"],
            "category": q["category"],
            "passed": passed,
            "latency": latency,
            "checks": checks,
            "answer": answer
        })

    # Print Report Summary
    print(f"\n{'ID':<15} {'CATEGORY':<22} {'PASS':<6} {'LATENCY':<8} CHECKS")
    print("-" * 75)
    
    n_pass = 0
    n_total = 0
    for r in results:
        n_total += 1
        if r["passed"]:
            n_pass += 1
        print(f"{r['id']:<15} {r['category']:<22} {str(r['passed']):<6} {r['latency']:<8} {r['checks']}")
        
        if not r["passed"]:
            print(f"  -> A: {r['answer'][:200]}...")

    print("-" * 75)
    print(f"Result: {n_pass}/{n_total} evaluation checks passed.")
    return 0 if n_pass == n_total else 1

if __name__ == "__main__":
    sys.exit(main())