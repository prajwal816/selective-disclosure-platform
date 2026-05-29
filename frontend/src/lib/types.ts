/**
 * Shared TypeScript types for the VeriCred Share frontend.
 */

// ── Auth ──────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

// ── Credentials ───────────────────────────────────────
export interface Credential {
  id: string;
  credential_type: string;
  claims: Record<string, unknown>;
  merkle_root: string;
  issuer_did: string;
  issued_at: string;
  status: string;
  created_at: string;
  total_claims: number;
}

export interface CredentialListResponse {
  credentials: Credential[];
  total: number;
}

export interface CredentialCreatePayload {
  credential_type: string;
  claims: Record<string, unknown>;
}

// ── Sharing ───────────────────────────────────────────
export interface ShareRequest {
  credential_id: string;
  selected_fields: string[];
  expiry_hours?: number;
}

export interface ShareResponse {
  share_token: string;
  share_url: string;
  qr_data: string;
  expires_at: string;
  disclosed_fields: string[];
  total_original_fields: number;
}

export interface ShareListItem {
  id: string;
  share_token: string;
  credential_id: string;
  credential_type: string;
  disclosed_fields: string[];
  expires_at: string;
  access_count: number;
  max_access_count: number;
  created_at: string;
  is_expired: boolean;
}

export interface ShareListResponse {
  shares: ShareListItem[];
  total: number;
}

// ── Verification ──────────────────────────────────────
export interface FieldVerification {
  field_name: string;
  value: unknown;
  merkle_proof_valid: boolean;
  leaf_hash: string;
  status: "verified" | "invalid" | "error";
}

export interface VerificationResult {
  verified: boolean;
  status: "verified" | "invalid" | "expired" | "not_found" | "access_limit" | "error";
  message: string;
  credential_type?: string;
  issuer_did?: string;
  issued_at?: string;
  disclosed_fields?: Record<string, unknown>;
  field_verifications?: FieldVerification[];
  merkle_root?: string;
  signature_valid?: boolean;
  total_fields_disclosed?: number;
  trust_score?: number;
  trust_indicators?: string[];
  share_created_at?: string;
  share_expires_at?: string;
  access_count?: number;
}

export interface PresentationData {
  share_token: string;
  credential_type: string;
  issuer_did: string;
  issued_at: string;
  disclosed_fields: Record<string, unknown>;
  expires_at: string;
  created_at: string;
  verification: VerificationResult;
}
