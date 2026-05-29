"""
Tests for the cryptographic engine — Merkle tree and Ed25519 signatures.
These are the most critical tests as they validate the core selective disclosure logic.
"""

import json
import pytest

from app.core.crypto import (
    Ed25519Signer,
    MerkleTree,
    MerkleTreeData,
    _compute_leaf_hash,
    _sha256,
    create_signing_payload,
    generate_salt,
    generate_salts_for_claims,
)


# ═══════════════════════════════════════════════════════════════════
# SALT GENERATION TESTS
# ═══════════════════════════════════════════════════════════════════


class TestSaltGeneration:
    def test_salt_is_hex_string(self):
        salt = generate_salt()
        assert isinstance(salt, str)
        # 32 bytes → 64 hex chars
        assert len(salt) == 64
        # Should be valid hex
        int(salt, 16)

    def test_salts_are_unique(self):
        salts = [generate_salt() for _ in range(100)]
        assert len(set(salts)) == 100

    def test_generate_salts_for_claims(self):
        claims = {"name": "Alice", "age": 30, "degree": "PhD"}
        salts = generate_salts_for_claims(claims)
        assert set(salts.keys()) == set(claims.keys())
        assert len(set(salts.values())) == 3  # All unique


# ═══════════════════════════════════════════════════════════════════
# MERKLE TREE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestMerkleTree:
    @pytest.fixture
    def sample_claims(self):
        return {
            "name": "Prajwal Kumar",
            "degree": "B.Tech Computer Science",
            "university": "IIT Delhi",
            "graduationYear": 2025,
            "cgpa": 8.5,
            "rollNumber": "CS2021001",
            "issuerName": "Academic Records Office",
        }

    @pytest.fixture
    def sample_salts(self, sample_claims):
        return generate_salts_for_claims(sample_claims)

    @pytest.fixture
    def sample_tree(self, sample_claims, sample_salts):
        return MerkleTree.build(sample_claims, sample_salts)

    def test_build_produces_valid_root(self, sample_tree):
        assert sample_tree.root
        assert isinstance(sample_tree.root, str)
        assert len(sample_tree.root) == 64  # SHA-256 hex

    def test_build_has_correct_leaf_count(self, sample_tree, sample_claims):
        assert len(sample_tree.leaves) == len(sample_claims)

    def test_leaf_keys_are_sorted(self, sample_tree):
        assert sample_tree.leaf_keys == sorted(sample_tree.leaf_keys)

    def test_build_is_deterministic(self, sample_claims, sample_salts):
        tree1 = MerkleTree.build(sample_claims, sample_salts)
        tree2 = MerkleTree.build(sample_claims, sample_salts)
        assert tree1.root == tree2.root

    def test_different_claims_different_root(self, sample_salts):
        claims1 = {"name": "Alice", "age": 30}
        claims2 = {"name": "Bob", "age": 30}
        salts1 = generate_salts_for_claims(claims1)
        salts2 = generate_salts_for_claims(claims2)
        tree1 = MerkleTree.build(claims1, salts1)
        tree2 = MerkleTree.build(claims2, salts2)
        assert tree1.root != tree2.root

    def test_build_empty_claims_raises(self):
        with pytest.raises(ValueError, match="empty claims"):
            MerkleTree.build({}, {})

    def test_build_missing_salt_raises(self):
        with pytest.raises(ValueError, match="Missing salt"):
            MerkleTree.build({"name": "Alice"}, {})

    def test_single_claim_tree(self):
        claims = {"name": "Alice"}
        salts = generate_salts_for_claims(claims)
        tree = MerkleTree.build(claims, salts)
        assert tree.root == tree.leaves[0]  # Single leaf IS the root

    def test_two_claim_tree(self):
        claims = {"a": 1, "b": 2}
        salts = generate_salts_for_claims(claims)
        tree = MerkleTree.build(claims, salts)
        # Root should be hash of two leaves concatenated
        expected = _sha256(tree.leaves[0] + tree.leaves[1])
        assert tree.root == expected

    def test_tree_levels_structure(self, sample_tree):
        # Leaf level should be first
        assert sample_tree.tree_levels[0] == sample_tree.leaves
        # Root level should be last
        assert len(sample_tree.tree_levels[-1]) == 1
        assert sample_tree.tree_levels[-1][0] == sample_tree.root


class TestMerkleProof:
    @pytest.fixture
    def tree_with_claims(self):
        claims = {
            "name": "Prajwal",
            "degree": "B.Tech",
            "university": "IIT Delhi",
            "cgpa": 8.5,
            "year": 2025,
        }
        salts = generate_salts_for_claims(claims)
        tree = MerkleTree.build(claims, salts)
        return claims, salts, tree

    def test_proof_generation_valid_index(self, tree_with_claims):
        claims, salts, tree = tree_with_claims
        for i in range(len(tree.leaves)):
            proof = MerkleTree.generate_proof(i, tree)
            assert isinstance(proof, list)
            assert len(proof) > 0 or len(tree.leaves) == 1

    def test_proof_verification_succeeds(self, tree_with_claims):
        claims, salts, tree = tree_with_claims
        for i, key in enumerate(tree.leaf_keys):
            leaf_hash = _compute_leaf_hash(key, salts[key], claims[key])
            proof = MerkleTree.generate_proof(i, tree)
            assert MerkleTree.verify_proof(leaf_hash, proof, tree.root)

    def test_proof_fails_with_wrong_leaf(self, tree_with_claims):
        _, _, tree = tree_with_claims
        proof = MerkleTree.generate_proof(0, tree)
        fake_leaf = _sha256("fake_data")
        assert not MerkleTree.verify_proof(fake_leaf, proof, tree.root)

    def test_proof_fails_with_wrong_root(self, tree_with_claims):
        claims, salts, tree = tree_with_claims
        key = tree.leaf_keys[0]
        leaf_hash = _compute_leaf_hash(key, salts[key], claims[key])
        proof = MerkleTree.generate_proof(0, tree)
        fake_root = _sha256("fake_root")
        assert not MerkleTree.verify_proof(leaf_hash, proof, fake_root)

    def test_proof_fails_with_tampered_value(self, tree_with_claims):
        claims, salts, tree = tree_with_claims
        key = tree.leaf_keys[0]
        # Tamper the value
        tampered_leaf = _compute_leaf_hash(key, salts[key], "TAMPERED")
        proof = MerkleTree.generate_proof(0, tree)
        assert not MerkleTree.verify_proof(tampered_leaf, proof, tree.root)

    def test_invalid_leaf_index_raises(self, tree_with_claims):
        _, _, tree = tree_with_claims
        with pytest.raises(IndexError):
            MerkleTree.generate_proof(-1, tree)
        with pytest.raises(IndexError):
            MerkleTree.generate_proof(100, tree)

    def test_generate_proofs_for_fields(self, tree_with_claims):
        claims, salts, tree = tree_with_claims
        selected = ["name", "degree"]
        proofs = MerkleTree.generate_proofs_for_fields(
            selected, claims, salts, tree
        )
        assert set(proofs.keys()) == set(selected)
        for key in selected:
            assert "value" in proofs[key]
            assert "salt" in proofs[key]
            assert "leaf_hash" in proofs[key]
            assert "proof" in proofs[key]
            assert proofs[key]["value"] == claims[key]

    def test_selective_disclosure_roundtrip(self, tree_with_claims):
        """End-to-end: issue → select fields → generate proofs → verify each."""
        claims, salts, tree = tree_with_claims
        selected = ["name", "cgpa"]
        proofs = MerkleTree.generate_proofs_for_fields(
            selected, claims, salts, tree
        )

        for key, proof_data in proofs.items():
            # Recompute leaf from disclosed data
            leaf = _compute_leaf_hash(key, proof_data["salt"], proof_data["value"])
            assert leaf == proof_data["leaf_hash"]

            # Reconstruct proof steps
            from app.core.crypto import MerkleProofStep
            steps = [MerkleProofStep.from_dict(s) for s in proof_data["proof"]]

            # Verify against root
            assert MerkleTree.verify_proof(leaf, steps, tree.root)


# ═══════════════════════════════════════════════════════════════════
# ED25519 SIGNATURE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestEd25519Signer:
    def test_key_generation(self):
        signer = Ed25519Signer()
        assert len(signer.private_key_hex) == 64  # 32 bytes hex
        assert len(signer.public_key_hex) == 64

    def test_sign_and_verify(self):
        signer = Ed25519Signer()
        data = "test message to sign"
        signature = signer.sign(data)
        assert signer.verify(data, signature)

    def test_verify_fails_with_wrong_data(self):
        signer = Ed25519Signer()
        signature = signer.sign("original data")
        assert not signer.verify("tampered data", signature)

    def test_verify_fails_with_wrong_signature(self):
        signer = Ed25519Signer()
        signer.sign("some data")
        fake_sig = "a" * 128  # Wrong signature
        assert not signer.verify("some data", fake_sig)

    def test_verify_with_public_key_static(self):
        signer = Ed25519Signer()
        data = "verify with public key"
        signature = signer.sign(data)
        assert Ed25519Signer.verify_with_public_key(
            data, signature, signer.public_key_hex
        )

    def test_deterministic_key_from_hex(self):
        signer1 = Ed25519Signer()
        key_hex = signer1.private_key_hex
        signer2 = Ed25519Signer(key_hex)
        assert signer1.public_key_hex == signer2.public_key_hex

    def test_different_keys_different_signatures(self):
        signer1 = Ed25519Signer()
        signer2 = Ed25519Signer()
        data = "same data"
        sig1 = signer1.sign(data)
        sig2 = signer2.sign(data)
        assert sig1 != sig2

    def test_cross_signer_verification_fails(self):
        signer1 = Ed25519Signer()
        signer2 = Ed25519Signer()
        data = "test data"
        sig = signer1.sign(data)
        assert not signer2.verify(data, sig)


class TestCredentialSigning:
    def test_signing_payload_format(self):
        payload = create_signing_payload("root123", "did:test:issuer", "2025-01-01T00:00:00")
        assert "root:root123" in payload
        assert "issuer:did:test:issuer" in payload
        assert "issued:2025-01-01T00:00:00" in payload

    def test_full_credential_flow(self):
        """End-to-end: create claims → build tree → sign → verify."""
        claims = {
            "name": "Test User",
            "degree": "B.Tech",
            "year": 2025,
        }
        salts = generate_salts_for_claims(claims)
        tree = MerkleTree.build(claims, salts)

        signer = Ed25519Signer()
        payload = create_signing_payload(tree.root, "did:test:issuer", "2025-01-01")
        signature = signer.sign(payload)

        # Verify signature
        assert signer.verify(payload, signature)
        assert Ed25519Signer.verify_with_public_key(
            payload, signature, signer.public_key_hex
        )

        # Selective disclosure: share only "name"
        proofs = MerkleTree.generate_proofs_for_fields(
            ["name"], claims, salts, tree
        )

        # Verifier side: verify the proof
        proof_data = proofs["name"]
        leaf = _compute_leaf_hash("name", proof_data["salt"], proof_data["value"])
        from app.core.crypto import MerkleProofStep
        steps = [MerkleProofStep.from_dict(s) for s in proof_data["proof"]]
        assert MerkleTree.verify_proof(leaf, steps, tree.root)
