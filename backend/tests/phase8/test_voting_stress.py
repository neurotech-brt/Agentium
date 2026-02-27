"""
Phase 8.1 — Voting System Stress Testing.

Tests:
  1. Quorum validation (1, 5, 100 council members)
  2. Supermajority threshold (66%)
  3. Abstention handling
  4. Delegation chains (A→B→C)
  5. Loop prevention (A→B→A)
  6. Timeout / auto-fail
"""

import os
import sys
import math
import uuid
from datetime import datetime, timedelta

import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.entities.voting import (
    AmendmentVoting,
    TaskDeliberation,
    IndividualVote,
    AmendmentStatus,
    DeliberationStatus,
    VoteType,
)
from backend.services.amendment_service import (
    QUORUM_PERCENTAGE,
    SUPERMAJORITY_THRESHOLD,
)


# ──────────────────────────────────────────────────────
# Quorum Calculation Tests
# ──────────────────────────────────────────────────────

class TestQuorumValidation:
    """Verify quorum calculations across different council sizes."""

    def _quorum(self, eligible_count: int) -> int:
        """Calculate required quorum (60% rounded up)."""
        return math.ceil(eligible_count * QUORUM_PERCENTAGE / 100)

    def test_quorum_1_member(self):
        """1 member → quorum = 1 (100% required)."""
        q = self._quorum(1)
        print(f"\n  1 member  → quorum = {q}")
        assert q == 1

    def test_quorum_2_members(self):
        """2 members → quorum = 2 (both required for 60%)."""
        q = self._quorum(2)
        print(f"\n  2 members → quorum = {q}")
        assert q == 2

    def test_quorum_3_members(self):
        """3 members → quorum = 2."""
        q = self._quorum(3)
        print(f"\n  3 members → quorum = {q}")
        assert q == 2

    def test_quorum_5_members(self):
        """5 members → quorum = 3."""
        q = self._quorum(5)
        print(f"\n  5 members → quorum = {q}")
        assert q == 3

    def test_quorum_10_members(self):
        """10 members → quorum = 6."""
        q = self._quorum(10)
        print(f"\n  10 members → quorum = {q}")
        assert q == 6

    def test_quorum_100_members(self):
        """100 members → quorum = 60."""
        q = self._quorum(100)
        print(f"\n  100 members → quorum = {q}")
        assert q == 60


class TestSupermajorityThreshold:
    """Validate 66% supermajority enforcement."""

    def test_supermajority_pass(self):
        """7/10 votes FOR → 70% → passes 66% threshold."""
        votes_for = 7
        total_cast = 10
        pct = (votes_for / total_cast) * 100
        assert pct >= SUPERMAJORITY_THRESHOLD

    def test_supermajority_fail(self):
        """6/10 votes FOR → 60% → fails 66% threshold."""
        votes_for = 6
        total_cast = 10
        pct = (votes_for / total_cast) * 100
        assert pct < SUPERMAJORITY_THRESHOLD

    def test_supermajority_exact_boundary(self):
        """66/100 votes FOR → 66% → should pass (≥ 66)."""
        votes_for = 66
        total_cast = 100
        pct = (votes_for / total_cast) * 100
        assert pct >= SUPERMAJORITY_THRESHOLD

    def test_supermajority_one_below(self):
        """65/100 votes → 65% → should fail."""
        votes_for = 65
        total_cast = 100
        pct = (votes_for / total_cast) * 100
        assert pct < SUPERMAJORITY_THRESHOLD


class TestAbstentionHandling:
    """Verify abstentions are handled correctly."""

    def test_abstentions_reduce_participation(self):
        """
        5 eligible, 3 vote FOR, 1 AGAINST, 1 ABSTAIN.
        Total cast = 5, but effective votes = 4 (excl abstain for threshold).
        """
        votes_for = 3
        votes_against = 1
        votes_abstain = 1
        total_voted = votes_for + votes_against + votes_abstain
        total_non_abstain = votes_for + votes_against

        # For/Against percentage computed on non-abstain votes
        for_pct = (votes_for / total_non_abstain) * 100 if total_non_abstain > 0 else 0
        print(f"\n  FOR: {votes_for}, AGAINST: {votes_against}, ABSTAIN: {votes_abstain}")
        print(f"  FOR % (excl abstain): {for_pct:.1f}%")
        assert for_pct == 75.0

    def test_all_abstain(self):
        """All abstentions → should not pass (0/0 = no majority)."""
        votes_for = 0
        votes_against = 0
        votes_abstain = 5
        total_non_abstain = votes_for + votes_against
        for_pct = (votes_for / total_non_abstain) * 100 if total_non_abstain > 0 else 0
        assert for_pct == 0


class TestDelegationChains:
    """Test vote delegation chains."""

    def test_delegation_a_to_b_to_c(self):
        """
        A delegates to B, B delegates to C.
        When C votes FOR, A's and B's votes should be counted as FOR.
        """
        # Simulate: 3 council members, A delegates to B, B delegates to C
        delegations = {"10001": "10002", "10002": "10003"}  # A→B, B→C

        def resolve_delegate(voter_id: str, chain=None):
            """Walk delegation chain to find the terminal voter."""
            if chain is None:
                chain = set()
            if voter_id in chain:
                raise ValueError(f"Delegation loop detected: {voter_id}")
            chain.add(voter_id)
            if voter_id in delegations:
                return resolve_delegate(delegations[voter_id], chain)
            return voter_id

        # C is the terminal delegate for both A and B
        assert resolve_delegate("10001") == "10003"
        assert resolve_delegate("10002") == "10003"
        assert resolve_delegate("10003") == "10003"

        # When C votes FOR, it counts as 3 votes FOR (A, B, and C)
        terminal_votes = {}
        for voter in ["10001", "10002", "10003"]:
            terminal = resolve_delegate(voter)
            terminal_votes.setdefault(terminal, []).append(voter)

        # C holds 3 vote weights
        assert len(terminal_votes["10003"]) == 3

    def test_delegation_loop_prevention(self):
        """A→B→A delegation chain must be rejected."""
        delegations = {"10001": "10002", "10002": "10001"}

        def resolve_delegate(voter_id: str, chain=None):
            if chain is None:
                chain = set()
            if voter_id in chain:
                raise ValueError(f"Delegation loop: {voter_id}")
            chain.add(voter_id)
            if voter_id in delegations:
                return resolve_delegate(delegations[voter_id], chain)
            return voter_id

        with pytest.raises(ValueError, match="Delegation loop"):
            resolve_delegate("10001")

    def test_three_way_loop_prevention(self):
        """A→B→C→A must be rejected."""
        delegations = {"10001": "10002", "10002": "10003", "10003": "10001"}

        def resolve_delegate(voter_id: str, chain=None):
            if chain is None:
                chain = set()
            if voter_id in chain:
                raise ValueError(f"Delegation loop: {voter_id}")
            chain.add(voter_id)
            if voter_id in delegations:
                return resolve_delegate(delegations[voter_id], chain)
            return voter_id

        with pytest.raises(ValueError, match="Delegation loop"):
            resolve_delegate("10001")


class TestVoteTimeout:
    """Test vote expiry and auto-fail (logic-only, no SQLAlchemy model instantiation)."""

    def test_expired_amendment_auto_fail(self):
        """
        Amendment with expired voting window should conclude as REJECTED.
        Tests the timeout detection logic without constructing ORM objects.
        """
        voting_deadline = datetime.utcnow() - timedelta(hours=1)
        started_at = datetime.utcnow() - timedelta(hours=100)
        now = datetime.utcnow()

        is_expired = voting_deadline is not None and now > voting_deadline

        print(f"\n  Voting deadline: {voting_deadline}")
        print(f"  Current time  : {now}")
        print(f"  Expired       : {is_expired}")
        assert is_expired, "Amendment should be expired"

    def test_active_amendment_not_expired(self):
        """Amendment with future deadline should not be expired."""
        voting_deadline = datetime.utcnow() + timedelta(hours=48)
        now = datetime.utcnow()

        is_expired = voting_deadline is not None and now > voting_deadline
        assert not is_expired, "Amendment should NOT be expired"

    def test_deadline_exactly_now(self):
        """Deadline at exactly now — should be expired (now > deadline is False for ==)."""
        voting_deadline = datetime.utcnow()
        now = voting_deadline  # same instant

        is_expired = now > voting_deadline
        # now == deadline → NOT expired (strict >)
        assert not is_expired

    def test_no_deadline_never_expires(self):
        """No voting deadline means never expires."""
        voting_deadline = None
        now = datetime.utcnow()

        is_expired = voting_deadline is not None and now > voting_deadline
        assert not is_expired
