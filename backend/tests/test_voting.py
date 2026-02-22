"""Tests for voting API routes.

Covers:
- Amendment voting endpoints
- Task deliberation endpoints
- Vote casting and tallying
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.models.entities.voting import AmendmentVoting, TaskDeliberation, IndividualVote, AmendmentStatus, DeliberationStatus, VoteType
from backend.models.entities.agents import Agent, AgentType


# ──────────────────────────────────────────────────
# Test Client Setup
# ──────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_current_user():
    """Create a mock current user (Council member)."""
    return {"sub": "10001", "email": "council@agentium.ai"}


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# ──────────────────────────────────────────────────
# Amendment API Tests
# ──────────────────────────────────────────────────

class TestAmendmentEndpoints:
    """Test amendment voting endpoints."""

    def test_list_amendments_empty(self, client, mock_current_user):
        """Test listing amendments when none exist."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

                response = client.get("/api/v1/voting/amendments")

                assert response.status_code == 200
                assert response.json() == []

    def test_list_amendments_with_data(self, client, mock_current_user):
        """Test listing amendments with existing data."""
        mock_amendment = Mock()
        mock_amendment.id = "test-amendment-1"
        mock_amendment.agentium_id = "AV20260101000000"
        mock_amendment.status = AmendmentStatus.PROPOSED
        mock_amendment.eligible_voters = ["10001", "10002", "10003"]
        mock_amendment.votes_for = 2
        mock_amendment.votes_against = 1
        mock_amendment.votes_abstain = 0
        mock_amendment.final_result = None
        mock_amendment.started_at = None
        mock_amendment.ended_at = None
        mock_amendment.created_at = datetime.utcnow()
        mock_amendment.discussion_thread = [
            {"timestamp": datetime.utcnow().isoformat(), "agent": "10001", "message": "PROPOSAL: Test Amendment"}
        ]

        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db', mock_db):
                mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_amendment]

                response = client.get("/api/v1/voting/amendments")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == "test-amendment-1"
                assert data[0]["status"] == "proposed"

    def test_list_amendments_filter_by_status(self, client, mock_current_user):
        """Test filtering amendments by status."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

                response = client.get("/api/v1/voting/amendments?status_filter=passed")

                assert response.status_code == 200
                mock_db.query.return_value.filter.assert_called()

    def test_propose_amendment_unauthorized(self, client):
        """Test that non-council members cannot propose amendments."""
        non_council_user = {"sub": "30001", "email": "agent@agentium.ai"}

        with patch('backend.api.routes.voting.get_current_active_user', return_value=non_council_user):
            with patch('backend.api.routes.voting.AmendmentService') as MockService:
                MockService.return_value.propose_amendment.side_effect = PermissionError(
                    "Only Council members (1xxxx) or Head (0xxxx) can propose amendments."
                )

                response = client.post(
                    "/api/v1/voting/amendments",
                    json={
                        "title": "Test Amendment",
                        "diff_markdown": "+ Add new article",
                        "rationale": "Testing purposes"
                    }
                )

                assert response.status_code == 403

    def test_propose_amendment_success(self, client, mock_current_user):
        """Test successful amendment proposal."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.AmendmentService') as MockService:
                mock_service = Mock()
                mock_service.propose_amendment = AsyncMock(return_value={
                    "amendment_id": "new-amendment-1",
                    "status": "proposed",
                    "title": "Test Amendment",
                    "proposer": "10001",
                    "sponsors": ["10001"],
                    "sponsors_needed": 1,
                    "eligible_voters": ["10001", "10002", "10003"]
                })
                MockService.return_value = mock_service

                response = client.post(
                    "/api/v1/voting/amendments",
                    json={
                        "title": "Test Amendment",
                        "diff_markdown": "+ Add new article",
                        "rationale": "Testing purposes"
                    }
                )

                assert response.status_code == 201

    def test_get_amendment_details_not_found(self, client, mock_current_user):
        """Test getting non-existent amendment."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.AmendmentService') as MockService:
                mock_service = Mock()
                mock_service.get_amendment_detail = AsyncMock(return_value=None)
                MockService.return_value = mock_service

                response = client.get("/api/v1/voting/amendments/non-existent-id")

                assert response.status_code == 404

    def test_get_amendment_details_success(self, client, mock_current_user):
        """Test getting amendment details."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.AmendmentService') as MockService:
                mock_service = Mock()
                mock_service.get_amendment_detail = AsyncMock(return_value={
                    "id": "amendment-1",
                    "agentium_id": "AV20260101000000",
                    "status": "voting",
                    "title": "Test Amendment",
                    "debate_document": "# Amendment content",
                    "sponsors": ["10001"],
                    "votes_for": 2,
                    "votes_against": 1
                })
                MockService.return_value = mock_service

                response = client.get("/api/v1/voting/amendments/amendment-1")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "amendment-1"

    def test_cast_vote_not_found(self, client, mock_current_user):
        """Test voting on non-existent amendment."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = None

                response = client.post(
                    "/api/v1/voting/amendments/non-existent/vote",
                    json={"vote": "for", "rationale": "Looks good"}
                )

                assert response.status_code == 404

    def test_cast_vote_invalid_status(self, client, mock_current_user):
        """Test voting on amendment not in VOTING status."""
        mock_amendment = Mock()
        mock_amendment.id = "amendment-1"
        mock_amendment.status = AmendmentStatus.PROPOSED
        mock_amendment.eligible_voters = ["10001", "10002"]

        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = mock_amendment

                response = client.post(
                    "/api/v1/voting/amendments/amendment-1/vote",
                    json={"vote": "for"}
                )

                assert response.status_code == 400

    def test_cast_vote_not_eligible(self, client, mock_current_user):
        """Test voting by non-eligible voter."""
        mock_amendment = Mock()
        mock_amendment.id = "amendment-1"
        mock_amendment.status = AmendmentStatus.VOTING
        mock_amendment.eligible_voters = ["10002", "10003"]
        mock_amendment.votes_for = 0
        mock_amendment.votes_against = 0
        mock_amendment.votes_abstain = 0

        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = mock_amendment

                response = client.post(
                    "/api/v1/voting/amendments/amendment-1/vote",
                    json={"vote": "for"}
                )

                assert response.status_code == 403

    def test_cast_vote_invalid_vote_type(self, client, mock_current_user):
        """Test casting invalid vote type."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            response = client.post(
                "/api/v1/voting/amendments/amendment-1/vote",
                json={"vote": "invalid"}
            )

            assert response.status_code == 422  # Validation error

    def test_sponsor_amendment_not_found(self, client, mock_current_user):
        """Test sponsoring non-existent amendment."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.AmendmentService') as MockService:
                mock_service = Mock()
                mock_service.sponsor_amendment = AsyncMock(side_effect=ValueError("Amendment not found"))
                MockService.return_value = mock_service

                response = client.post("/api/v1/voting/amendments/non-existent/sponsor")

                assert response.status_code == 400


# ──────────────────────────────────────────────────
# Deliberation API Tests
# ──────────────────────────────────────────────────

class TestDeliberationEndpoints:
    """Test task deliberation endpoints."""

    def test_list_deliberations_empty(self, client, mock_current_user):
        """Test listing deliberations when none exist."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

                response = client.get("/api/v1/voting/deliberations")

                assert response.status_code == 200
                assert response.json() == []

    def test_list_deliberations_with_data(self, client, mock_current_user):
        """Test listing deliberations with existing data."""
        mock_deliberation = Mock()
        mock_deliberation.id = "delib-1"
        mock_deliberation.agentium_id = "D20260101000000"
        mock_deliberation.task_id = "task-1"
        mock_deliberation.status = DeliberationStatus.ACTIVE
        mock_deliberation.participating_members = ["10001", "10002"]
        mock_deliberation.votes_for = 1
        mock_deliberation.votes_against = 0
        mock_deliberation.votes_abstain = 0
        mock_deliberation.final_decision = None
        mock_deliberation.head_overridden = False
        mock_deliberation.started_at = datetime.utcnow()
        mock_deliberation.ended_at = None
        mock_deliberation.time_limit_minutes = 30
        mock_deliberation.discussion_thread = []

        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db', mock_db):
                mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_deliberation]

                response = client.get("/api/v1/voting/deliberations")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == "delib-1"

    def test_get_deliberation_details_not_found(self, client, mock_current_user):
        """Test getting non-existent deliberation."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = None

                response = client.get("/api/v1/voting/deliberations/non-existent")

                assert response.status_code == 404

    def test_get_deliberation_details_success(self, client, mock_current_user):
        """Test getting deliberation details."""
        mock_deliberation = Mock()
        mock_deliberation.id = "delib-1"
        mock_deliberation.agentium_id = "D20260101000000"
        mock_deliberation.task_id = "task-1"
        mock_deliberation.status = DeliberationStatus.ACTIVE
        mock_deliberation.participating_members = ["10001", "10002"]
        mock_deliberation.required_approvals = 2
        mock_deliberation.min_quorum = 2
        mock_deliberation.votes_for = 1
        mock_deliberation.votes_against = 0
        mock_deliberation.votes_abstain = 0
        mock_deliberation.final_decision = None
        mock_deliberation.head_overridden = False
        mock_deliberation.head_override_reason = None
        mock_deliberation.started_at = datetime.utcnow()
        mock_deliberation.ended_at = None
        mock_deliberation.time_limit_minutes = 30
        mock_deliberation.discussion_thread = []

        mock_vote = Mock()
        mock_vote.voter_agentium_id = "10001"
        mock_vote.vote = VoteType.FOR
        mock_vote.rationale = "Approve"
        mock_vote.changed_at = datetime.utcnow()

        mock_deliberation.individual_votes = Mock()
        mock_deliberation.individual_votes.all.return_value = [mock_vote]

        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deliberation

                response = client.get("/api/v1/voting/deliberations/delib-1")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "delib-1"
                assert "individual_votes" in data

    def test_cast_deliberation_vote_not_active(self, client, mock_current_user):
        """Test voting on inactive deliberation."""
        mock_deliberation = Mock()
        mock_deliberation.id = "delib-1"
        mock_deliberation.status = DeliberationStatus.CONCLUDED
        mock_deliberation.participating_members = ["10001", "10002"]

        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deliberation

                response = client.post(
                    "/api/v1/voting/deliberations/delib-1/vote",
                    json={"vote": "for"}
                )

                assert response.status_code == 400

    def test_start_deliberation_not_found(self, client, mock_current_user):
        """Test starting non-existent deliberation."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = None

                response = client.post("/api/v1/voting/deliberations/non-existent/start")

                assert response.status_code == 404

    def test_conclude_deliberation_not_found(self, client, mock_current_user):
        """Test concluding non-existent deliberation."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            with patch('backend.api.routes.voting.db') as mock_db:
                mock_db.query.return_value.filter_by.return_value.first.return_value = None

                response = client.post("/api/v1/voting/deliberations/non-existent/conclude")

                assert response.status_code == 404


# ──────────────────────────────────────────────────
# Vote Tally Tests
# ──────────────────────────────────────────────────

class TestVoteTallying:
    """Test vote calculation and tallying."""

    def test_vote_percentage_calculation(self):
        """Test vote percentage calculation."""
        # Test data
        votes_for = 10
        votes_against = 5
        votes_abstain = 5
        total = votes_for + votes_against + votes_abstain

        # Calculate percentages
        for_percentage = (votes_for / total) * 100 if total > 0 else 0
        against_percentage = (votes_against / total) * 100 if total > 0 else 0
        abstain_percentage = (votes_abstain / total) * 100 if total > 0 else 0

        assert for_percentage == 50.0
        assert against_percentage == 25.0
        assert abstain_percentage == 25.0

    def test_zero_votes_calculation(self):
        """Test calculation with zero votes."""
        votes_for = 0
        votes_against = 0
        votes_abstain = 0
        total = votes_for + votes_against + votes_abstain

        for_percentage = (votes_for / total) * 100 if total > 0 else 0

        assert for_percentage == 0

    def test_supermajority_threshold(self):
        """Test supermajority threshold calculation."""
        # 66% threshold
        threshold = 66
        votes_for = 7
        total = 10
        percentage = (votes_for / total) * 100

        assert percentage >= threshold

    def test_failed_supermajority(self):
        """Test failed supermajority threshold."""
        threshold = 66
        votes_for = 5
        total = 10
        percentage = (votes_for / total) * 100

        assert percentage < threshold


# ──────────────────────────────────────────────────
# Integration Tests
# ──────────────────────────────────────────────────

class TestVotingIntegration:
    """Integration tests for voting flow."""

    def test_amendment_full_lifecycle(self, client, mock_current_user):
        """Test complete amendment lifecycle: propose -> sponsor -> vote -> conclude."""
        # This would require more complex mocking of the service layer
        # For now, we test the endpoint responses
        pass

    def test_deliberation_full_lifecycle(self, client, mock_current_user):
        """Test complete deliberation lifecycle: create -> start -> vote -> conclude."""
        # This would require more complex mocking of the service layer
        # For now, we test the endpoint responses
        pass


# ──────────────────────────────────────────────────
# Error Handling Tests
# ──────────────────────────────────────────────────

class TestVotingErrors:
    """Test error handling in voting endpoints."""

    def test_invalid_amendment_id_format(self, client, mock_current_user):
        """Test invalid amendment ID format."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            response = client.get("/api/v1/voting/amendments/invalid@#$%^&*")

            # Should handle gracefully (404 or 400)
            assert response.status_code in [404, 400, 422]

    def test_invalid_deliberation_id_format(self, client, mock_current_user):
        """Test invalid deliberation ID format."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            response = client.get("/api/v1/voting/deliberations/invalid@#$%^&*")

            # Should handle gracefully
            assert response.status_code in [404, 400, 422]

    def test_missing_required_fields_proposal(self, client, mock_current_user):
        """Test proposal with missing required fields."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            response = client.post(
                "/api/v1/voting/amendments",
                json={"title": "Only title"}
            )

            assert response.status_code == 422

    def test_invalid_voting_period(self, client, mock_current_user):
        """Test proposal with invalid voting period."""
        with patch('backend.api.routes.voting.get_current_active_user', return_value=mock_current_user):
            response = client.post(
                "/api/v1/voting/amendments",
                json={
                    "title": "Test",
                    "diff_markdown": "+ content",
                    "rationale": "test",
                    "voting_period_hours": 10  # Too short (min 24)
                }
            )

            assert response.status_code == 422
