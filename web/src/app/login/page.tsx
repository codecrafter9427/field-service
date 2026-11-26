"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { demoLogin } from "@/lib/api";
import { saveSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("dispatcher@demo.local");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await demoLogin(email, password);
      saveSession(result.access_token, result.user);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-panel" onSubmit={onSubmit}>
        <h1>Field Service</h1>
        <p>Demo login placeholder for dispatchers and technicians.</p>
        {error ? <div className="error">{error}</div> : null}
        <label className="field">
          Email
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="field">
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p className="hint">
          Demo: dispatcher@demo.local / demo · tech@demo.local / demo
        </p>
      </form>
    </div>
  );
}
