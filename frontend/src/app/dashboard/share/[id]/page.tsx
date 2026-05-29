"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import { credentialApi, shareApi } from "@/lib/api";
import type { Credential, ShareResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  Copy,
  Check,
  QrCode,
  Share2,
  Eye,
  EyeOff,
  ShieldCheck,
  Loader2,
  ExternalLink,
  Clock,
  Lock,
} from "lucide-react";

export default function ShareCredentialPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [credential, setCredential] = useState<Credential | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set());
  const [expiryHours, setExpiryHours] = useState("24");
  const [isSharing, setIsSharing] = useState(false);
  const [shareResult, setShareResult] = useState<ShareResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await credentialApi.getById(id);
        setCredential(res.data);
        // Pre-select all fields
        setSelectedFields(new Set(Object.keys(res.data.claims)));
      } catch {
        toast.error("Credential not found");
        router.push("/dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, router]);

  const toggleField = (key: string) => {
    setSelectedFields((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const selectAll = () => {
    if (credential) {
      setSelectedFields(new Set(Object.keys(credential.claims)));
    }
  };

  const deselectAll = () => setSelectedFields(new Set());

  const handleShare = async () => {
    if (selectedFields.size === 0) {
      toast.error("Select at least one field to share");
      return;
    }

    setIsSharing(true);
    try {
      const res = await shareApi.create({
        credential_id: id,
        selected_fields: Array.from(selectedFields),
        expiry_hours: parseInt(expiryHours),
      });
      setShareResult(res.data);
      toast.success("Share link generated!");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to create share");
    } finally {
      setIsSharing(false);
    }
  };

  const copyLink = async () => {
    if (shareResult) {
      await navigator.clipboard.writeText(shareResult.share_url);
      setCopied(true);
      toast.success("Link copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  if (!credential) return null;

  const allFields = Object.entries(credential.claims);
  const disclosedCount = selectedFields.size;
  const hiddenCount = allFields.length - disclosedCount;

  // ── Share Success State ──────────────────────────────
  if (shareResult) {
    return (
      <div className="max-w-lg mx-auto animate-slide-up">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4 animate-pulse-glow">
            <ShieldCheck className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Share Link Ready!</h2>
          <p className="text-muted-foreground">
            {shareResult.disclosed_fields.length} of{" "}
            {shareResult.total_original_fields} fields will be disclosed
          </p>
        </div>

        {/* QR Code */}
        <Card className="mb-4 border-border/50">
          <CardContent className="pt-6 flex flex-col items-center">
            <div className="p-4 bg-white rounded-2xl mb-4 shadow-lg">
              <QRCodeSVG
                value={shareResult.qr_data}
                size={200}
                level="H"
                includeMargin
              />
            </div>
            <p className="text-sm text-muted-foreground mb-2">
              Scan to verify credentials
            </p>
          </CardContent>
        </Card>

        {/* Share Link */}
        <Card className="mb-4 border-border/50">
          <CardContent className="pt-6">
            <Label className="text-sm font-medium mb-2 block">Share Link</Label>
            <div className="flex gap-2">
              <div className="flex-1 px-3 py-2 bg-muted rounded-lg text-sm font-mono truncate">
                {shareResult.share_url}
              </div>
              <Button
                size="icon"
                variant="outline"
                onClick={copyLink}
                className="shrink-0"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            </div>

            <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                Expires: {new Date(shareResult.expires_at).toLocaleString()}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Disclosed Fields Preview */}
        <Card className="mb-6 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Disclosed Fields</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {shareResult.disclosed_fields.map((field) => (
                <div key={field} className="flex items-center gap-2">
                  <Eye className="w-3.5 h-3.5 text-green-500" />
                  <span className="text-sm capitalize">
                    {field.replace(/([A-Z])/g, " $1").trim()}
                  </span>
                  <span className="text-sm text-muted-foreground ml-auto">
                    {String(credential.claims[field])}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Link href="/dashboard" className="flex-1">
            <Button variant="outline" className="w-full">Dashboard</Button>
          </Link>
          <a href={shareResult.share_url} target="_blank" rel="noopener noreferrer" className="flex-1">
            <Button className="w-full gradient-primary text-white border-0 gap-1">
              Open Link <ExternalLink className="w-3.5 h-3.5" />
            </Button>
          </a>
        </div>
      </div>
    );
  }

  // ── Field Selection State ────────────────────────────
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Selective Disclosure</h1>
          <p className="text-sm text-muted-foreground">
            Choose which fields to share — hidden fields remain cryptographically protected
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* ── Field Selector (left) ──────────────── */}
        <div className="lg:col-span-3">
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Credential Fields</CardTitle>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" className="text-xs h-7" onClick={selectAll}>
                    Select All
                  </Button>
                  <Button variant="ghost" size="sm" className="text-xs h-7" onClick={deselectAll}>
                    Clear
                  </Button>
                </div>
              </div>
              <CardDescription>
                <Badge variant="secondary" className="mr-2">
                  {credential.credential_type.replace("Credential", "")}
                </Badge>
                Tap fields to include or exclude from sharing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {allFields.map(([key, value]) => {
                  const isSelected = selectedFields.has(key);
                  return (
                    <div
                      key={key}
                      onClick={() => toggleField(key)}
                      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-all duration-200 ${
                        isSelected
                          ? "border-primary/30 bg-primary/5"
                          : "border-transparent bg-muted/50 opacity-60"
                      } hover:opacity-100`}
                    >
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleField(key)}
                        className="pointer-events-none"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium capitalize">
                          {key.replace(/([A-Z])/g, " $1").trim()}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {isSelected ? String(value) : "••••••••"}
                        </p>
                      </div>
                      {isSelected ? (
                        <Eye className="w-4 h-4 text-green-500 shrink-0" />
                      ) : (
                        <EyeOff className="w-4 h-4 text-muted-foreground shrink-0" />
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Preview + Controls (right) ─────────── */}
        <div className="lg:col-span-2 space-y-4">
          {/* Summary */}
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Share Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                  <Eye className="w-3.5 h-3.5" /> Disclosed
                </span>
                <Badge variant="secondary">{disclosedCount}</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <Lock className="w-3.5 h-3.5" /> Hidden
                </span>
                <Badge variant="outline">{hiddenCount}</Badge>
              </div>

              <Separator />

              {/* Expiry */}
              <div className="space-y-2">
                <Label className="text-sm">Link Expiry</Label>
                <Select value={expiryHours} onValueChange={setExpiryHours}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 hour</SelectItem>
                    <SelectItem value="6">6 hours</SelectItem>
                    <SelectItem value="24">24 hours</SelectItem>
                    <SelectItem value="168">7 days</SelectItem>
                    <SelectItem value="720">30 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                className="w-full gradient-primary text-white border-0 h-11 gap-2"
                onClick={handleShare}
                disabled={isSharing || selectedFields.size === 0}
              >
                {isSharing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Share2 className="w-4 h-4" />
                )}
                Generate Share Link
              </Button>

              {selectedFields.size === 0 && (
                <p className="text-xs text-destructive text-center">
                  Select at least one field
                </p>
              )}
            </CardContent>
          </Card>

          {/* Crypto Info */}
          <Card className="border-border/50 bg-muted/30">
            <CardContent className="pt-4">
              <div className="space-y-2 text-xs text-muted-foreground">
                <div className="flex items-start gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 mt-0.5 text-primary shrink-0" />
                  <span>
                    Each field gets a Merkle inclusion proof verified against the
                    signed root
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <Lock className="w-3.5 h-3.5 mt-0.5 text-primary shrink-0" />
                  <span>
                    Hidden fields remain cryptographically protected — verifiers
                    cannot reconstruct them
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Label({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <label className={`text-sm font-medium ${className}`}>{children}</label>;
}
