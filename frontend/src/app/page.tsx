"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import {
  Shield,
  Lock,
  QrCode,
  CheckCircle2,
  ArrowRight,
  Fingerprint,
  Layers,
  Eye,
} from "lucide-react";

export default function LandingPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      {/* ── Navbar ─────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg">VeriCred Share</span>
          </Link>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link href="/dashboard">
                <Button className="gradient-primary text-white border-0">
                  Dashboard <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm" className="gradient-primary text-white border-0">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ── Hero Section ───────────────────────────── */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-float" style={{ animationDelay: "3s" }} />
        </div>

        <div className="max-w-4xl mx-auto text-center relative">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full border border-primary/20 bg-primary/5 text-sm text-primary">
            <Lock className="w-3.5 h-3.5" />
            Cryptographic Selective Disclosure
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6 leading-[1.1]">
            Share Your Credentials.{" "}
            <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
              Reveal Only What Matters.
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            VeriCred Share uses Merkle trees and Ed25519 signatures to let you
            selectively disclose credential fields while maintaining
            cryptographic verifiability.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href={isAuthenticated ? "/dashboard" : "/register"}>
              <Button size="lg" className="gradient-primary text-white border-0 px-8 h-12 text-base">
                {isAuthenticated ? "Go to Dashboard" : "Start Sharing Securely"}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link href="#how-it-works">
              <Button variant="outline" size="lg" className="h-12 text-base px-8">
                How It Works
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Feature Cards ──────────────────────────── */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Enterprise-Grade Security</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Built with real cryptographic primitives — not just JSON filtering.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 stagger-children">
            {[
              {
                icon: Layers,
                title: "Merkle Tree Proofs",
                desc: "Each credential claim is a leaf in a SHA-256 Merkle tree. Disclose individual fields with cryptographic inclusion proofs.",
              },
              {
                icon: Fingerprint,
                title: "Ed25519 Signatures",
                desc: "The Merkle root is signed with EdDSA. Verifiers can confirm authenticity without seeing undisclosed data.",
              },
              {
                icon: Eye,
                title: "Selective Disclosure",
                desc: "Choose exactly which fields to share. CGPA, marks, roll number — reveal only what the verifier needs.",
              },
              {
                icon: QrCode,
                title: "QR & Share Links",
                desc: "Generate time-limited links and QR codes for instant, mobile-friendly credential sharing.",
              },
              {
                icon: CheckCircle2,
                title: "Instant Verification",
                desc: "Public verification page with per-field trust indicators. No login required to verify.",
              },
              {
                icon: Lock,
                title: "Privacy First",
                desc: "Full credentials never leave your control. Salt-based hashing prevents brute-force attacks on hidden fields.",
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="group p-6 rounded-xl border border-border/50 bg-card hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
              >
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────── */}
      <section id="how-it-works" className="py-20 px-4 bg-muted/30">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground">Three simple steps to verified credential sharing</p>
          </div>

          <div className="space-y-8">
            {[
              {
                step: "01",
                title: "Issue a Credential",
                desc: "Enter your credential claims (name, degree, GPA, etc.). The system generates per-field salts, builds a Merkle tree, and signs the root with Ed25519.",
              },
              {
                step: "02",
                title: "Select & Share",
                desc: "Choose which fields to disclose using simple checkboxes. Merkle inclusion proofs are generated for each selected field. Get a secure, time-limited share link or QR code.",
              },
              {
                step: "03",
                title: "Verify Instantly",
                desc: "The verifier opens the link — no login needed. Each field's Merkle proof is verified against the signed root. Per-field trust indicators show authenticity.",
              },
            ].map((item, i) => (
              <div key={i} className="flex gap-6 items-start">
                <div className="flex-shrink-0 w-12 h-12 rounded-full gradient-primary flex items-center justify-center text-white font-bold text-sm">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">{item.title}</h3>
                  <p className="text-muted-foreground">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────── */}
      <section className="py-20 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Share Securely?</h2>
          <p className="text-muted-foreground mb-8">
            Create your first verifiable credential in under a minute.
          </p>
          <Link href={isAuthenticated ? "/dashboard" : "/register"}>
            <Button size="lg" className="gradient-primary text-white border-0 px-10 h-12">
              {isAuthenticated ? "Open Dashboard" : "Create Free Account"}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────── */}
      <footer className="border-t border-border/50 py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Shield className="w-4 h-4" />
            VeriCred Share — Cryptographic Selective Disclosure Platform
          </div>
          <p className="text-xs text-muted-foreground">
            Merkle Trees • Ed25519 • SHA-256 • Zero-Trust Verification
          </p>
        </div>
      </footer>
    </div>
  );
}
