"""Tests for SHA-256 Merkle hash chain."""

from __future__ import annotations

import pytest

from audit.chain import GENESIS_HASH, MerkleChain, compute_entry_hash


def test_genesis_hash_length() -> None:
    assert len(GENESIS_HASH) == 64
    assert GENESIS_HASH == "0" * 64


def test_compute_entry_hash_deterministic() -> None:
    h1 = compute_entry_hash(
        "2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc123", GENESIS_HASH, "corr-001"
    )
    h2 = compute_entry_hash(
        "2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc123", GENESIS_HASH, "corr-001"
    )
    assert h1 == h2
    assert len(h1) == 64


def test_compute_entry_hash_single_byte_change() -> None:
    base = compute_entry_hash(
        "2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc123", GENESIS_HASH, "corr-001"
    )
    changed = compute_entry_hash(
        "2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc124", GENESIS_HASH, "corr-001"
    )
    assert base != changed


def test_merkle_chain_starts_at_genesis() -> None:
    chain = MerkleChain()
    assert chain.head == GENESIS_HASH


def test_merkle_chain_append_updates_head() -> None:
    chain = MerkleChain()
    h1 = chain.append("2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc123", "corr-001")
    assert chain.head == h1
    h2 = chain.append("2024-01-01T00:00:01Z", "blue-agent", "classification", "def456", "corr-001")
    assert chain.head == h2
    assert h1 != h2


def test_verify_chain_valid() -> None:
    chain = MerkleChain()
    h1 = chain.append("2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc123", "corr-001")
    h2 = chain.append("2024-01-01T00:00:01Z", "blue-agent", "classification", "def456", "corr-001")

    entries = [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "actor": "red-agent",
            "event_type": "prompt_sent",
            "payload_hash": "abc123",
            "correlation_id": "corr-001",
            "entry_hash": h1,
        },
        {
            "timestamp": "2024-01-01T00:00:01Z",
            "actor": "blue-agent",
            "event_type": "classification",
            "payload_hash": "def456",
            "correlation_id": "corr-001",
            "entry_hash": h2,
        },
    ]
    valid, idx = MerkleChain().verify_chain(entries)
    assert valid is True
    assert idx is None


def test_verify_chain_tamper_detected() -> None:
    chain = MerkleChain()
    h1 = chain.append("2024-01-01T00:00:00Z", "red-agent", "prompt_sent", "abc123", "corr-001")
    h2 = chain.append("2024-01-01T00:00:01Z", "blue-agent", "classification", "def456", "corr-001")

    entries = [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "actor": "red-agent",
            "event_type": "prompt_sent",
            "payload_hash": "abc123",
            "correlation_id": "corr-001",
            "entry_hash": h1,
        },
        {
            "timestamp": "2024-01-01T00:00:01Z",
            "actor": "blue-agent",
            "event_type": "classification",
            "payload_hash": "TAMPERED",  # modified
            "correlation_id": "corr-001",
            "entry_hash": h2,
        },
    ]
    valid, idx = MerkleChain().verify_chain(entries)
    assert valid is False
    assert idx == 1


def test_verify_chain_empty() -> None:
    valid, idx = MerkleChain().verify_chain([])
    assert valid is True
    assert idx is None
