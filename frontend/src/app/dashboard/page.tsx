"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { credentialApi, shareApi } from "@/lib/api";
import type { Credential, ShareListItem } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FilePlus,
  Share2,
  ShieldCheck,
  FileText,
  ArrowRight,
  Clock,
} from "lucide-react";

export default function DashboardPage() {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [shares, setShares] = useState<ShareListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [credRes, shareRes] = await Promise.all([
          credentialApi.list(),
          shareApi.list(),
        ]);
        setCredentials(credRes.data.credentials);
        setShares(shareRes.data.shares);
      } catch {
        // handled by interceptor
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const activeShares = shares.filter((s) => !s.is_expired);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* ── Stats Cards ──────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger-children">
        <Card className="border-border/50 hover:border-primary/30 transition-colors">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Credentials</p>
                <p className="text-3xl font-bold">{credentials.length}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <FileText className="w-6 h-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 hover:border-primary/30 transition-colors">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Shares</p>
                <p className="text-3xl font-bold">{activeShares.length}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <Share2 className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 hover:border-primary/30 transition-colors">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Verifications</p>
                <p className="text-3xl font-bold">
                  {shares.reduce((sum, s) => sum + s.access_count, 0)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Quick Actions ────────────────────────── */}
      <div className="flex flex-wrap gap-3">
        <Link href="/dashboard/issue">
          <Button className="gradient-primary text-white border-0 gap-2">
            <FilePlus className="w-4 h-4" /> Issue Credential
          </Button>
        </Link>
        <Link href="/dashboard/shares">
          <Button variant="outline" className="gap-2">
            <Share2 className="w-4 h-4" /> View Shares
          </Button>
        </Link>
      </div>

      {/* ── Credential List ──────────────────────── */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Your Credentials</h2>
        {credentials.length === 0 ? (
          <Card className="border-dashed border-2 border-border">
            <CardContent className="py-12 text-center">
              <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-semibold text-lg mb-2">No credentials yet</h3>
              <p className="text-muted-foreground mb-4">
                Issue your first verifiable credential to get started
              </p>
              <Link href="/dashboard/issue">
                <Button className="gradient-primary text-white border-0">
                  Issue Credential
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
            {credentials.map((cred) => (
              <Card
                key={cred.id}
                className="group border-border/50 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <Badge variant="secondary" className="mb-2 text-xs">
                        {cred.credential_type.replace("Credential", "")}
                      </Badge>
                      <CardTitle className="text-base">
                        {(cred.claims.name as string) || (cred.claims.title as string) || "Credential"}
                      </CardTitle>
                    </div>
                    <ShieldCheck className="w-5 h-5 text-green-500 opacity-60 group-hover:opacity-100 transition-opacity" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1.5 text-sm text-muted-foreground mb-4">
                    {Object.entries(cred.claims)
                      .slice(0, 3)
                      .map(([key, val]) => (
                        <div key={key} className="flex justify-between">
                          <span className="capitalize">{key.replace(/([A-Z])/g, " $1").trim()}</span>
                          <span className="font-medium text-foreground truncate ml-2 max-w-[140px]">
                            {String(val)}
                          </span>
                        </div>
                      ))}
                    {cred.total_claims > 3 && (
                      <p className="text-xs text-muted-foreground">
                        +{cred.total_claims - 3} more fields
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-border/50">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {new Date(cred.issued_at).toLocaleDateString()}
                    </div>
                    <Link href={`/dashboard/share/${cred.id}`}>
                      <Button size="sm" variant="ghost" className="gap-1 text-primary">
                        Share <ArrowRight className="w-3 h-3" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
