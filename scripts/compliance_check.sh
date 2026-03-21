#!/usr/bin/env bash
# compliance_check.sh — EVOLV CI/CD Compliance Gate
#
# Headless compliance checks that run on every push/PR to validate that
# the EVOLV codebase meets GAMP 5 / 21 CFR Part 11 coding standards.
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed (blocks merge)
#
# :requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.

set -euo pipefail

PASS=0
FAIL=0
ERRORS=()

# ── Helpers ────────────────────────────────────────────────────────
check_pass() { echo "  ✅ $1"; ((PASS++)) || true; }
check_fail() { echo "  ❌ $1"; ((FAIL++)) || true; ERRORS+=("$1"); }

section() { echo; echo "▶ $1"; }

# ── 1. URS Traceability Tags ───────────────────────────────────────
section "URS Traceability — public functions in Agents/ and utils/"

# Find all public functions (def name — not _name) in Agents/ and utils/
# Check that the function is followed by a :requirement: tag within 10 lines
python3 - <<'PYEOF'
import re
import sys
from pathlib import Path

TAG_RE  = re.compile(r":requirement:\s*URS-\d+\.\d+")
FUNC_RE = re.compile(r"^def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\(")

dirs = ["Agents", "utils", "API"]
missing = []

for d in dirs:
    for pyfile in sorted(Path(d).rglob("*.py")):
        lines = pyfile.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            m = FUNC_RE.match(line.strip())
            if not m:
                continue
            func = m.group(1)
            if func.startswith("_") or func.startswith("test_"):
                continue
            window = "\n".join(lines[i:i+10])
            if not TAG_RE.search(window):
                missing.append(f"{pyfile}:{i+1} — {func}()")

if missing:
    for item in missing:
        print(f"  MISSING :requirement: tag — {item}")
    sys.exit(1)
sys.exit(0)
PYEOF

if [ $? -eq 0 ]; then
    check_pass "All public functions have :requirement: URS-X.Y tags"
else
    check_fail "Some public functions missing :requirement: URS-X.Y tags (see above)"
fi

# ── 2. Audit Trail Protection ──────────────────────────────────────
section "Audit Trail Integrity — no direct writes to audit_trail.csv"

if grep -r --include="*.py" \
     -E "open\(['\"]output/audit_trail\.csv" \
     Agents/ API/ utils/ scripts/ frontend/ 2>/dev/null \
   | grep -v "integrity_manager.py" \
   | grep -v "#"; then
    check_fail "Direct writes to audit_trail.csv detected (use log_audit_event() instead)"
else
    check_pass "No direct writes to audit_trail.csv"
fi

# ── 3. Error Codes ─────────────────────────────────────────────────
section "Exception Classes — error_code attribute"

python3 - <<'PYEOF'
import ast, sys
from pathlib import Path

missing = []
for pyfile in sorted(Path("Agents").rglob("*.py")):
    try:
        tree = ast.parse(pyfile.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Look for Exception subclasses
        bases = [getattr(b, "id", "") for b in node.bases]
        if not any("Error" in b or "Exception" in b for b in bases):
            continue
        # Check for error_code class var
        has_code = any(
            isinstance(s, ast.Assign) and
            any(getattr(t, "id", "") == "error_code" for t in s.targets)
            for s in node.body
        )
        if not has_code:
            missing.append(f"{pyfile}:{node.lineno} — {node.name}")

if missing:
    for item in missing:
        print(f"  MISSING error_code — {item}")
    sys.exit(1)
sys.exit(0)
PYEOF

if [ $? -eq 0 ]; then
    check_pass "All Exception classes have error_code attributes"
else
    check_fail "Some Exception classes missing error_code attribute (see above)"
fi

# ── 4. Type Hints ──────────────────────────────────────────────────
section "Type Hints — functions in Agents/ have return annotations"

python3 - <<'PYEOF'
import ast, sys
from pathlib import Path

missing = []
for pyfile in sorted(Path("Agents").rglob("*.py")):
    try:
        tree = ast.parse(pyfile.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        if node.returns is None:
            missing.append(f"{pyfile}:{node.lineno} — {node.name}()")

if missing:
    for item in missing[:10]:  # cap output
        print(f"  MISSING return annotation — {item}")
    if len(missing) > 10:
        print(f"  ... and {len(missing)-10} more")
    sys.exit(1)
sys.exit(0)
PYEOF

if [ $? -eq 0 ]; then
    check_pass "All public Agent functions have return type annotations"
else
    check_fail "Some Agent functions missing return type annotations (see above)"
fi

# ── 5. Branding Check ──────────────────────────────────────────────
section "Branding — no retired names in source files"

RETIRED_NAMES=("Trustme AI" "trustme-ai" "CSV Engine" "csv-engine")
BRAND_FAIL=0
for name in "${RETIRED_NAMES[@]}"; do
    matches=$(grep -r --include="*.py" --include="*.jsx" --include="*.js" \
              -l "$name" . \
              --exclude-dir=node_modules \
              --exclude-dir=.git \
              2>/dev/null || true)
    if [ -n "$matches" ]; then
        echo "  Retired brand '$name' found in: $matches"
        BRAND_FAIL=1
    fi
done

if [ $BRAND_FAIL -eq 0 ]; then
    check_pass "No retired brand names found"
else
    check_fail "Retired brand names detected (see above)"
fi

# ── 6. Hook Scripts Exist ──────────────────────────────────────────
section "Claude Code Hooks — required scripts exist"

HOOK_SCRIPTS=(
    "scripts/protect_audit_trail.py"
    "scripts/log_dev_change.py"
    "scripts/validate_urs_tag.py"
)
for script in "${HOOK_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        check_pass "$script exists"
    else
        check_fail "$script MISSING"
    fi
done

# ── Summary ────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════"
echo " EVOLV Compliance Gate — Results"
echo "════════════════════════════════════════════"
echo " ✅ Passed : $PASS"
echo " ❌ Failed : $FAIL"
echo "════════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
    echo
    echo "FAILED checks:"
    for err in "${ERRORS[@]}"; do
        echo "  • $err"
    done
    echo
    echo "Merge blocked — fix compliance issues before merging."
    exit 1
fi

echo
echo "All compliance checks passed. Safe to merge."
exit 0
