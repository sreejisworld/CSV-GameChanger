# User Requirements Specification (URS)

**Project:** Laboratory Equipment Calibration System
**Generated:** 2026-01-28 18:33:04 UTC
**Total Requirements:** 10

---

## Requirements Table

| URS ID | Requirement Statement | Criticality | Regulatory Rationale |
|--------|----------------------|-------------|---------------------|
| URS-7.1 | The system shall track calibration schedules for all laboratory equipment. | High | Per Validating AI systems in GMP.pdf (p.35): manual procedure...” 
◦ Also include a step to periodically verify the system: maybe once a week, run ... |
| URS-7.2 | The system shall record calibration results with timestamps and technician ID. | High | Per GAMP DI Guide.pdf (p.36): risk of data transcription error. Appropriately controlled and synchronized clocks should be available for recording ... |
| URS-7.3 | The system shall generate calibration certificates. | High | Per GAMP DI Guide.pdf (p.99): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® ... |
| URS-7.4 | The system shall send alerts when calibration is due or overdue. | High | Per Validating AI systems in GMP.pdf (p.80): the annex expects you to detect that. You might set statistical triggers – 
e.g., if the model starts ... |
| URS-7.5 | The system shall maintain audit trail of all calibration activities. | High | Per GAMP DI Guide.pdf (p.80): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 78 ISP... |
| URS-7.6 | The system shall store equipment specifications and calibration procedures. | High | Per GAMP DI Guide.pdf (p.137): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP®... |
| URS-7.7 | The system shall support electronic signatures for calibration approval. | High | Per GAMP DI Guide.pdf (p.108): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 106 I... |
| URS-7.8 | The system shall generate compliance reports for regulatory audits. | High | Per Validating AI systems in GMP.pdf (p.54): • alerts for unusual patterns 
 • conﬁdence spread graphs 
 • feature drift heat-maps 
Why GMP teams l... |
| URS-7.9 | The system shall manage calibration service providers and vendors. | High | Per Validating AI systems in GMP.pdf (p.33): We’d audit/document vendor qualiﬁcations: Did they develop the model under a 
quality system? Can they... |
| URS-7.10 | The system shall track equipment out-of-tolerance events and corrective actions. | High | Per GAMP DI Guide.pdf (p.84): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 82 ISP... |

---

## Detailed Requirements

### URS-7.1

**Requirement Statement:**
> The system shall track calibration schedules for all laboratory equipment.

**Criticality:** High

**Regulatory Rationale:**
> Per Validating AI systems in GMP.pdf (p.35): manual procedure...” 
◦ Also include a step to periodically verify the system: maybe once a week, run a 
control plate or have an analyst double-count one plate to ensure it’s still 
working. 
◦ Analy... | Per Validating AI systems in GMP.pdf (p.33): We’d audit/document vendor qualiﬁcations: Did they develop the model under a 
quality system? Can they provide validation data? For example, vendor might have a 
spec “99% accurate on standard colony ... | Per Validating AI systems in GMP.pdf (p.69): • cluster structures 
 • feature correlations 
 • sensor baseline noise levels 
 • instrument signature patterns 
 • seasonal variations if relevant 
This becomes your reference distribution. 
Practic...

---

### URS-7.2

**Requirement Statement:**
> The system shall record calibration results with timestamps and technician ID.

**Criticality:** High

**Regulatory Rationale:**
> Per GAMP DI Guide.pdf (p.36): risk of data transcription error. Appropriately controlled and synchronized clocks should be available for recording 
timed events [8]. Time and date stamps used should be explicit within the context ... | Per GAMP DI Guide.pdf (p.98): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 96 ISPE GAMP® Guide:
Appendix D1 Records and Data Int egrity
# Requirement
11 The system ... | Per GAMP DI Guide.pdf (p.91): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 89
Records and Data Integrity Appendix M6
• Record and data maintenance...

---

### URS-7.3

**Requirement Statement:**
> The system shall generate calibration certificates.

**Criticality:** High

**Regulatory Rationale:**
> Per GAMP DI Guide.pdf (p.99): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 97
Records and Data Integrity Appendix D1
# Requirement
5 Validation do... | Per GAMP DI Guide.pdf (p.88): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 86 ISPE GAMP® Guide:
Appendix M6 Records and Data Int egrity
Regulatory inspectors may wa... | Per Validating AI systems in GMP.pdf (p.33): We’d audit/document vendor qualiﬁcations: Did they develop the model under a 
quality system? Can they provide validation data? For example, vendor might have a 
spec “99% accurate on standard colony ...

---

### URS-7.4

**Requirement Statement:**
> The system shall send alerts when calibration is due or overdue.

**Criticality:** High

**Regulatory Rationale:**
> Per Validating AI systems in GMP.pdf (p.80): the annex expects you to detect that. You might set statistical triggers – 
e.g., if the model starts getting a lot of “out of scope” inputs or if 
outcomes change signiﬁcantly, that signals it’s time... | Per Validating AI systems in GMP.pdf (p.70): 1.   Distribution Monitoring (Data Drift Detection) 
You track whether today’s inputs statistically differ from baseline. 
Metrics: 
 • PSI (Population Stability Index) 
 • KL divergence 
 • KS statis... | Per Validating AI systems in GMP.pdf (p.71): Validating AI Systems in GMP: A Beginner’s Guide for CSV Professionals
3.   Performance Drift Monitoring (Most Important) 
You check whether the model is still accurate. 
 • accuracy per failure mode ...

---

### URS-7.5

**Requirement Statement:**
> The system shall maintain audit trail of all calibration activities.

**Criticality:** High

**Regulatory Rationale:**
> Per GAMP DI Guide.pdf (p.80): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 78 ISPE GAMP® Guide:
Appendix M4 Records and Data Int egrity
Audit trail information on p... | Per GAMP DI Guide.pdf (p.78): etc). Audit trails may be reviewed as a list of relevant data, or by a validated ‘exception reporting’ process. QA 
should also review a sample of relevant audit trails, raw data and metadata as part ... | Per GAMP DI Guide.pdf (p.81): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 79
Records and Data Integrity Appendix M4
9.4 Audit Trail Review
There ...

---

### URS-7.6

**Requirement Statement:**
> The system shall store equipment specifications and calibration procedures.

**Criticality:** High

**Regulatory Rationale:**
> Per GAMP DI Guide.pdf (p.137): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 135
Records and Data Integrity Appendix O2
The use of spreadsheets shou... | Per GAMP AI Guide.pdf (p.75): 7.3.5 Specifications
“For product development, the supplier should document the functionality and design of the system to meet the 
defined requirements. This should cover software, hardware, and conf... | Per GAMP DI Guide.pdf (p.91): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 89
Records and Data Integrity Appendix M6
• Record and data maintenance...

---

### URS-7.7

**Requirement Statement:**
> The system shall support electronic signatures for calibration approval.

**Criticality:** High

**Regulatory Rationale:**
> Per GAMP DI Guide.pdf (p.108): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 106 ISPE GAMP® Guide:
Appendix D3 Records and Data Int egrity
Within the US regulatory fr... | Per GAMP DI Guide.pdf (p.109): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 107
Records and Data Integrity Appendix D3
• Method of display or print...

---

### URS-7.8

**Requirement Statement:**
> The system shall generate compliance reports for regulatory audits.

**Criticality:** High

**Regulatory Rationale:**
> Per Validating AI systems in GMP.pdf (p.54): • alerts for unusual patterns 
 • conﬁdence spread graphs 
 • feature drift heat-maps 
Why GMP teams like it: 
You can export PDF snapshots monthly into your QMS to satisfy compliance. 
⸻ 
2. CSV-Read... | Per GAMP DI Guide.pdf (p.83): be explained as if it was being presented to a regulatory inspector. This can highlight any confusion about where 
the data resides and how it passes from one system to another, and may identify areas...

---

### URS-7.9

**Requirement Statement:**
> The system shall manage calibration service providers and vendors.

**Criticality:** High

**Regulatory Rationale:**
> Per Validating AI systems in GMP.pdf (p.33): We’d audit/document vendor qualiﬁcations: Did they develop the model under a 
quality system? Can they provide validation data? For example, vendor might have a 
spec “99% accurate on standard colony ... | Per GAMP AI Guide.pdf (p.47): 4.4.2 Service Management and Performance Monit oring
“The support required for each system, and how it will be provided, should be established.” [2] In addition to non-AI-
enabled computerized systems... | Per GAMP DI Guide.pdf (p.117): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
ISPE GAMP® Guide: Page 115
Records and Data Integrity Appendix D4
• In addition, staff at the ...

---

### URS-7.10

**Requirement Statement:**
> The system shall track equipment out-of-tolerance events and corrective actions.

**Criticality:** High

**Regulatory Rationale:**
> Per GAMP DI Guide.pdf (p.84): This Document is licensed to
Carlos J. Cabrer
Valrico, FL
ID number: 1568
Downloaded on: 6/19/19 11:34 AM
Page 82 ISPE GAMP® Guide:
Appendix M5 Records and Data Int egrity
• Look for invalidated Out o... | Per Validating AI systems in GMP.pdf (p.72): Validating AI Systems in GMP: A Beginner’s Guide for CSV Professionals
 • Drift in PCA visualizations of raw signals 
 • Model repeatedly mislabeled “agitation jitter” as “oxygen depletion” 
Drift con... | Per GAMP AI Guide.pdf (p.193): • Handling outliers
• Correction of errors in data
For individual use only. © 2025 ISPE. All rights reserved.
Downloaded from https://guidance-docs.ispe.org/ by David Lerner on August 4, 2025.
For per...

---

---

*Generated by CSV-GameChanger URS Drafting Tool*
*Regulatory context sourced from GAMP 5 and CSA documentation*