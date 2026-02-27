# IMPACT ASSESSMENT REPORT

> **Classification:** GxP Controlled Document
> **Regulatory Framework:** GAMP 5 Rev 2 | 21 CFR Part 11 | ICH Q10
> **Retention Period:** Minimum 5 years post-system retirement

---

## Document Control

| Field | Value |
|-------|-------|
| **IAR ID** | `IAR-{{YYYYMMDD}}-{{DIFF_HASH_8}}` |
| **Project** | {{PROJECT_NAME}} |
| **System / Application** | EVOLV — The Validation Factory |
| **Traceability Graph** | `{{GRAPH_ID}}` |
| **Reference Diff Hash** | `{{DIFF_HASH}}` |
| **Date Generated** | {{DATE}} |
| **Time (UTC)** | {{TIME}} |
| **Prepared By** | {{AUTHOR}} |
| **Document Status** | DRAFT — Pending QA Review |

---

## 1. Change Summary

_Provide a complete, plain-English description of the change. This section
must be understandable to a regulatory inspector who is not a software
engineer. Avoid implementation jargon where possible._

| Attribute | Value |
|-----------|-------|
| **Change Type** | `{{CHANGE_TYPE}}` _(Enhancement / Defect Fix / Configuration Change / New Feature)_ |
| **GxP Classification** | `{{GXP_CLASSIFICATION}}` _(GxP Direct / GxP Indirect / GxP None)_ |
| **Files Modified** | `{{FILE_COUNT}}` |
| **Functions Affected** | `{{FUNCTION_COUNT}}` |

### 1.1 Overview

{{CHANGE_OVERVIEW}}

> **Guidance:** State what the system does differently after this change compared
> to before. Use the format: "Prior to this change, [behaviour]. Following this
> change, [new behaviour]."

### 1.2 Technical Detail

{{TECHNICAL_DETAIL}}

> **Guidance:** Name the specific module(s), class(es), and function(s) modified.
> Describe at the code level what was altered (e.g., algorithm, data structure,
> API contract, configuration value).

### 1.3 Modified Files

| # | File Path | Lines Added | Lines Removed | Functions Modified |
|---|-----------|-------------|---------------|--------------------|
| 1 | `{{FILE_PATH_1}}` | {{LINES_ADDED_1}} | {{LINES_REMOVED_1}}` | `{{FUNCTIONS_1}}` |

### 1.4 Modified Functions

| Function | Class | Module | Criticality Override |
|----------|-------|--------|----------------------|
| `{{FUNCTION_NAME}}` | `{{CLASS_NAME}}` | `{{MODULE_ID}}` | {{OVERRIDE}} |

---

## 2. Risk Impact Assessment

> **Formula:** Impact Score = Criticality × Scope
> Criticality: High=3, Medium=2, Low=1
> Scope ∈ [0.0, 1.0]: `0.6 × (lines_changed / LINE_CAP) + 0.4 × (changed_fns / tracked_fns)`
> Bands: CRITICAL (>2.4) | HIGH (>1.8) | MEDIUM (>1.0) | LOW (≤1.0)

| # | Requirement ID | Title | Risk Level | GxP | Criticality | Scope | **Impact Score** | Band |
|---|---------------|-------|------------|-----|-------------|-------|-----------------|------|
| 1 | `{{REQ_ID}}` | {{REQ_TITLE}} | {{RISK_LEVEL}} | {{GXP_CAT}} | {{CRIT}} | {{SCOPE}} | **{{SCORE}}** | **{{BAND}}** |

---

## 3. In-Scope Tests — Required Re-Execution

_The following test scripts must be re-executed and formally documented before
the change may be considered in a validated state. Failure to execute any
in-scope script constitutes a deviation requiring CAPA under 21 CFR Part 11._

### 3.N `{{SCRIPT_ID}}` — {{SCRIPT_TITLE}}

| Field | Value |
|-------|-------|
| **Phase** | {{PHASE}} _(IQ / OQ / PQ / UAT / Informal)_ |
| **Execution Priority** | {{PRIORITY}} _(Critical / High / Medium / Low)_ |
| **Automation Status** | {{AUTOMATION}} _(Automated / Semi-Automated / Manual)_ |

**Justification:**

> {{IN_SCOPE_JUSTIFICATION}}
>
> _Guidance: Explain precisely which validated behaviour is at risk. Reference
> the specific function or algorithm that changed. State the consequence of not
> re-running (e.g., "Failure to re-execute would leave unverified the correctness
> of [specific behaviour] under the validated configuration.")_

**Regulatory Basis:** _{{REGULATORY_BASIS_IN_SCOPE}}_

---

## 4. Exclusion Rationale

_The following modules share requirements with the changed code but have NOT
been directly modified. Each exclusion must be formally justified and defensible
under regulatory inspection. Exclusions are governed by GAMP 5 Section 8.3.3:
"Impact assessment shall consider the scope of the change; unaffected functional
paths do not require re-qualification."_

> **Note:** An exclusion is NOT a statement that the module is unimportant.
> It is a formal finding that the specific change does not alter the module's
> functional path and therefore requalification is not warranted at this time.

### 4.N `{{MODULE_ID}}` — `{{FILE_PATH}}`

**Module Description:** {{MODULE_DESCRIPTION}}

**Shared Requirements with Changed Code:** `{{SHARED_REQ_IDS}}`

**Exclusion Rationale:**

> {{EXCLUSION_RATIONALE}}
>
> _Guidance: The rationale MUST:_
> _1. Name the unchanged internal logic (e.g., "The SHA-256 hashing algorithm,_
>    _append-only write mechanism, and CSV column schema were not modified.")_
> _2. Explain why the change cannot affect this module's outputs_
>    _(e.g., "This module consumes the output of the changed module as an_
>    _opaque string; its processing logic is input-agnostic.")_
> _3. Cite a regulatory basis for the exclusion principle._

**Regulatory Basis:** _{{REGULATORY_BASIS_EXCLUSION}}_

---

## 5. Regulatory Conclusion

{{REGULATORY_CONCLUSION}}

> **Risk Acceptance Statement:** {{RISK_ACCEPTANCE_STATEMENT}}

---

## 6. Related Documentation

| Document Type | Document ID / Reference | Status |
|---------------|-------------------------|--------|
| Traceability Graph | `{{GRAPH_ID}}` | Current |
| Change Request | {{CHANGE_REQUEST_ID}} | Approved |
| CAPA (if applicable) | {{CAPA_ID}} | N/A |
| URS for affected requirements | {{URS_IDS}} | Approved |
| Previous Validation Report | {{PREVIOUS_VAL_REPORT}} | Superseded |

---

## 7. Sign-Off

_This Impact Assessment Report must be reviewed and approved by the listed
roles before the change may be deployed to the validated environment.
Electronic signatures are governed by 21 CFR Part 11.100–11.300._

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By (CSV / Validation Engineer) | | | |
| Peer Reviewed By (CSV Engineer) | | | |
| Reviewed By (Quality Assurance) | | | |
| Approved By (System Owner / Business Owner) | | | |

---

## Appendix A — Traceability Matrix Excerpt

_List all Traceability Graph links relevant to this change for cross-reference._

| Link ID | Requirement | Module | Test Scripts | Impact Type |
|---------|-------------|--------|-------------|-------------|
| `{{LINK_ID}}` | `{{REQ_ID}}` | `{{MODULE_ID}}` | `{{SCRIPT_IDS}}` | {{IMPACT_TYPE}} |

---

## Appendix B — Impact Formula Reference

```
Impact Score = Criticality × Scope

Criticality:
    High   = 3  (GxP Direct, patient safety, regulatory compliance)
    Medium = 2  (Quality, traceability, audit-relevant)
    Low    = 1  (Administrative, non-GxP)

Scope ∈ [0.0, 1.0]:
    scope = (0.6 × line_factor) + (0.4 × function_factor)

    line_factor     = min(1.0, lines_changed / LINE_CAP)
                      LINE_CAP = 80 (configurable)

    function_factor = |changed_functions ∩ tracked_functions|
                      ─────────────────────────────────────────
                      max(1, |all_tracked_functions_in_module|)

Risk Bands:
    CRITICAL : score > 2.4   → Mandatory immediate escalation
    HIGH     : score > 1.8   → Senior QA review required
    MEDIUM   : score > 1.0   → Standard QA review
    LOW      : score ≤ 1.0   → Self-review with documentation
```

---

_Generated by EVOLV Sentinel — Justification Engine_
_Powered by EVOLV | A WingstarTech Inc. Product_
