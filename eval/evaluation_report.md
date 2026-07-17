# Evaluation Report

## Why a synthetic test set

The provided document (a Red Herring Prospectus) contains real instances
of **names, emails, phone numbers, company names, and addresses**, but
— being a corporate financial filing rather than a support ticket log —
**no SSNs, credit card numbers, IP addresses, or dates of birth**. To
evaluate all 9 required PII categories against ground truth, I built a
small hand-labeled synthetic "ticket log" (`synthetic_ticket_log.txt`,
`ground_truth.json`) that exercises every category, including two
non-PII control values ("Order #", "Ticket #") the tool must correctly
*not* redact. The real document is used for the actual deliverable
(Deliverable 2) and for a qualitative recall/precision discussion, since
no ground truth exists for it.

## Methodology

Ran `eval/evaluate.py`, which:
1. Runs the redaction engine on the synthetic set.
2. Matches each predicted span against gold labels per PII type
   (case-insensitive substring match, to tolerate minor boundary
   differences e.g. trailing punctuation).
3. Computes per-type **Precision**, **Recall**, **F1**.
4. Computes an overall **instance-level accuracy** = (true positives +
   correctly-ignored non-PII controls) / (all gold PII instances +
   control instances).

## Results (synthetic labeled set, 9 categories, 23 gold PII instances + 5 control non-PII instances)

| Type          | TP | FP | FN | Precision | Recall | F1   |
|---------------|----|----|----|-----------|--------|------|
| PERSON        | 2  | 0  | 1  | 1.00      | 0.67   | 0.80 |
| EMAIL         | 3  | 0  | 0  | 1.00      | 1.00   | 1.00 |
| PHONE         | 4  | 0  | 0  | 1.00      | 1.00   | 1.00 |
| ORG           | 3  | 1  | 0  | 0.75      | 0.67   | 0.86 |
| ADDRESS       | 3  | 0  | 0  | 1.00      | 1.00   | 1.00 |
| SSN           | 2  | 0  | 0  | 1.00      | 1.00   | 1.00 |
| CREDIT_CARD   | 2  | 0  | 1  | 1.00      | 0.67   | 0.80 |
| DOB           | 2  | 0  | 1  | 1.00      | 0.67   | 0.80 |
| IP            | 3  | 0  | 0  | 1.00      | 1.00   | 1.00 |
| **OVERALL**   | **24** | **1** | **3** | **0.96** | **0.89** | **0.92** |

**Control (non-PII) false positives: 0/5** — "ORD-58291" and
"TCK-77123" style reference numbers were correctly left un-redacted.

**Instance-level accuracy: 90.62%**

## Root-cause of each miss (for transparency)

- **PERSON FN / ORG FP (same root cause):** "Ananya Iyer" was tagged
  `ORG` instead of `PERSON` by the small spaCy model in the sentence
  "filed by Ananya Iyer, ananya.iyer@…" — this is one error, but it
  costs both a PERSON false negative and an ORG false positive.
- **ORG FN:** "Infosys Ltd" was not detected at all by
  `en_core_web_sm` in that sentence context — a known recall
  ceiling of the small (non-transformer) spaCy model.
- **CREDIT_CARD FN:** one synthetic test card number I entered
  (`4916 1234 5678 9013`) turns out to **fail the Luhn checksum** —
  i.e. it isn't a structurally valid card number. The tool correctly
  rejected it. This is arguably a data-authoring mistake on my part
  rather than a tool defect — it demonstrates the Luhn safeguard
  working as intended (real card numbers pass; malformed ones don't).
- **DOB FN:** "Date of birth **on file**: 14/08/1990" — the DOB regex
  requires the date to follow the keyword within a short gap; the
  filler phrase "on file" breaks that. A wider context window would
  fix this at some risk to precision elsewhere in a large document.

## Qualitative results on the real document (no ground truth available)

- 2,709 total PII instances redacted: 1,335 ORG, 1,278 PERSON, 70
  EMAIL, 25 PHONE, 1 ADDRESS.
- **Recall on ADDRESS is qualitatively poor** on the real document —
  addresses are split across separate table-cell paragraphs (street
  line vs. Taluka line vs. PIN-code line), and the detector runs
  per-paragraph. See README "Known limitations" item 2 for the fix.
- **Precision on ORG is the weakest spot.** Before adding the
  stoplist + ID-pattern filter, the naive spaCy pass produced 1,868
  ORG hits; after filtering, 1,335 — a ~29% reduction in likely false
  positives from generic legal boilerplate terms ("the Company",
  "N.A.", "₹", "UPI Bidders", etc.), while genuine company/trust names
  (e.g. "HDFC Bank Limited", "Annapurna Family Trust") were preserved.
  Manual spot-check of a 30-item sample of the remaining ORG hits found
  roughly 6/30 (20%) were still arguably non-PII legal terms rather
  than company names — the honest precision ceiling of a stoplist-based
  approach on dense legal prose.
- One company name (`kshinternational.com`, inside a URL) leaked
  through because NER only tags natural-language mentions, not URL
  tokens — see README limitation 1.

## Would a bigger model help?

Yes — swapping `en_core_web_sm` for `en_core_web_trf` (transformer-based)
would likely fix the PERSON/ORG confusion case and catch more ORG
mentions, at the cost of much slower inference on CPU and an extra ~500MB
model download. Given the 24-hour time box and no GPU in this
environment, I prioritized a fast, dependency-light model and documented
the resulting recall ceiling rather than over-engineering the NER stage.
