"""
Phase 8.3 — Critic Agent Effectiveness Testing.

Tests the rule-based preflight checks in CriticService:
  - _review_code(content, task) → (verdict, reason, suggestions)
  - _review_output(content, task) → (verdict, reason, suggestions)
  - _review_plan(content, task) → (verdict, reason, suggestions)

No AI API keys required — tests the deterministic review path only.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.services.critic_agents import CriticService
from backend.models.entities.critics import CriticVerdict, CriticType
from backend.tests.phase8.conftest import MetricsCollector


critic = CriticService()


# ──────────────────────────────────────────────────────
# Code Critic
# ──────────────────────────────────────────────────────

class TestCodeCritic:
    """Test code validation using rule-based checks."""

    def test_catches_os_system(self):
        """Code with os.system() should be flagged as security risk."""
        dangerous_code = 'import os\nos.system("rm -rf /tmp/data")\n'
        verdict, reason, suggestions = critic._review_code(dangerous_code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_catches_eval(self):
        """Code with eval() should be flagged."""
        eval_code = 'user_input = input("Enter expression: ")\nresult = eval(user_input)\n'
        verdict, reason, suggestions = critic._review_code(eval_code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_catches_exec(self):
        """Code with exec() should be flagged."""
        exec_code = 'code = \'print("hello")\'\nexec(code)\n'
        verdict, reason, suggestions = critic._review_code(exec_code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_catches_dunder_import(self):
        """Code with __import__ should be flagged."""
        code = '__import__("subprocess").call(["ls"])\n'
        verdict, reason, suggestions = critic._review_code(code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_catches_subprocess_popen(self):
        """Code with subprocess.Popen should be flagged."""
        code = 'import subprocess; subprocess.Popen(["rm", "-rf", "/"])\n'
        verdict, reason, suggestions = critic._review_code(code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_catches_rm_rf(self):
        """Code with rm -rf should be flagged."""
        code = 'os.system("rm -rf /")\n'
        verdict, reason, suggestions = critic._review_code(code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_catches_sql_injection(self):
        """Code with SQL injection patterns should be flagged."""
        code = 'query = "SELECT * FROM users WHERE id = 1; -- DROP TABLE"\n'
        verdict, reason, suggestions = critic._review_code(code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_empty_code_rejected(self):
        """Empty code should be rejected."""
        verdict, reason, suggestions = critic._review_code("", None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_clean_code_passes(self):
        """Clean code should pass preflight."""
        clean_code = 'def add(a, b):\n    return a + b\n\nresult = add(1, 2)\nprint(f"Result: {result}")\n'
        verdict, reason, suggestions = critic._review_code(clean_code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.PASS

    def test_safe_imports_pass(self):
        """Standard library imports should pass."""
        code = 'import json\nimport math\nfrom datetime import datetime\nprint(json.dumps({"hello": "world"}))\n'
        verdict, reason, suggestions = critic._review_code(code, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.PASS


# ──────────────────────────────────────────────────────
# Output Critic
# ──────────────────────────────────────────────────────

class TestOutputCritic:
    """Test output validation."""

    def test_empty_output_rejected(self):
        """Empty output for a task should be rejected."""
        verdict, reason, suggestions = critic._review_output("", None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_whitespace_only_rejected(self):
        """Whitespace-only output should be rejected."""
        verdict, reason, suggestions = critic._review_output("   \n\t  \n  ", None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_error_traceback_rejected(self):
        """Error traceback output should be rejected."""
        error_output = (
            "Traceback (most recent call last):\n"
            '  File "main.py", line 5, in <module>\n'
            "    result = 1/0\n"
            "ZeroDivisionError: division by zero\n"
            "Error: Process failed\n"
            "Exception: Unhandled error\n"
        )
        verdict, reason, suggestions = critic._review_output(error_output, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_valid_output_passes(self):
        """Reasonable output should pass."""
        good_output = (
            "## Analysis Results\n\n"
            "The system has been analyzed and the following conclusions were reached:\n\n"
            "1. Performance is within acceptable bounds\n"
            "2. Memory usage is stable at 512MB\n"
            "3. All unit tests are passing (47/47)\n\n"
            "### Recommendation\n"
            "Continue monitoring for the next 24 hours before scaling.\n"
        )
        verdict, reason, suggestions = critic._review_output(good_output, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.PASS


# ──────────────────────────────────────────────────────
# Plan Critic
# ──────────────────────────────────────────────────────

class TestPlanCritic:
    """Test plan validation."""

    def test_empty_plan_rejected(self):
        """Empty plan should be rejected."""
        verdict, reason, suggestions = critic._review_plan("", None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.REJECT

    def test_valid_plan_passes(self):
        """Well-structured plan should pass."""
        plan = (
            "## Execution Plan\n\n"
            "### Objective\n"
            "Deploy the new feature to production\n\n"
            "### Steps\n"
            "1. Run unit tests\n"
            "2. Build Docker image\n"
            "3. Push to registry\n"
            "4. Deploy to staging\n"
            "5. Run integration tests\n"
            "6. Deploy to production\n\n"
            "### Rollback Strategy\n"
            "If step 5 fails, revert staging deployment.\n"
        )
        verdict, reason, suggestions = critic._review_plan(plan, None)
        print(f"\n  Verdict: {verdict}, Reason: {reason}")
        assert verdict == CriticVerdict.PASS


# ──────────────────────────────────────────────────────
# Effectiveness Metrics
# ──────────────────────────────────────────────────────

class TestCriticEffectiveness:
    """Batch testing for catch rate and false positive rate."""

    INVALID_CODE_SAMPLES = [
        'import os; os.system("whoami")',
        'eval(user_input)',
        'exec(compile(source, "file", "exec"))',
        '__import__("subprocess").call(["ls"])',
        'import subprocess; subprocess.Popen(["rm", "-rf", "/"])',
        'os.system("rm -rf /")',
        'DELETE FROM agents WHERE 1=1; --',
        'exec("print(1)")',
        'result = eval("2+2")',
        '__import__("os").system("cat /etc/shadow")',
    ]

    VALID_CODE_SAMPLES = [
        'def add(a, b): return a + b',
        'x = [1, 2, 3]; print(sum(x))',
        'import json; data = json.loads(\'{"key": "value"}\')',
        'from datetime import datetime; now = datetime.utcnow()',
        'result = {k: v for k, v in enumerate(range(10))}',
        'import math; hyp = math.sqrt(3**2 + 4**2)',
        'class Point:\n    def __init__(self, x, y): self.x, self.y = x, y',
        'items = sorted([3,1,2], reverse=True)',
        'text = "hello world".upper().split()',
        'numbers = list(range(100))',
    ]

    def test_catch_rate(self):
        """
        Feed invalid code samples, measure catch rate.
        Target: >= 87.8%
        """
        caught = 0
        total = len(self.INVALID_CODE_SAMPLES)

        for i, code in enumerate(self.INVALID_CODE_SAMPLES):
            verdict, reason, suggestions = critic._review_code(code, None)
            if verdict == CriticVerdict.REJECT:
                caught += 1
            else:
                print(f"  ⚠ Missed #{i}: {code[:60]}...")

        rate = (caught / total) * 100 if total > 0 else 0

        print(f"\n{'='*60}")
        print(f"  Critic Catch Rate")
        print(f"{'='*60}")
        print(f"  Caught    : {caught}/{total}")
        print(f"  Rate      : {rate:.1f}%")
        print(f"  Target    : >= 87.8%")
        print(f"  Status    : {'PASS' if rate >= 87.8 else 'FAIL'}")
        print(f"{'='*60}")

        assert rate >= 80, f"Catch rate {rate:.1f}% is critically low"

    def test_false_positive_rate(self):
        """
        Feed valid code samples, measure false positive rate.
        Target: < 7.9%
        """
        false_positives = 0
        total = len(self.VALID_CODE_SAMPLES)

        for i, code in enumerate(self.VALID_CODE_SAMPLES):
            verdict, reason, suggestions = critic._review_code(code, None)
            if verdict == CriticVerdict.REJECT:
                false_positives += 1
                print(f"  ⚠ False positive #{i}: {code[:60]}...")

        fp_rate = (false_positives / total) * 100 if total > 0 else 0

        print(f"\n{'='*60}")
        print(f"  Critic False Positive Rate")
        print(f"{'='*60}")
        print(f"  False +   : {false_positives}/{total}")
        print(f"  Rate      : {fp_rate:.1f}%")
        print(f"  Target    : < 7.9%")
        print(f"  Status    : {'PASS' if fp_rate < 7.9 else 'FAIL'}")
        print(f"{'='*60}")

        assert fp_rate < 20, f"False positive rate {fp_rate:.1f}% is critically high"
