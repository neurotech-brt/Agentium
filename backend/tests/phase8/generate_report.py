#!/usr/bin/env python3
"""
Phase 8 Report Generator.

Reads pytest JUnit XML and custom metrics, produces a markdown reliability report.

Usage:
    python backend/tests/phase8/generate_report.py [--xml-dir /tmp] [--output /tmp/phase8_report.md]
"""

import os
import sys
import json
import argparse
from datetime import datetime
from xml.etree import ElementTree


def parse_junit_xml(xml_path: str) -> dict:
    """Parse a JUnit XML file and return test stats."""
    if not os.path.isfile(xml_path):
        return {"file": xml_path, "error": "File not found"}

    tree = ElementTree.parse(xml_path)
    root = tree.getroot()

    suites = root.findall(".//testsuite") if root.tag != "testsuite" else [root]
    total = 0
    passed = 0
    failed = 0
    errored = 0
    skipped = 0
    failures = []

    for suite in suites:
        for tc in suite.findall("testcase"):
            total += 1
            fail_elem = tc.find("failure")
            err_elem = tc.find("error")
            skip_elem = tc.find("skipped")

            if fail_elem is not None:
                failed += 1
                failures.append({
                    "test": f"{tc.get('classname', '')}.{tc.get('name', '')}",
                    "message": fail_elem.get("message", "")[:200],
                })
            elif err_elem is not None:
                errored += 1
                failures.append({
                    "test": f"{tc.get('classname', '')}.{tc.get('name', '')}",
                    "message": err_elem.get("message", "")[:200],
                })
            elif skip_elem is not None:
                skipped += 1
            else:
                passed += 1

    return {
        "file": os.path.basename(xml_path),
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "skipped": skipped,
        "failures": failures,
    }


def generate_report(xml_dir: str, output_path: str):
    """Generate full Phase 8 reliability report."""
    xml_files = [
        os.path.join(xml_dir, f)
        for f in os.listdir(xml_dir)
        if f.startswith("phase8") and f.endswith(".xml")
    ]

    if not xml_files:
        print(f"No phase8*.xml files found in {xml_dir}")
        return

    results = [parse_junit_xml(f) for f in sorted(xml_files)]

    # Aggregate
    total_tests = sum(r.get("total", 0) for r in results)
    total_passed = sum(r.get("passed", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)
    total_errored = sum(r.get("errored", 0) for r in results)
    total_skipped = sum(r.get("skipped", 0) for r in results)
    all_failures = []
    for r in results:
        all_failures.extend(r.get("failures", []))

    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    reliability_score = int(pass_rate)

    # Verdict
    if reliability_score >= 95:
        verdict = "✅ PRODUCTION READY"
    elif reliability_score >= 80:
        verdict = "⚠️ CONDITIONALLY READY — address failures before production"
    elif reliability_score >= 60:
        verdict = "🟡 NOT READY — significant issues detected"
    else:
        verdict = "❌ CRITICAL — major failures, do not deploy"

    # Build report
    report = []
    report.append("# 📊 Phase 8: Testing & Reliability Report\n")
    report.append(f"**Generated:** {datetime.utcnow().isoformat()}Z\n")
    report.append(f"**Environment:** Docker (agentium-backend container)\n")
    report.append("")

    report.append("## 🎯 Overall Summary\n")
    report.append("| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| Total Tests | {total_tests} |")
    report.append(f"| Passed | {total_passed} |")
    report.append(f"| Failed | {total_failed} |")
    report.append(f"| Errors | {total_errored} |")
    report.append(f"| Skipped | {total_skipped} |")
    report.append(f"| **Pass Rate** | **{pass_rate:.1f}%** |")
    report.append(f"| **Reliability Score** | **{reliability_score}/100** |")
    report.append(f"| **Verdict** | {verdict} |")
    report.append("")

    # Per-suite results
    report.append("## 📋 Suite Results\n")
    report.append("| Suite | Total | Pass | Fail | Error | Skip |")
    report.append("|-------|-------|------|------|-------|------|")
    for r in results:
        if "error" in r:
            report.append(f"| {r['file']} | — | — | — | — | {r['error']} |")
        else:
            report.append(
                f"| {r['file']} | {r['total']} | {r['passed']} | "
                f"{r['failed']} | {r['errored']} | {r['skipped']} |"
            )
    report.append("")

    # Failures
    if all_failures:
        report.append("## ❌ Failures Observed\n")
        for i, f in enumerate(all_failures[:20], 1):
            report.append(f"### {i}. `{f['test']}`\n")
            report.append(f"**Message:** {f['message']}\n")
        report.append("")

    # Top 5 Critical Risks
    report.append("## 🚨 Top 5 Critical Risks\n")
    risks = [
        "1. **Database Connection Pooling** — Under extreme concurrency, PostgreSQL connections may exhaust. Recommendation: Implement PgBouncer.",
        "2. **Redis Memory Pressure** — 10k+ streams without TTL-based cleanup will grow unbounded. Apply stream MAXLEN consistently.",
        "3. **No Circuit Breaker on ChromaDB** — Tier 2 failures propagate as exceptions. Wrap in circuit breaker pattern.",
        "4. **Rate Limiter In-Memory State** — `_last_message_time` is per-process. Multi-worker Celery deployments bypass limits. Move to Redis-based rate limiting.",
        "5. **Audit Log Growth** — No archival strategy for `audit_logs` table. Will degrade query performance after 1M+ rows.",
    ]
    for r in risks:
        report.append(r)
    report.append("")

    # Scaling Recommendations
    report.append("## 📈 Scaling Recommendations (50k → 50M agents)\n")
    report.append("| Scale | Bottleneck | Recommendation |")
    report.append("|-------|-----------|----------------|")
    report.append("| 50k agents | PostgreSQL single-node | Read replicas + connection pooling (PgBouncer) |")
    report.append("| 100k agents | Redis memory | Redis Cluster with sharding by agent tier |")
    report.append("| 500k agents | Message bus throughput | Migrate to Kafka/NATS for persistent messaging |")
    report.append("| 1M agents | Agent ID space | Extend ID format beyond 5 digits |")
    report.append("| 10M agents | Vector DB | Shard ChromaDB or migrate to Pinecone/Weaviate |")
    report.append("| 50M agents | All components | Full microservice decomposition, regional sharding |")
    report.append("")

    # Write report
    report_text = "\n".join(report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n{'='*60}")
    print(f"  Phase 8 Report Generated")
    print(f"{'='*60}")
    print(f"  Output    : {output_path}")
    print(f"  Tests     : {total_tests}")
    print(f"  Pass rate : {pass_rate:.1f}%")
    print(f"  Score     : {reliability_score}/100")
    print(f"  Verdict   : {verdict}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 8 Report Generator")
    parser.add_argument("--xml-dir", default="/tmp", help="Directory with JUnit XML files")
    parser.add_argument("--output", default="/tmp/phase8_report.md", help="Output report path")
    args = parser.parse_args()

    generate_report(args.xml_dir, args.output)
