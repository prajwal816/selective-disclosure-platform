"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { shareApi } from "@/lib/api";
import type { ShareListItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft,
  Clock,
  ExternalLink,
  Eye,
  Share2,
  Trash2,
  AlertTriangle,
} from "lucide-react";

export default function SharesPage() {
  const [shares, setShares] = useState<ShareListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState<string | null>(null);

  useEffect(() => {
    loadShares();
  }, []);

  async function loadShares() {
    try {
      const res = await shareApi.list();
      setShares(res.data.shares);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  }

  async function handleRevoke(token: string) {
    setRevoking(token);
    try {
      await shareApi.revoke(token);
      setShares((prev) => prev.filter((s) => s.share_token !== token));
      toast.success("Share revoked");
    } catch {
      toast.error("Failed to revoke share");
    } finally {
      setRevoking(null);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">My Shares</h1>
          <p className="text-sm text-muted-foreground">
            Manage your active and expired share links
          </p>
        </div>
      </div>

      {shares.length === 0 ? (
        <Card className="border-dashed border-2">
          <CardContent className="py-12 text-center">
            <Share2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-semibold text-lg mb-2">No shares yet</h3>
            <p className="text-muted-foreground mb-4">
              Share a credential to create your first link
            </p>
            <Link href="/dashboard">
              <Button className="gradient-primary text-white border-0">
                Go to Dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3 stagger-children">
          {shares.map((share) => {
            const isExpired = share.is_expired;
            const shareUrl = `${typeof window !== "undefined" ? window.location.origin : ""}/verify/${share.share_token}`;

            return (
              <Card
                key={share.id}
                className={`border-border/50 transition-all ${isExpired ? "opacity-60" : "hover:border-primary/30"}`}
              >
                <CardContent className="pt-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant={isExpired ? "outline" : "secondary"} className="text-xs">
                          {share.credential_type.replace("Credential", "")}
                        </Badge>
                        {isExpired ? (
                          <Badge variant="destructive" className="text-xs gap-1">
                            <AlertTriangle className="w-3 h-3" /> Expired
                          </Badge>
                        ) : (
                          <Badge className="text-xs bg-green-500/10 text-green-600 border-green-500/20 hover:bg-green-500/20">
                            Active
                          </Badge>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5" />
                          {share.disclosed_fields.length} fields disclosed
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          Expires: {new Date(share.expires_at).toLocaleString()}
                        </span>
                        <span className="text-xs">
                          {share.access_count} views
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-1 mt-2">
                        {share.disclosed_fields.map((f) => (
                          <Badge key={f} variant="outline" className="text-xs capitalize">
                            {f.replace(/([A-Z])/g, " $1").trim()}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {!isExpired && (
                        <a href={shareUrl} target="_blank" rel="noopener noreferrer">
                          <Button size="sm" variant="outline" className="gap-1">
                            <ExternalLink className="w-3.5 h-3.5" /> Open
                          </Button>
                        </a>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive hover:text-destructive"
                        onClick={() => handleRevoke(share.share_token)}
                        disabled={revoking === share.share_token}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
