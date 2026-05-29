"""
Integration tests for credential issuance, sharing, and verification.
Tests the complete selective disclosure flow end-to-end.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCredentialIssuance:
    async def test_issue_credential(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/credentials/issue",
            json={
                "credential_type": "AcademicCredential",
                "claims": {
                    "name": "Test Student",
                    "degree": "B.Tech CS",
                    "university": "IIT Delhi",
                    "graduationYear": 2025,
                    "cgpa": 9.0,
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["credential_type"] == "AcademicCredential"
        assert data["merkle_root"]
        assert data["issuer_did"]
        assert data["total_claims"] == 5

    async def test_issue_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/credentials/issue",
            json={"claims": {"name": "Test"}},
        )
        assert response.status_code == 401

    async def test_issue_minimum_claims(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/credentials/issue",
            json={"claims": {"a": 1}},  # Only 1 claim — should fail
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_list_credentials(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        response = await client.get("/api/v1/credentials", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_get_credential_detail(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        cred_id = test_credential["id"]
        response = await client.get(f"/api/v1/credentials/{cred_id}", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
class TestShareAndVerify:
    async def test_create_share(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        response = await client.post(
            "/api/v1/credentials/share",
            json={
                "credential_id": test_credential["id"],
                "selected_fields": ["name", "degree", "university"],
                "expiry_hours": 24,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
        assert "qr_data" in data
        assert len(data["disclosed_fields"]) == 3

    async def test_share_invalid_fields(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        response = await client.post(
            "/api/v1/credentials/share",
            json={
                "credential_id": test_credential["id"],
                "selected_fields": ["nonexistent_field"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_verify_share(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        # Create share
        share_response = await client.post(
            "/api/v1/credentials/share",
            json={
                "credential_id": test_credential["id"],
                "selected_fields": ["name", "degree"],
            },
            headers=auth_headers,
        )
        token = share_response.json()["share_token"]

        # Verify (no auth needed)
        verify_response = await client.get(f"/api/v1/verify/{token}")
        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data["verification"]["verified"] is True
        assert data["verification"]["status"] == "verified"
        assert "name" in data["disclosed_fields"]
        assert "degree" in data["disclosed_fields"]
        # CGPA should NOT be disclosed
        assert "cgpa" not in data["disclosed_fields"]

    async def test_verify_nonexistent_token(self, client: AsyncClient):
        response = await client.get("/api/v1/verify/nonexistent-token-123")
        assert response.status_code == 200
        data = response.json()
        assert data["verification"]["verified"] is False
        assert data["verification"]["status"] == "not_found"

    async def test_full_selective_disclosure_flow(self, client: AsyncClient, auth_headers: dict):
        """
        End-to-end test: Issue → Select fields → Share → Verify
        This validates the entire cryptographic selective disclosure pipeline.
        """
        # Step 1: Issue credential with 7 claims
        issue_resp = await client.post(
            "/api/v1/credentials/issue",
            json={
                "credential_type": "AcademicCredential",
                "claims": {
                    "name": "Prajwal Kumar",
                    "degree": "B.Tech Computer Science",
                    "university": "IIT Delhi",
                    "graduationYear": 2025,
                    "cgpa": 8.5,
                    "rollNumber": "CS2021001",
                    "issuerName": "Academic Records Office",
                },
            },
            headers=auth_headers,
        )
        assert issue_resp.status_code == 201
        credential = issue_resp.json()

        # Step 2: Share only 3 of 7 fields
        share_resp = await client.post(
            "/api/v1/credentials/share",
            json={
                "credential_id": credential["id"],
                "selected_fields": ["name", "degree", "graduationYear"],
                "expiry_hours": 1,
            },
            headers=auth_headers,
        )
        assert share_resp.status_code == 201
        share = share_resp.json()
        assert share["total_original_fields"] == 7
        assert len(share["disclosed_fields"]) == 3

        # Step 3: Verify as a public verifier (no auth)
        verify_resp = await client.get(f"/api/v1/verify/{share['share_token']}")
        assert verify_resp.status_code == 200
        verification = verify_resp.json()

        # Assertions on the verification
        assert verification["verification"]["verified"] is True
        assert verification["verification"]["signature_valid"] is True
        assert verification["verification"]["trust_score"] > 0.9
        assert verification["verification"]["total_fields_disclosed"] == 3

        # Only selected fields are disclosed
        assert "name" in verification["disclosed_fields"]
        assert "degree" in verification["disclosed_fields"]
        assert "graduationYear" in verification["disclosed_fields"]
        assert "cgpa" not in verification["disclosed_fields"]
        assert "rollNumber" not in verification["disclosed_fields"]

        # Each field should be individually verified
        for fv in verification["verification"]["field_verifications"]:
            assert fv["status"] == "verified"
            assert fv["merkle_proof_valid"] is True

    async def test_list_shares(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        # Create a share
        await client.post(
            "/api/v1/credentials/share",
            json={
                "credential_id": test_credential["id"],
                "selected_fields": ["name"],
            },
            headers=auth_headers,
        )

        response = await client.get("/api/v1/credentials/shares", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_revoke_share(self, client: AsyncClient, auth_headers: dict, test_credential: dict):
        # Create a share
        share_resp = await client.post(
            "/api/v1/credentials/share",
            json={
                "credential_id": test_credential["id"],
                "selected_fields": ["name"],
            },
            headers=auth_headers,
        )
        token = share_resp.json()["share_token"]

        # Revoke it
        del_resp = await client.delete(
            f"/api/v1/credentials/shares/{token}", headers=auth_headers
        )
        assert del_resp.status_code == 204

        # Verify it's gone
        verify_resp = await client.get(f"/api/v1/verify/{token}")
        assert verify_resp.json()["verification"]["status"] == "not_found"
