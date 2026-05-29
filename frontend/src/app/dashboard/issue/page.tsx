"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { credentialApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  Plus,
  Trash2,
  GraduationCap,
  Briefcase,
  UserCheck,
  Sparkles,
  ArrowLeft,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";

const templates: Record<string, { type: string; claims: Record<string, string | number> }> = {
  academic: {
    type: "AcademicCredential",
    claims: {
      name: "Prajwal Kumar",
      degree: "B.Tech Computer Science",
      university: "IIT Delhi",
      graduationYear: 2025,
      cgpa: 8.5,
      rollNumber: "CS2021001",
      issuerName: "Academic Records Office",
      issueDate: new Date().toISOString().split("T")[0],
    },
  },
  professional: {
    type: "ProfessionalCredential",
    claims: {
      name: "Prajwal Kumar",
      title: "Software Engineer",
      company: "Tech Corp",
      department: "Engineering",
      employeeId: "EMP-2024-001",
      startDate: "2024-01-15",
      issuerName: "HR Department",
    },
  },
  identity: {
    type: "IdentityCredential",
    claims: {
      fullName: "Prajwal Kumar",
      dateOfBirth: "1999-05-15",
      nationality: "Indian",
      documentType: "Aadhaar",
      documentNumber: "XXXX-XXXX-1234",
      issuerName: "UIDAI",
      issueDate: new Date().toISOString().split("T")[0],
    },
  },
};

interface ClaimField {
  key: string;
  value: string;
}

export default function IssueCredentialPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [credentialType, setCredentialType] = useState("AcademicCredential");
  const [fields, setFields] = useState<ClaimField[]>([
    { key: "", value: "" },
    { key: "", value: "" },
  ]);

  const updateField = (index: number, prop: "key" | "value", val: string) => {
    setFields((prev) =>
      prev.map((f, i) => (i === index ? { ...f, [prop]: val } : f))
    );
  };

  const addField = () => setFields((prev) => [...prev, { key: "", value: "" }]);

  const removeField = (index: number) => {
    if (fields.length <= 2) {
      toast.error("Minimum 2 fields required");
      return;
    }
    setFields((prev) => prev.filter((_, i) => i !== index));
  };

  const loadTemplate = (name: string) => {
    const tpl = templates[name];
    if (!tpl) return;
    setCredentialType(tpl.type);
    setFields(
      Object.entries(tpl.claims).map(([key, value]) => ({
        key,
        value: String(value),
      }))
    );
    toast.success("Template loaded!");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validFields = fields.filter((f) => f.key.trim() && f.value.trim());
    if (validFields.length < 2) {
      toast.error("Please fill in at least 2 credential fields");
      return;
    }

    // Check for duplicate keys
    const keys = validFields.map((f) => f.key.trim());
    if (new Set(keys).size !== keys.length) {
      toast.error("Duplicate field names are not allowed");
      return;
    }

    // Build claims object — try to parse numbers
    const claims: Record<string, unknown> = {};
    for (const field of validFields) {
      const num = Number(field.value);
      claims[field.key.trim()] = !isNaN(num) && field.value.trim() !== "" && /^[\d.]+$/.test(field.value.trim())
        ? num
        : field.value.trim();
    }

    setIsLoading(true);
    try {
      await credentialApi.issue({
        credential_type: credentialType,
        claims,
      });
      setIsSuccess(true);
      toast.success("Credential issued with cryptographic signature!");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to issue credential");
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="max-w-lg mx-auto text-center py-16 animate-slide-up">
        <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-6 animate-pulse-glow">
          <CheckCircle2 className="w-10 h-10 text-green-500" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Credential Issued! 🎉</h2>
        <p className="text-muted-foreground mb-8">
          Your credential has been cryptographically signed with Ed25519 and
          secured with a Merkle tree. You can now selectively share it.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/dashboard">
            <Button variant="outline">Back to Dashboard</Button>
          </Link>
          <Button
            className="gradient-primary text-white border-0"
            onClick={() => {
              setIsSuccess(false);
              setFields([{ key: "", value: "" }, { key: "", value: "" }]);
            }}
          >
            Issue Another
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Issue Credential</h1>
          <p className="text-sm text-muted-foreground">
            Create a cryptographically signed verifiable credential
          </p>
        </div>
      </div>

      {/* ── Template Selector ─────────────────────── */}
      <Card className="mb-6 border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            Quick Templates
          </CardTitle>
          <CardDescription>Load a pre-filled template to get started quickly</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => loadTemplate("academic")}
            >
              <GraduationCap className="w-3.5 h-3.5" /> Academic
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => loadTemplate("professional")}
            >
              <Briefcase className="w-3.5 h-3.5" /> Professional
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => loadTemplate("identity")}
            >
              <UserCheck className="w-3.5 h-3.5" /> Identity
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Credential Form ───────────────────────── */}
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label>Credential Type</Label>
              <Select value={credentialType} onValueChange={setCredentialType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="AcademicCredential">Academic Credential</SelectItem>
                  <SelectItem value="ProfessionalCredential">Professional Credential</SelectItem>
                  <SelectItem value="IdentityCredential">Identity Credential</SelectItem>
                  <SelectItem value="CustomCredential">Custom Credential</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Credential Claims</Label>
                <Badge variant="secondary" className="text-xs">
                  {fields.filter((f) => f.key.trim()).length} fields
                </Badge>
              </div>

              {fields.map((field, index) => (
                <div key={index} className="flex gap-2 items-start animate-fade-in">
                  <div className="flex-1">
                    <Input
                      placeholder="Field name (e.g., degree)"
                      value={field.key}
                      onChange={(e) => updateField(index, "key", e.target.value)}
                    />
                  </div>
                  <div className="flex-1">
                    <Input
                      placeholder="Value (e.g., B.Tech CS)"
                      value={field.value}
                      onChange={(e) => updateField(index, "value", e.target.value)}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => removeField(index)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full gap-1 border-dashed"
                onClick={addField}
              >
                <Plus className="w-3.5 h-3.5" /> Add Field
              </Button>
            </div>

            <Button
              type="submit"
              className="w-full gradient-primary text-white border-0 h-11"
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : null}
              Issue Credential with Ed25519 Signature
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
