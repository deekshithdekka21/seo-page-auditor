"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Suggestion = {
  suggested_title: string;
  suggested_meta_description: string;
  suggested_h1: string;
  reasoning: string;
};

type AuditResult = {
  url: string;
  title: string | null;
  meta_description: string | null;
  h1: string[];
  issues: string[];
  suggestion: Suggestion | null;
  suggestion_issues: string[] | null;
  suggestion_error: string | null;
};

function ResultCard({ result }: { result: AuditResult }) {
  return (
    <section>
      <h2>Results for {result.url}</h2>

      <p><strong>Title:</strong> {result.title ?? "(missing)"}</p>
      <p><strong>Meta description:</strong> {result.meta_description ?? "(missing)"}</p>
      <p><strong>H1 headings:</strong> {result.h1.length > 0 ? result.h1.join(" | ") : "(none)"}</p>

      <h3>Issues</h3>
      {result.issues.length === 0 ? (
        <p>No issues found. 🎉</p>
      ) : (
        <ul>
          {result.issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      )}

      <h3>AI suggestions</h3>
      {result.suggestion ? (
        <div>
          <p><strong>Title:</strong> {result.suggestion.suggested_title}</p>
          <p><strong>Meta description:</strong> {result.suggestion.suggested_meta_description}</p>
          <p><strong>H1:</strong> {result.suggestion.suggested_h1}</p>
          <p><em>{result.suggestion.reasoning}</em></p>
        </div>
      ) : (
        <p>{result.suggestion_error ?? "No suggestions needed."}</p>
      )}
    </section>
  );
}

type AuditRow = {
  id: number;
  created_at: string;
  result: AuditResult;
};

function RecentAudits({ audits }: { audits: AuditRow[] }) {
  if (audits.length === 0) {
    return <p>No audits yet.</p>;
  }
  return (
    <ul>
      {audits.map((audit) => (
        <li key={audit.id}>
          {audit.result.url}: {audit.result.issues.length} issue(s),{" "}
          {new Date(audit.created_at).toLocaleString()}
        </li>
      ))}
    </ul>
  );
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<AuditResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [audits, setAudits] = useState<AuditRow[]>([]);

  async function loadAudits() {
     try {
       const response = await fetch(`${API_URL}/audits`);
       if (response.ok) {
         setAudits(await response.json());
       }
     } catch {
       // If the list can't load, the rest of the page still works
     }
   }

   useEffect(() => {
     loadAudits();
   }, []);

async function handleAudit() {
    setLoading(true);
    setError(null);
    setResult(null);          // reset: clear the old result

    try {
      const response = await fetch(`${API_URL}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();   // data is created here

      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Please enter a valid URL.");
      } else {
        setResult(data);      // success: show the new result
        loadAudits();         // and refresh the list
      }
    } catch {
      setError("Could not reach the API. Is it running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>SEO Page Auditor</h1>
      <p>Enter a URL to check its title, meta description, and headings.</p>

      <input
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        placeholder="https://example.com"
      />
      <button onClick={handleAudit} disabled={loading || !url}>
        {loading ? "Auditing..." : "Audit"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {result && <ResultCard result={result} />}

      <h2>Recent audits</h2>
      <RecentAudits audits={audits} />
    </main>
  );
}