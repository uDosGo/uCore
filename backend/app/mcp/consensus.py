"""Hivemind Consensus Engine — Multi-agent voting and resolution.

Supports four voting modes:
  - majority: Simple majority wins
  - unanimous: All agents must agree
  - weighted: Weighted score threshold
  - escalation: Escalate to human on deadlock
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

log = logging.getLogger("ucore.mcp.hivemind.consensus")


class Vote(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class ConsensusMode(Enum):
    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"
    ESCALATION = "escalation"


@dataclass
class AgentVote:
    agent_id: str
    vote: Vote
    reasoning: str = ""
    weight: float = 1.0


@dataclass
class Proposal:
    id: str
    agent_id: str
    title: str
    description: str
    actions: list[dict[str, Any]] = field(default_factory=list)
    votes: list[AgentVote] = field(default_factory=list)
    round: int = 1
    max_rounds: int = 3
    resolved: bool = False
    outcome: str | None = None


class ConsensusEngine:
    """Multi-agent consensus engine with configurable voting modes."""

    def __init__(self, mode: ConsensusMode = ConsensusMode.MAJORITY):
        self.mode = mode
        self.proposals: dict[str, Proposal] = {}
        self._round_counters: dict[str, int] = {}

    def create_proposal(
        self,
        agent_id: str,
        title: str,
        description: str,
        actions: list[dict[str, Any]] | None = None,
    ) -> Proposal:
        """Create a new proposal for agents to vote on."""
        proposal_id = f"prop_{len(self.proposals) + 1}"
        proposal = Proposal(
            id=proposal_id,
            agent_id=agent_id,
            title=title,
            description=description,
            actions=actions or [],
        )
        self.proposals[proposal_id] = proposal
        self._round_counters[proposal_id] = 1
        log.info("Proposal created: %s by %s — %s", proposal_id, agent_id, title)
        return proposal

    def cast_vote(
        self,
        proposal_id: str,
        agent_id: str,
        vote: Vote,
        reasoning: str = "",
        weight: float = 1.0,
    ) -> dict[str, Any]:
        """Cast a vote on a proposal and check for resolution."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"error": f"Proposal '{proposal_id}' not found"}

        if proposal.resolved:
            return {"error": "Proposal already resolved", "outcome": proposal.outcome}

        agent_vote = AgentVote(
            agent_id=agent_id,
            vote=vote,
            reasoning=reasoning,
            weight=weight,
        )
        proposal.votes.append(agent_vote)
        log.info("Vote cast: %s voted %s on %s", agent_id, vote.value, proposal_id)

        return self._check_resolution(proposal)

    def _check_resolution(self, proposal: Proposal) -> dict[str, Any]:
        """Check if the proposal can be resolved based on current votes."""
        if not proposal.votes:
            return {"status": "pending", "round": proposal.round}

        if self.mode == ConsensusMode.MAJORITY:
            return self._resolve_majority(proposal)
        elif self.mode == ConsensusMode.UNANIMOUS:
            return self._resolve_unanimous(proposal)
        elif self.mode == ConsensusMode.WEIGHTED:
            return self._resolve_weighted(proposal)
        elif self.mode == ConsensusMode.ESCALATION:
            return self._resolve_escalation(proposal)
        else:
            return self._resolve_majority(proposal)

    def _resolve_majority(self, proposal: Proposal) -> dict[str, Any]:
        """Simple majority: >50% of non-abstain votes wins."""
        approves = sum(1 for v in proposal.votes if v.vote == Vote.APPROVE)
        rejects = sum(1 for v in proposal.votes if v.vote == Vote.REJECT)
        total = approves + rejects

        if total == 0:
            return {"status": "pending", "round": proposal.round}

        if approves > rejects:
            return self._resolve(proposal, "approved")
        elif rejects > approves:
            return self._resolve(proposal, "rejected")
        else:
            return self._handle_tie(proposal)

    def _resolve_unanimous(self, proposal: Proposal) -> dict[str, Any]:
        """Unanimous: all non-abstain votes must approve."""
        rejects = [v for v in proposal.votes if v.vote == Vote.REJECT]
        if rejects:
            return self._resolve(proposal, "rejected")
        approves = [v for v in proposal.votes if v.vote == Vote.APPROVE]
        if approves:
            return self._resolve(proposal, "approved")
        return {"status": "pending", "round": proposal.round}

    def _resolve_weighted(self, proposal: Proposal) -> dict[str, Any]:
        """Weighted: score threshold (sum of weights * vote)."""
        threshold = 0.5  # 50% threshold
        total_weight = sum(v.weight for v in proposal.votes if v.vote != Vote.ABSTAIN)
        approve_weight = sum(
            v.weight for v in proposal.votes if v.vote == Vote.APPROVE
        )

        if total_weight == 0:
            return {"status": "pending", "round": proposal.round}

        score = approve_weight / total_weight
        if score > threshold:
            return self._resolve(proposal, "approved")
        elif score < threshold:
            return self._resolve(proposal, "rejected")
        else:
            return self._handle_tie(proposal)

    def _resolve_escalation(self, proposal: Proposal) -> dict[str, Any]:
        """Escalation: escalate to human on deadlock or after max rounds."""
        if proposal.round >= proposal.max_rounds:
            return self._resolve(
                proposal, "escalated",
                detail="Max rounds reached, escalated to human",
            )
        return self._resolve_majority(proposal)

    def _handle_tie(self, proposal: Proposal) -> dict[str, Any]:
        """Handle a tie by incrementing round or escalating."""
        if proposal.round >= proposal.max_rounds:
            return self._resolve(
                proposal, "escalated",
                detail="Tie after max rounds, escalated to human",
            )
        proposal.round += 1
        log.info("Tie on %s — advancing to round %d", proposal.id, proposal.round)
        return {
            "status": "tie",
            "round": proposal.round,
            "message": f"Tie broken — advancing to round {proposal.round}",
        }

    def _resolve(
        self,
        proposal: Proposal,
        outcome: str,
        detail: str | None = None,
    ) -> dict[str, Any]:
        """Mark a proposal as resolved."""
        proposal.resolved = True
        proposal.outcome = outcome
        log.info("Proposal %s resolved: %s", proposal.id, outcome)
        result = {
            "status": "resolved",
            "outcome": outcome,
            "round": proposal.round,
            "votes": [
                {"agent_id": v.agent_id, "vote": v.vote.value, "reasoning": v.reasoning}
                for v in proposal.votes
            ],
        }
        if detail:
            result["detail"] = detail
        return result

    def get_status(self, proposal_id: str) -> dict[str, Any] | None:
        """Get the current status of a proposal."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return None
        return {
            "id": proposal.id,
            "agent_id": proposal.agent_id,
            "title": proposal.title,
            "round": proposal.round,
            "resolved": proposal.resolved,
            "outcome": proposal.outcome,
            "vote_count": len(proposal.votes),
            "votes": [
                {"agent_id": v.agent_id, "vote": v.vote.value}
                for v in proposal.votes
            ],
        }

    def list_active(self) -> list[dict[str, Any]]:
        """List all unresolved proposals."""
        result: list[dict[str, Any]] = []
        for pid, p in self.proposals.items():
            if not p.resolved:
                status = self.get_status(pid)
                if status:
                    result.append(status)
        return result

