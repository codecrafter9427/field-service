"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  apiGet,
  apiSend,
  type Asset,
  type Customer,
  type JobPrepResult,
  type Page,
  type ServiceMemoryResult,
  type ServiceReportDraft,
  type WorkOrder,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

type Tab = "report" | "prep" | "memory";

export default function AIAssistPage() {
  const [tab, setTab] = useState<Tab>("report");
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // Service report state
  const [reportWoId, setReportWoId] = useState("");
  const [extraNotes, setExtraNotes] = useState("");
  const [draft, setDraft] = useState<ServiceReportDraft | null>(null);
  const [problem, setProblem] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [workPerformed, setWorkPerformed] = useState("");
  const [partsText, setPartsText] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [busy, setBusy] = useState(false);

  // Job prep state
  const [prepWoId, setPrepWoId] = useState("");
  const [prep, setPrep] = useState<JobPrepResult | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Record<string, boolean>>(
    {}
  );

  // Service Memory state
  const [memoryQuery, setMemoryQuery] = useState("filter");
  const [memoryAssetId, setMemoryAssetId] = useState("");
  const [memoryCustomerId, setMemoryCustomerId] = useState("");
  const [memory, setMemory] = useState<ServiceMemoryResult | null>(null);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      const [wo, cust, assetPage] = await Promise.all([
        apiGet<Page<WorkOrder>>("/work-orders?page_size=100", token),
        apiGet<Page<Customer>>("/customers?page_size=100", token),
        apiGet<Page<Asset>>("/assets?page_size=100", token),
      ]);
      setOrders(wo.items);
      setCustomers(cust.items);
      setAssets(assetPage.items);
      if (!reportWoId && wo.items.length) setReportWoId(wo.items[0].id);
      if (!prepWoId && wo.items.length) setPrepWoId(wo.items[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load AI context");
    }
  }, [reportWoId, prepWoId]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedReportWo = useMemo(
    () => orders.find((o) => o.id === reportWoId) ?? null,
    [orders, reportWoId]
  );

  async function generateReport(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !reportWoId) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await apiSend<ServiceReportDraft>(
        "/ai/service-report",
        token,
        "POST",
        { work_order_id: reportWoId, notes: extraNotes || null }
      );
      setDraft(result);
      setProblem(result.draft.problem);
      setDiagnosis(result.draft.diagnosis);
      setWorkPerformed(result.draft.work_performed);
      setPartsText(result.draft.parts.join("\n"));
      setFollowUp(result.draft.follow_up);
      setInfo(`Draft from provider "${result.provider}". Edit before approving.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Draft failed");
    } finally {
      setBusy(false);
    }
  }

  async function approveReport(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !reportWoId || !draft) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await apiSend<{
        message: string;
        status_unchanged: string;
        attachment_id: string;
      }>("/ai/service-report/approve", token, "POST", {
        work_order_id: reportWoId,
        problem,
        diagnosis,
        work_performed: workPerformed,
        parts: partsText
          .split("\n")
          .map((p) => p.trim())
          .filter(Boolean),
        follow_up: followUp,
        edited: true,
      });
      setInfo(
        `${result.message} Attachment ${result.attachment_id}. Status stayed ${result.status_unchanged}.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    } finally {
      setBusy(false);
    }
  }

  async function runJobPrep(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !prepWoId) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await apiSend<JobPrepResult>("/ai/job-prep", token, "POST", {
        work_order_id: prepWoId,
      });
      setPrep(result);
      const map: Record<string, boolean> = {};
      for (const s of result.suggested_checklist) map[s.label] = false;
      setSelectedSuggestions(map);
      setInfo(`Job prep from "${result.provider}". Confirm checklist items to add them.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Job prep failed");
    } finally {
      setBusy(false);
    }
  }

  async function confirmChecklist(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !prepWoId) return;
    const items = Object.entries(selectedSuggestions)
      .filter(([, on]) => on)
      .map(([label]) => label);
    if (!items.length) {
      setError("Select at least one suggested checklist item to confirm.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await apiSend<{ message: string; added_labels: string[] }>(
        "/ai/job-prep/confirm-checklist",
        token,
        "POST",
        { work_order_id: prepWoId, items }
      );
      setInfo(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
  }

  async function runMemory(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await apiSend<ServiceMemoryResult>(
        "/ai/service-memory",
        token,
        "POST",
        {
          query: memoryQuery,
          asset_id: memoryAssetId || null,
          customer_id: memoryCustomerId || null,
          limit: 15,
        }
      );
      setMemory(result);
      setInfo(
        `Service Memory (${result.provider}): ${result.hits.length} source job(s). Confirm before creating follow-up work.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Service Memory search failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1 className="page-title">AI Assist</h1>
      <p className="page-sub">
        Demo AI drafts (no Ollama required). Edit and confirm before any business action —
        AI cannot complete jobs or sign for customers.
      </p>

      {error ? <div className="error">{error}</div> : null}
      {info ? <div className="ok-banner">{info}</div> : null}

      <div className="tab-row" role="tablist" aria-label="AI tools">
        {(
          [
            ["report", "Service report"],
            ["prep", "Job prep"],
            ["memory", "Service Memory"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? "tab active" : "tab"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "report" ? (
        <div className="split">
          <form className="panel stack" onSubmit={generateReport}>
            <h2>Draft from notes</h2>
            <p className="muted">
              Structured fields: problem, diagnosis, work, parts, follow-up. AI-labeled —
              you must edit/approve.
            </p>
            <label className="field">
              Work order
              <select
                value={reportWoId}
                onChange={(e) => setReportWoId(e.target.value)}
                required
              >
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.title} ({o.status})
                  </option>
                ))}
              </select>
            </label>
            {selectedReportWo ? (
              <p className="muted">
                Status: {selectedReportWo.status} — approving a report will not change it.
              </p>
            ) : null}
            <label className="field">
              Extra notes / transcript
              <textarea
                value={extraNotes}
                onChange={(e) => setExtraNotes(e.target.value)}
                placeholder="Optional notes to include with stored job notes"
              />
            </label>
            <button className="btn" type="submit" disabled={busy}>
              Generate draft
            </button>
          </form>

          {draft ? (
            <form className="panel stack" onSubmit={approveReport}>
              <h2>Edit &amp; approve</h2>
              <p className="muted">
                Provider: {draft.provider}. AI cannot: {draft.ai_cannot.join(", ")}.
              </p>
              <label className="field">
                Problem
                <textarea value={problem} onChange={(e) => setProblem(e.target.value)} required />
              </label>
              <label className="field">
                Diagnosis
                <textarea value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} />
              </label>
              <label className="field">
                Work performed
                <textarea
                  value={workPerformed}
                  onChange={(e) => setWorkPerformed(e.target.value)}
                  required
                />
              </label>
              <label className="field">
                Parts (one per line)
                <textarea value={partsText} onChange={(e) => setPartsText(e.target.value)} />
              </label>
              <label className="field">
                Follow-up
                <textarea value={followUp} onChange={(e) => setFollowUp(e.target.value)} />
              </label>
              <button className="btn" type="submit" disabled={busy}>
                Approve edited report
              </button>
              <ul className="muted source-list">
                {draft.sources.map((s) => (
                  <li key={`${s.type}-${s.id}`}>
                    {s.type}: {s.label}
                  </li>
                ))}
              </ul>
            </form>
          ) : (
            <div className="panel">
              <h2>No draft yet</h2>
              <p className="muted">Generate a draft from a work order to edit it here.</p>
            </div>
          )}
        </div>
      ) : null}

      {tab === "prep" ? (
        <div className="split">
          <form className="panel stack" onSubmit={runJobPrep}>
            <h2>Job prep summary</h2>
            <p className="muted">
              Uses asset/customer history and existing checklist. Suggestions by job type
              need confirmation.
            </p>
            <label className="field">
              Work order
              <select value={prepWoId} onChange={(e) => setPrepWoId(e.target.value)} required>
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.title}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn" type="submit" disabled={busy}>
              Prepare job
            </button>
          </form>

          {prep ? (
            <div className="panel stack">
              <h2>Prep result</h2>
              <p>{prep.summary}</p>
              <p className="muted">{prep.explanation}</p>
              {prep.history_highlights.length ? (
                <>
                  <h3 className="section-h">History highlights</h3>
                  <ul>
                    {prep.history_highlights.map((h, i) => (
                      <li key={`${i}-${h.slice(0, 24)}`}>{h}</li>
                    ))}
                  </ul>
                </>
              ) : null}
              <form className="stack" onSubmit={confirmChecklist}>
                <h3 className="section-h">Suggested checklist (confirm to add)</h3>
                {prep.suggested_checklist.map((s) => (
                  <label key={s.label} className="checklist-item">
                    <input
                      type="checkbox"
                      checked={!!selectedSuggestions[s.label]}
                      onChange={(e) =>
                        setSelectedSuggestions((prev) => ({
                          ...prev,
                          [s.label]: e.target.checked,
                        }))
                      }
                    />
                    <span>
                      {s.label}
                      <span className="muted"> — {s.reason}</span>
                    </span>
                  </label>
                ))}
                <button className="btn" type="submit" disabled={busy}>
                  Confirm selected items
                </button>
              </form>
            </div>
          ) : (
            <div className="panel">
              <h2>No prep yet</h2>
              <p className="muted">Run job prep on a scheduled work order.</p>
            </div>
          )}
        </div>
      ) : null}

      {tab === "memory" ? (
        <div className="split">
          <form className="panel stack" onSubmit={runMemory}>
            <h2>Service Memory</h2>
            <p className="muted">
              Search recurring failures by asset or customer. Summary uses recorded history
              only.
            </p>
            <label className="field">
              Query
              <input
                value={memoryQuery}
                onChange={(e) => setMemoryQuery(e.target.value)}
                placeholder="filter, leak, vibration…"
              />
            </label>
            <label className="field">
              Asset (optional)
              <select
                value={memoryAssetId}
                onChange={(e) => setMemoryAssetId(e.target.value)}
              >
                <option value="">Any asset</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.asset_type ?? "—"})
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Customer (optional)
              <select
                value={memoryCustomerId}
                onChange={(e) => setMemoryCustomerId(e.target.value)}
              >
                <option value="">Any customer</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn" type="submit" disabled={busy}>
              Search memory
            </button>
          </form>

          {memory ? (
            <div className="panel stack">
              <h2>Summary</h2>
              <p className="muted">{memory.explanation}</p>
              <ul>
                {memory.recurring_themes.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
              <p>
                <strong>Suggested follow-up:</strong> {memory.suggested_follow_up}
              </p>
              <p className="muted">
                Human confirmation required before creating follow-up work. Provider:{" "}
                {memory.provider}.
              </p>
              <h3 className="section-h">Source jobs</h3>
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Job</th>
                      <th>Asset</th>
                      <th>Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {memory.hits.map((h) => (
                      <tr key={`${h.work_order_id}-${h.occurred_at}`}>
                        <td>
                          {h.title}
                          <div className="muted">{h.status}</div>
                        </td>
                        <td>{h.asset_name ?? "—"}</td>
                        <td>{h.note_excerpt ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="panel">
              <h2>No search yet</h2>
              <p className="muted">
                Try query &quot;filter&quot; on Rooftop HVAC for the seeded recurring pattern.
              </p>
            </div>
          )}
        </div>
      ) : null}
    </>
  );
}
