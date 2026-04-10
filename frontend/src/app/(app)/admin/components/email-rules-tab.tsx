"use client";

/**
 * E-Mail-Regeln-Tab: Whitelist/Blacklist-Verwaltung.
 * Admin kann Muster hinzufuegen, suchen und loeschen.
 * Wildcards (*) werden unterstuetzt, z.B. *@school.de
 */

import { useState, useEffect, useCallback } from "react";
import { adminApi, EmailRule } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Trash2,
  Plus,
  Search,
  RefreshCw,
  Loader2,
  ShieldCheck,
  ShieldX,
} from "lucide-react";
import { toast } from "sonner";
import { formatDate } from "./admin-utils";

export default function EmailRulesTab() {
  const [rules, setRules] = useState<EmailRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newPattern, setNewPattern] = useState("");
  const [newRuleType, setNewRuleType] = useState<"whitelist" | "blacklist">("blacklist");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"all" | "whitelist" | "blacklist">("all");
  const [isAdding, setIsAdding] = useState(false);

  const fetchRules = useCallback(async () => {
    setIsLoading(true);
    const { data, error } = await adminApi.getEmailRules();
    if (data) setRules(data.rules);
    else if (error) toast.error(`Fehler: ${error}`);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  const handleAddRule = async () => {
    const pattern = newPattern.trim().toLowerCase();
    if (!pattern) {
      toast.error("Bitte ein Muster eingeben");
      return;
    }

    setIsAdding(true);
    const { data, error } = await adminApi.createEmailRule(pattern, newRuleType);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(data?.message || "Regel erstellt");
      setNewPattern("");
      fetchRules();
    }
    setIsAdding(false);
  };

  const handleDeleteRule = async (ruleId: number, pattern: string) => {
    if (!confirm(`Regel "${pattern}" wirklich loeschen?`)) return;

    const { error } = await adminApi.deleteEmailRule(ruleId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(`Regel geloescht: ${pattern}`);
      fetchRules();
    }
  };

  const filteredRules = rules.filter((r) => {
    const matchesSearch = r.pattern.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === "all" || r.rule_type === filterType;
    return matchesSearch && matchesFilter;
  });

  const whitelistCount = rules.filter((r) => r.rule_type === "whitelist").length;
  const blacklistCount = rules.filter((r) => r.rule_type === "blacklist").length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Info */}
      <Card>
        <CardContent className="p-4 text-sm text-muted-foreground">
          <p>
            <strong>Whitelist</strong> hat Vorrang vor <strong>Blacklist</strong>.
            Wildcards mit <code className="rounded bg-muted px-1">*</code> erlaubt (z.B. <code className="rounded bg-muted px-1">*@school.de</code>).
            Ohne Regeln ist die Registrierung offen.
          </p>
        </CardContent>
      </Card>

      {/* Neue Regel hinzufuegen */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Neue Regel</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <Input
              placeholder="z.B. *@school.de oder user@example.com"
              value={newPattern}
              onChange={(e) => setNewPattern(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddRule()}
              className="flex-1"
            />
            <div className="flex items-center gap-1 rounded-md border p-1">
              <Button
                variant={newRuleType === "whitelist" ? "default" : "ghost"}
                size="sm"
                onClick={() => setNewRuleType("whitelist")}
                className="h-7 text-xs"
              >
                <ShieldCheck className="mr-1 h-3.5 w-3.5" />
                Whitelist
              </Button>
              <Button
                variant={newRuleType === "blacklist" ? "destructive" : "ghost"}
                size="sm"
                onClick={() => setNewRuleType("blacklist")}
                className="h-7 text-xs"
              >
                <ShieldX className="mr-1 h-3.5 w-3.5" />
                Blacklist
              </Button>
            </div>
            <Button onClick={handleAddRule} disabled={isAdding || !newPattern.trim()}>
              {isAdding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
              Hinzufuegen
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Regelliste */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Regeln</CardTitle>
              <CardDescription>
                {whitelistCount} Whitelist, {blacklistCount} Blacklist
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={fetchRules}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Aktualisieren
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Suche und Filter */}
          <div className="mb-4 flex items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Regeln suchen..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-1 rounded-md border p-1">
              {(["all", "whitelist", "blacklist"] as const).map((type) => (
                <Button
                  key={type}
                  variant={filterType === type ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => setFilterType(type)}
                  className="h-7 text-xs"
                >
                  {type === "all" ? "Alle" : type === "whitelist" ? "Whitelist" : "Blacklist"}
                </Button>
              ))}
            </div>
          </div>

          {/* Liste */}
          <div className="space-y-2">
            {filteredRules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {rule.rule_type === "whitelist" ? (
                    <ShieldCheck className="h-4 w-4 text-green-600 flex-shrink-0" />
                  ) : (
                    <ShieldX className="h-4 w-4 text-red-600 flex-shrink-0" />
                  )}
                  <div>
                    <span className="font-mono text-sm">{rule.pattern}</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge
                        variant="secondary"
                        className={`text-xs ${
                          rule.rule_type === "whitelist"
                            ? "bg-green-100 text-green-800 border-green-200"
                            : "bg-red-100 text-red-800 border-red-200"
                        }`}
                      >
                        {rule.rule_type === "whitelist" ? "Whitelist" : "Blacklist"}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(rule.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteRule(rule.id, rule.pattern)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}

            {filteredRules.length === 0 && (
              <div className="py-8 text-center text-muted-foreground">
                {rules.length === 0
                  ? "Keine Regeln vorhanden. Registrierung ist offen."
                  : "Keine Regeln gefunden."}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
