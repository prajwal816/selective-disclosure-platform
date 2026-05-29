"""
Cryptographic engine for selective disclosure using Merkle trees and Ed25519 signatures.

This module implements the core cryptographic primitives:
1. MerkleTree: Builds hash trees from credential claims, generates inclusion proofs,
   and verifies proofs for selective disclosure.
2. Ed25519Signer: Signs and verifies Merkle roots using Ed25519 (EdDSA) via PyNaCl.
3. Salt generation: Cryptographically random per-claim salts to prevent brute-force attacks.

Flow:
  ISSUANCE:   claims → salt each → leaf = SHA256(key:salt:value) → build tree → sign root
  SHARING:    select fields → generate Merkle proof per field → bundle as presentation
  VERIFICATION: recompute leaf → walk proof to root → verify signature on root
"""

import hashlib
import json
import math
import os
import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import nacl.encoding
import nacl.signing


# ═══════════════════════════════════════════════════════════════════
# SALT GENERATION
# ═══════════════════════════════════════════════════════════════════

def generate_salt() -> str:
    """Generate a cryptographically random 32-byte hex salt."""
    return secrets.token_hex(32)


def generate_salts_for_claims(claims: Dict[str, Any]) -> Dict[str, str]:
    """Generate a unique random salt for each claim key."""
    return {key: generate_salt() for key in claims}


# ═══════════════════════════════════════════════════════════════════
# MERKLE TREE
# ═══════════════════════════════════════════════════════════════════

def _sha256(data: str) -> str:
    """Compute SHA-256 hash of a string, return hex digest."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _compute_leaf_hash(key: str, salt: str, value: Any) -> str:
    """
    Compute the leaf hash for a single credential claim.
    
    Canonical format: SHA256("key" + ":" + "salt" + ":" + json(value))
    Using JSON serialization for the value ensures deterministic hashing
    regardless of Python type (str, int, float, bool, etc.).
    """
    canonical_value = json.dumps(value, sort_keys=True, separators=(",", ":"))
    leaf_input = f"{key}:{salt}:{canonical_value}"
    return _sha256(leaf_input)


@dataclass
class MerkleProofStep:
    """A single step in a Merkle inclusion proof."""
    hash: str
    position: str  # "left" or "right" — the sibling's position

    def to_dict(self) -> dict:
        return {"hash": self.hash, "position": self.position}

    @classmethod
    def from_dict(cls, data: dict) -> "MerkleProofStep":
        return cls(hash=data["hash"], position=data["position"])


@dataclass
class MerkleTreeData:
    """Complete Merkle tree data structure."""
    root: str
    leaves: List[str]
    leaf_keys: List[str]  # Ordered claim keys corresponding to leaves
    tree_levels: List[List[str]]  # All levels of the tree, from leaves to root


class MerkleTree:
    """
    Merkle tree implementation for selective disclosure of credential claims.
    
    Builds a binary hash tree from credential claims where each leaf is
    SHA256(key:salt:value). Supports generating and verifying inclusion proofs
    for individual claims.
    """

    @staticmethod
    def build(
        claims: Dict[str, Any], salts: Dict[str, str]
    ) -> MerkleTreeData:
        """
        Build a Merkle tree from claims and their corresponding salts.
        
        Args:
            claims: Dictionary of claim key → value pairs.
            salts: Dictionary of claim key → random salt pairs.
            
        Returns:
            MerkleTreeData containing the root, leaves, and full tree structure.
        """
        if not claims:
            raise ValueError("Cannot build Merkle tree from empty claims")

        # Sort keys for deterministic ordering
        sorted_keys = sorted(claims.keys())

        # Compute leaf hashes
        leaves = []
        for key in sorted_keys:
            if key not in salts:
                raise ValueError(f"Missing salt for claim key: {key}")
            leaf_hash = _compute_leaf_hash(key, salts[key], claims[key])
            leaves.append(leaf_hash)

        # Build tree levels bottom-up
        tree_levels = [leaves.copy()]
        current_level = leaves.copy()

        while len(current_level) > 1:
            next_level = []
            # If odd number of nodes, duplicate the last one
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i + 1]
                parent_hash = _sha256(combined)
                next_level.append(parent_hash)

            tree_levels.append(next_level)
            current_level = next_level

        root = current_level[0] if current_level else ""

        return MerkleTreeData(
            root=root,
            leaves=leaves,
            leaf_keys=sorted_keys,
            tree_levels=tree_levels,
        )

    @staticmethod
    def generate_proof(
        leaf_index: int, tree_data: MerkleTreeData
    ) -> List[MerkleProofStep]:
        """
        Generate a Merkle inclusion proof for a leaf at the given index.
        
        The proof consists of sibling hashes at each level, along with their
        position (left or right), enabling reconstruction of the root.
        
        Args:
            leaf_index: Index of the leaf in the sorted claims list.
            tree_data: The full Merkle tree data.
            
        Returns:
            List of MerkleProofStep objects forming the inclusion proof.
        """
        if leaf_index < 0 or leaf_index >= len(tree_data.leaves):
            raise IndexError(
                f"Leaf index {leaf_index} out of range [0, {len(tree_data.leaves)})"
            )

        proof = []
        current_index = leaf_index

        for level in tree_data.tree_levels[:-1]:  # Skip the root level
            # Handle odd-length levels (last node duplicated)
            working_level = level.copy()
            if len(working_level) % 2 != 0:
                working_level.append(working_level[-1])

            # Determine sibling
            if current_index % 2 == 0:
                # Current is left child, sibling is right
                sibling_index = current_index + 1
                sibling_position = "right"
            else:
                # Current is right child, sibling is left
                sibling_index = current_index - 1
                sibling_position = "left"

            if sibling_index < len(working_level):
                proof.append(
                    MerkleProofStep(
                        hash=working_level[sibling_index],
                        position=sibling_position,
                    )
                )

            # Move to parent index
            current_index = current_index // 2

        return proof

    @staticmethod
    def verify_proof(
        leaf_hash: str,
        proof: List[MerkleProofStep],
        expected_root: str,
    ) -> bool:
        """
        Verify a Merkle inclusion proof against an expected root.
        
        Recomputes the root from the leaf hash and proof steps, then compares
        against the expected root.
        
        Args:
            leaf_hash: The hash of the leaf being verified.
            proof: The Merkle proof (list of sibling hashes with positions).
            expected_root: The expected Merkle root (signed by issuer).
            
        Returns:
            True if the proof is valid and the leaf belongs to the tree.
        """
        current_hash = leaf_hash

        for step in proof:
            if step.position == "left":
                # Sibling is on the left
                combined = step.hash + current_hash
            else:
                # Sibling is on the right
                combined = current_hash + step.hash

            current_hash = _sha256(combined)

        return current_hash == expected_root

    @staticmethod
    def generate_proofs_for_fields(
        selected_keys: List[str],
        claims: Dict[str, Any],
        salts: Dict[str, str],
        tree_data: MerkleTreeData,
    ) -> Dict[str, dict]:
        """
        Generate Merkle proofs for multiple selected fields at once.
        
        Args:
            selected_keys: List of claim keys to disclose.
            claims: Full claims dictionary.
            salts: Full salts dictionary.
            tree_data: The complete Merkle tree data.
            
        Returns:
            Dictionary mapping each selected key to its proof data:
            {key: {"value": ..., "salt": ..., "leaf_hash": ..., "proof": [...], "leaf_index": int}}
        """
        proofs = {}

        for key in selected_keys:
            if key not in claims:
                raise ValueError(f"Selected key '{key}' not found in claims")
            if key not in tree_data.leaf_keys:
                raise ValueError(
                    f"Selected key '{key}' not found in tree leaf keys"
                )

            leaf_index = tree_data.leaf_keys.index(key)
            leaf_hash = _compute_leaf_hash(key, salts[key], claims[key])
            proof = MerkleTree.generate_proof(leaf_index, tree_data)

            proofs[key] = {
                "value": claims[key],
                "salt": salts[key],
                "leaf_hash": leaf_hash,
                "proof": [step.to_dict() for step in proof],
                "leaf_index": leaf_index,
            }

        return proofs


# ═══════════════════════════════════════════════════════════════════
# ED25519 DIGITAL SIGNATURES
# ═══════════════════════════════════════════════════════════════════

class Ed25519Signer:
    """
    Ed25519 (EdDSA) digital signature manager using PyNaCl.
    
    Provides signing and verification of data (typically Merkle roots)
    using Ed25519 key pairs. Keys can be generated fresh or loaded from
    hex-encoded seeds.
    """

    def __init__(self, private_key_hex: Optional[str] = None):
        """
        Initialize the signer with an existing key or generate a new one.
        
        Args:
            private_key_hex: Hex-encoded 32-byte seed for the signing key.
                           If empty/None, generates a new random key pair.
        """
        if private_key_hex:
            seed = bytes.fromhex(private_key_hex)
            self._signing_key = nacl.signing.SigningKey(seed)
        else:
            self._signing_key = nacl.signing.SigningKey.generate()

        self._verify_key = self._signing_key.verify_key

    @property
    def private_key_hex(self) -> str:
        """Get the hex-encoded private key seed (for secure storage)."""
        return self._signing_key.encode(
            encoder=nacl.encoding.HexEncoder
        ).decode("utf-8")

    @property
    def public_key_hex(self) -> str:
        """Get the hex-encoded public verification key (safe to share)."""
        return self._verify_key.encode(
            encoder=nacl.encoding.HexEncoder
        ).decode("utf-8")

    def sign(self, data: str) -> str:
        """
        Sign a string payload and return the hex-encoded signature.
        
        Args:
            data: The string data to sign (e.g., Merkle root + metadata).
            
        Returns:
            Hex-encoded Ed25519 signature (128 hex characters = 64 bytes).
        """
        signed = self._signing_key.sign(data.encode("utf-8"))
        # Extract just the signature (first 64 bytes of SignedMessage)
        return signed.signature.hex()

    def verify(self, data: str, signature_hex: str) -> bool:
        """
        Verify an Ed25519 signature against the expected data.
        
        Args:
            data: The original string data that was signed.
            signature_hex: The hex-encoded signature to verify.
            
        Returns:
            True if the signature is valid, False otherwise.
        """
        try:
            signature_bytes = bytes.fromhex(signature_hex)
            self._verify_key.verify(
                data.encode("utf-8"), signature_bytes
            )
            return True
        except (nacl.exceptions.BadSignatureError, ValueError):
            return False

    @staticmethod
    def verify_with_public_key(
        data: str, signature_hex: str, public_key_hex: str
    ) -> bool:
        """
        Statically verify a signature using only the public key.
        
        This is used by verifiers who don't have the private key.
        
        Args:
            data: The original signed data.
            signature_hex: The hex-encoded signature.
            public_key_hex: The hex-encoded Ed25519 public key.
            
        Returns:
            True if the signature is valid.
        """
        try:
            verify_key = nacl.signing.VerifyKey(
                bytes.fromhex(public_key_hex)
            )
            verify_key.verify(
                data.encode("utf-8"),
                bytes.fromhex(signature_hex),
            )
            return True
        except (nacl.exceptions.BadSignatureError, ValueError):
            return False


# ═══════════════════════════════════════════════════════════════════
# CREDENTIAL SIGNING HELPERS
# ═══════════════════════════════════════════════════════════════════

def create_signing_payload(
    merkle_root: str, issuer_did: str, issued_at: str
) -> str:
    """
    Create the canonical payload string to be signed by the issuer.
    
    Format: "root:{merkle_root}|issuer:{issuer_did}|issued:{issued_at}"
    
    This binds the Merkle root to the issuer identity and timestamp,
    preventing replay attacks and root substitution.
    """
    return f"root:{merkle_root}|issuer:{issuer_did}|issued:{issued_at}"


# ═══════════════════════════════════════════════════════════════════
# SINGLETON SIGNER INSTANCE
# ═══════════════════════════════════════════════════════════════════

_signer_instance: Optional[Ed25519Signer] = None


def get_signer() -> Ed25519Signer:
    """
    Get or create the application-wide Ed25519 signer.
    
    Loads the private key from settings if configured, otherwise generates
    a new key pair and logs a warning.
    """
    global _signer_instance
    if _signer_instance is None:
        from app.core.config import get_settings

        settings = get_settings()
        key_hex = settings.ED25519_PRIVATE_KEY_HEX

        if key_hex:
            _signer_instance = Ed25519Signer(key_hex)
        else:
            _signer_instance = Ed25519Signer()
            import logging
            logging.warning(
                "No ED25519_PRIVATE_KEY_HEX configured. "
                "Generated ephemeral key pair. Set this in production! "
                f"Generated private key: {_signer_instance.private_key_hex}"
            )

    return _signer_instance
