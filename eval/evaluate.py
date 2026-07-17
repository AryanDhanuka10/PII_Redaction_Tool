"""
evaluate.py
------------
Runs the redaction engine on the synthetic labeled ticket-log test set and
scores it against hand-annotated ground truth: precision, recall, F1 per
PII type, plus an overall instance-level accuracy figure and a false-
positive check against the "should NOT match" control list (order/ticket
numbers).

Usage: python evaluate.py
"""
import json
import sys
sys.path.insert(0, "../src")
from pii_engine import PIIMapper, redact_text  # noqa: E402


def normalize(s):
    return " ".join(s.lower().replace("–", "-").split())


def main():
    text = open("synthetic_ticket_log.txt", encoding="utf-8").read()
    gt = json.load(open("ground_truth.json", encoding="utf-8"))

    mapper = PIIMapper()
    _, matches = redact_text(text, mapper)

    predicted_by_type = {}
    for m in matches:
        predicted_by_type.setdefault(m.label, []).append(normalize(m.text))

    report_lines = []
    report_lines.append(f"{'Type':<14}{'TP':<5}{'FP':<5}{'FN':<5}{'Precision':<11}{'Recall':<9}{'F1':<6}")
    total_tp = total_fp = total_fn = 0

    for pii_type in ["PERSON", "EMAIL", "PHONE", "ORG", "ADDRESS", "SSN", "CREDIT_CARD", "DOB", "IP"]:
        gold = [normalize(x) for x in gt.get(pii_type, [])]
        pred = predicted_by_type.get(pii_type, [])

        matched_gold = set()
        tp = 0
        for p in pred:
            hit = False
            for i, g in enumerate(gold):
                if i in matched_gold:
                    continue
                if g in p or p in g:
                    matched_gold.add(i)
                    hit = True
                    break
            if hit:
                tp += 1
        fp = len(pred) - tp
        fn = len(gold) - len(matched_gold)

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        total_tp += tp
        total_fp += fp
        total_fn += fn

        report_lines.append(
            f"{pii_type:<14}{tp:<5}{fp:<5}{fn:<5}{precision:<11.2f}{recall:<9.2f}{f1:<6.2f}"
        )

    overall_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    overall_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    overall_f1 = 2 * overall_p * overall_r / (overall_p + overall_r) if (overall_p + overall_r) else 0.0

    # "Accuracy" for a span-detection task is instance-level: correctly
    # handled instances (TP + correctly-ignored non-PII controls) over all
    # instances considered (gold PII + control non-PII items).
    control_terms = [normalize(x) for x in gt["NOT_PII_SHOULD_NOT_MATCH"]]
    all_predicted_text = [normalize(m.text) for m in matches]
    control_false_positives = sum(
        1 for c in control_terms if any(c in p or p in c for p in all_predicted_text)
    )
    total_instances = total_tp + total_fn + len(control_terms)
    correct_instances = total_tp + (len(control_terms) - control_false_positives)
    accuracy = correct_instances / total_instances if total_instances else 0.0

    print("\n".join(report_lines))
    print("-" * 60)
    print(f"{'OVERALL':<14}{total_tp:<5}{total_fp:<5}{total_fn:<5}{overall_p:<11.2f}{overall_r:<9.2f}{overall_f1:<6.2f}")
    print(f"\nControl (non-PII) false positives: {control_false_positives}/{len(control_terms)}")
    print(f"Instance-level accuracy (TP + correctly-ignored controls): {accuracy:.2%}")

    with open("evaluation_results.json", "w") as f:
        json.dump({
            "per_type": {
                t: {"tp": None} for t in []  # placeholder, human-readable report is the .md
            },
            "overall_precision": overall_p,
            "overall_recall": overall_r,
            "overall_f1": overall_f1,
            "accuracy": accuracy,
            "control_false_positives": control_false_positives,
            "control_total": len(control_terms),
        }, f, indent=2)


if __name__ == "__main__":
    main()
