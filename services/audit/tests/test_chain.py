"""Tests for audit chain module."""

import pytest
from services.audit.src.audit.chain import AuditChain


class TestAuditChain:
    def test_log_event_creates_entry(self):
        chain = AuditChain()
        entry = chain.log_event("session-1", "attack_fired", {"target": "model-x"})
        assert entry.session_id == "session-1"
        assert entry.event_type == "attack_fired"
        assert entry.hash != ""

    def test_hash_chain_integrity(self):
        chain = AuditChain()
        chain.log_event("session-1", "event1", {"data": "a"})
        chain.log_event("session-1", "event2", {"data": "b"})
        chain.log_event("session-1", "event3", {"data": "c"})

        # Verify chain
        assert chain.verify_chain("session-1") is True

    def test_chain_tampering_detected(self):
        chain = AuditChain()
        chain.log_event("session-1", "event1", {"data": "a"})
        # Tamper with entry
        chain._entries[0].data = {"data": "modified"}
        assert chain.verify_chain("session-1") is False

    def test_merkle_root_computation(self):
        chain = AuditChain()
        chain.log_event("session-1", "event1", {"data": "a"})
        chain.log_event("session-1", "event2", {"data": "b"})
        chain.log_event("session-1", "event3", {"data": "c"})

        root = chain.get_merkle_root("session-1")
        assert root != ""
        assert len(root) == 64  # SHA-256 hex length

    def test_different_sessions_have_separate_chains(self):
        chain = AuditChain()
        chain.log_event("session-1", "event1", {"data": "a"})
        chain.log_event("session-2", "event1", {"data": "b"})

        assert chain.verify_chain("session-1") is True
        assert chain.verify_chain("session-2") is True

        root1 = chain.get_merkle_root("session-1")
        root2 = chain.get_merkle_root("session-2")
        assert root1 != root2
