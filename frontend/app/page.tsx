"use client";

import { useState } from "react";

const API_URL = "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAudit() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();

      if (!response.ok) {
        // 422 sends a list of problems; 502/504 send a message
        setError(typeof data.detail === "string" ? data.detail : "Please enter a valid URL.");
      } else {
        setResult(data);
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
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </main>
  );
}