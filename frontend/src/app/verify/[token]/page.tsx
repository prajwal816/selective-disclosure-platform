"use client";

import { useEffect, useState, use } from "react";
import { verifyApi } from "@/lib/api";
import type { PresentationData } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Shield,
  ShieldCheck,
  ShieldX,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Fingerprint,
  Lock,
  Eye,
  Info,
} from "lucide-react";

export default function VerifyPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const [data, setData] = useState<PresentationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await verifyApi.getPresentation(token);
        setData(res.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to load presentation");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="w-full max-w-lg space-y-4">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-destructive/30">
          <CardContent className="pt-8 text-center">
            <ShieldX className="w-16 h-16 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Verification Failed</h2>
            <p className="text-muted-foreground">{error || "Unable to load this presentation"}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const v = data.verification;
  const isVerified = v.verified;
  const isExpired = v.status === "expired";
  const isNotFound = v.status === "not_found";

  // Status display config
  const statusConfig = {
    verified: {
      icon: ShieldCheck,
      color: "text-green-500",
      bg: "bg-green-500/10",
      border: "border-green-500/30",
      label: "Verified",
      message: v.message,
    },
    invalid: {
      icon: ShieldX,
      color: "text-red-500",
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      label: "Invalid",
      message: v.message,
    },
    expired: {
      icon: Clock,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/30",
      label: "Expired",
      message: "This share link has expired and is no longer valid",
    },
    not_found: {
      icon: AlertTriangle,
      color: "text-red-500",
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      label: "Not Found",
      message: "This share link does not exist or has been revoked",
    },
    access_limit: {
      icon: Lock,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/30",
      label: "Access Limit Reached",
      message: "This share link has reached its maximum view count",
    },
    error: {
      icon: XCircle,
      color: "text-red-500",
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      label: "Error",
      message: v.message,
    },
  };

  const status = statusConfig[v.status as keyof typeof statusConfig] || statusConfig.error;
  const StatusIcon = status.icon;

  return (
    <div className="min-h-screen bg-background">
      {/* ── Header ─────────────────────────────────── */}
      <div className="border-b border-border/50 bg-card/50">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-sm">VeriCred Share</span>
            <p className="text-xs text-muted-foreground">Credential Verification</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* ── Status Banner ──────────────────────── */}
        <Card className={`${status.border} border-2 animate-slide-up`}>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <div className={`w-20 h-20 rounded-full ${status.bg} flex items-center justify-center mb-4 ${isVerified ? "animate-pulse-glow" : ""}`}>
                <StatusIcon className={`w-10 h-10 ${status.color}`} />
              </div>
              <h2 className="text-2xl font-bold mb-1">{status.label}</h2>
              <p className="text-sm text-muted-foreground max-w-md">{status.message}</p>

              {v.trust_score !== undefined && v.trust_score !== null && (
                <div className="mt-4 flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Trust Score:</span>
                  <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${
                        v.trust_score > 0.8 ? "bg-green-500" : v.trust_score > 0.5 ? "bg-yellow-500" : "bg-red-500"
                      }`}
                      style={{ width: `${v.trust_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold">{Math.round(v.trust_score * 100)}%</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* ── Disclosed Fields ───────────────────── */}
        {data.disclosed_fields && Object.keys(data.disclosed_fields).length > 0 && (
          <Card className="border-border/50 animate-slide-up" style={{ animationDelay: "0.1s" }}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Eye className="w-4 h-4 text-primary" />
                Disclosed Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(data.disclosed_fields).map(([key, value]) => {
                  const fieldVerification = v.field_verifications?.find(
                    (fv) => fv.field_name === key
                  );
                  const fieldValid = fieldVerification?.status === "verified";

                  return (
                    <div
                      key={key}
                      className="flex items-center justify-between py-2 px-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        {fieldValid ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-500 shrink-0" />
                        )}
                        <div className="min-w-0">
                          <p className="text-xs text-muted-foreground capitalize">
                            {key.replace(/([A-Z])/g, " $1").trim()}
                          </p>
                          <p className="text-sm font-medium truncate">{String(value)}</p>
                        </div>
                      </div>
                      <Badge
                        variant={fieldValid ? "secondary" : "destructive"}
                        className="text-xs shrink-0 ml-2"
                      >
                        {fieldValid ? "Verified" : "Invalid"}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Cryptographic Details ──────────────── */}
        {(v.issuer_did || v.signature_valid !== undefined) && (
          <Card className="border-border/50 animate-slide-up" style={{ animationDelay: "0.2s" }}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Fingerprint className="w-4 h-4 text-primary" />
                Cryptographic Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {v.issuer_did && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Issuer DID</span>
                  <span className="font-mono text-xs truncate max-w-[200px]">
                    {v.issuer_did}
                  </span>
                </div>
              )}
              {v.issued_at && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Issue Date</span>
                  <span>{new Date(v.issued_at).toLocaleDateString()}</span>
                </div>
              )}
              {v.credential_type && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Credential Type</span>
                  <Badge variant="outline" className="text-xs">
                    {v.credential_type.replace("Credential", "")}
                  </Badge>
                </div>
              )}
              {v.signature_valid !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Ed25519 Signature</span>
                  <Badge
                    variant={v.signature_valid ? "secondary" : "destructive"}
                    className="text-xs gap-1"
                  >
                    {v.signature_valid ? (
                      <><CheckCircle2 className="w-3 h-3" /> Valid</>
                    ) : (
                      <><XCircle className="w-3 h-3" /> Invalid</>
                    )}
                  </Badge>
                </div>
              )}
              {v.total_fields_disclosed !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Fields Disclosed</span>
                  <span>{v.total_fields_disclosed} of total</span>
                </div>
              )}
              {v.merkle_root && (
                <div className="pt-2">
                  <p className="text-xs text-muted-foreground mb-1">Merkle Root</p>
                  <p className="font-mono text-xs bg-muted p-2 rounded break-all">
                    {v.merkle_root}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ── Trust Indicators ───────────────────── */}
        {v.trust_indicators && v.trust_indicators.length > 0 && (
          <Card className="border-border/50 animate-slide-up" style={{ animationDelay: "0.3s" }}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Info className="w-4 h-4 text-primary" />
                Trust Indicators
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {v.trust_indicators.map((indicator, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                    <span>{indicator}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Footer ─────────────────────────────── */}
        <div className="text-center py-4 text-xs text-muted-foreground">
          <p className="flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            Verified by VeriCred Share — Cryptographic Selective Disclosure Platform
          </p>
          {v.share_expires_at && (
            <p className="mt-1">
              Share expires: {new Date(v.share_expires_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
