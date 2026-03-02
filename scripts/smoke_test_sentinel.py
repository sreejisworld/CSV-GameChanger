"""
EVOLV Sentinel — Smoke Test
============================
Run from project root:
    python scripts/smoke_test_sentinel.py

Exercises the Impact Engine with two synthetic git diffs:
1. A HIGH-impact change to _determine_criticality (core GxP logic)
2. A LOW-impact change to a comment-only edit in delta_agent.py
"""
import json
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agents.sentinel.impact_engine import ImpactEngine

GRAPH_PATH = Path("Agents/sentinel/traceability_sample.json")

# ---------------------------------------------------------------------------
# Synthetic diffs
# ---------------------------------------------------------------------------

DIFF_HIGH_IMPACT = """\
diff --git a/Agents/requirement_architect.py b/Agents/requirement_architect.py
index a1b2c3d..d4e5f6a 100644
--- a/Agents/requirement_architect.py
+++ b/Agents/requirement_architect.py
@@ -120,12 +120,15 @@ def _determine_criticality(self, text: str):
-        high_kw = ["patient", "safety", "gxp", "sterile", "clinical"]
+        high_kw = [
+            "patient", "safety", "gxp", "sterile", "clinical",
+            "life-sustaining", "adverse event", "pharmacovigilance",
+        ]
         medium_kw = ["quality", "audit", "calibration", "deviation"]
-        low_kw  = ["admin", "convenience"]
+        low_kw = ["admin", "convenience", "reporting"]
         text_lower = text.lower()
-        if any(kw in text_lower for kw in high_kw):
+        if any(kw in text_lower for kw in high_kw):
             return "High"
         if any(kw in text_lower for kw in medium_kw):
             return "Medium"
         return "Low"
+
+    # Updated: 2026-02-26 per GAMP 5 Rev 2
diff --git a/Agents/verification_agent.py b/Agents/verification_agent.py
index b2c3d4e..e5f6a7b 100644
--- a/Agents/verification_agent.py
+++ b/Agents/verification_agent.py
@@ -201,8 +201,12 @@ def _check_criticality_alignment(self, urs: dict, chunks):
-        HIGH_RISK_INDICATORS = ["patient", "safety", "gxp"]
+        HIGH_RISK_INDICATORS = [
+            "patient", "safety", "gxp", "sterile",
+            "batch release", "life-sustaining",
+        ]
         req_criticality = urs.get("Criticality", "").lower()
-        if req_criticality in ("low", "medium"):
+        if req_criticality in ("low", "medium"):
             for chunk in chunks:
                 for indicator in HIGH_RISK_INDICATORS:
                     if indicator in chunk.text.lower():
"""

DIFF_LOW_IMPACT = """\
diff --git a/Agents/delta_agent.py b/Agents/delta_agent.py
index c3d4e5f..f6a7b8c 100644
--- a/Agents/delta_agent.py
+++ b/Agents/delta_agent.py
@@ -95,3 +95,4 @@ class DeltaAgent:
     def generate_csa_test_from_ur_fr(self, ur_fr: dict, test_type: str) -> dict:
+        # Minor: updated docstring reference to GAMP 5 Rev 2 Section 6.5
         \"\"\"Generate a CSA test script from a UR/FR document.\"\"\"
"""

DIFF_AUDIT_CRITICAL = """\
diff --git a/Agents/integrity_manager.py b/Agents/integrity_manager.py
index d4e5f6a..a7b8c9d 100644
--- a/Agents/integrity_manager.py
+++ b/Agents/integrity_manager.py
@@ -80,10 +80,14 @@ def log_audit_event(agent_name, action, user_id, decision_logic):
-        row = {
-            "Timestamp": timestamp,
-            "User_ID": user_id or "SYSTEM",
-        }
+        row = {
+            "Timestamp": timestamp,
+            "User_ID": user_id or "SYSTEM",
+            "Session_ID": _get_session_id(),
+        }
@@ -146,6 +150,9 @@ def _compute_reasoning_hash(timestamp, user_id, agent_name, action):
-    raw = f"{timestamp}|{user_id}|{agent_name}|{action}|{decision_logic}"
+    raw = (
+        f"{timestamp}|{user_id}|{agent_name}|{action}"
+        f"|{decision_logic}|{compliance_impact}"
+    )
"""


def run_scenario(label: str, diff: str, engine: ImpactEngine) -> None:
    print(f"\n{'#' * 72}")
    print(f"# SCENARIO: {label}")
    print(f"{'#' * 72}")
    report = engine.analyze(diff)
    engine.print_report(report)

    # Assertions
    assert isinstance(report.summary["at_risk_requirements"], int)
    assert isinstance(report.test_scripts_to_execute, list)
    print(f"  [PASS] {label}\n")


def main() -> None:
    print("Loading traceability graph from:", GRAPH_PATH)
    engine = ImpactEngine.from_file(GRAPH_PATH)

    run_scenario(
        "HIGH IMPACT — Criticality keywords + VerificationAgent change",
        DIFF_HIGH_IMPACT,
        engine,
    )
    run_scenario(
        "LOW IMPACT — Comment-only delta_agent.py edit",
        DIFF_LOW_IMPACT,
        engine,
    )
    run_scenario(
        "CRITICAL IMPACT — Audit trail hash function modified",
        DIFF_AUDIT_CRITICAL,
        engine,
    )

    print("All Sentinel smoke tests passed.")


if __name__ == "__main__":
    main()
