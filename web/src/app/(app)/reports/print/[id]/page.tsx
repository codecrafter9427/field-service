"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { SignaturePad } from "@/components/SignaturePad";
import {
  apiGet,
  apiSend,
  type PrintableServiceReport,
  type Signoff,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function PrintServiceReportPage() {
  const params = useParams<{ id: string }>();
  const workOrderId = params.id;
  const [report, setReport] = useState<PrintableServiceReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [signerName, setSignerName] = useState("");
  const [signatureDataUrl, setSignatureDataUrl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token || !workOrderId) return;
    setError(null);
    try {
      const data = await apiGet<PrintableServiceReport>(
        `/reports/service/work-orders/${workOrderId}`,
        token
      );
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report");
    }
  }, [workOrderId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSignoff(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !workOrderId) return;
    setSaving(true);
    setError(null);
    try {
      await apiSend<Signoff>(
        `/work-orders/${workOrderId}/signoffs`,
        token,
        "POST",
        {
          signer_name: signerName,
          signature_data_url: signatureDataUrl,
        }
      );
      setSignerName("");
      setSignatureDataUrl(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signoff failed");
    } finally {
      setSaving(false);
    }
  }

  if (!report && !error) {
    return <main className="main">Loading service report…</main>;
  }

  return (
    <div className="print-report-page">
      <div className="no-print toolbar" style={{ marginBottom: "1rem" }}>
        <Link href="/work-orders" className="btn secondary small">
          ← Work orders
        </Link>
        <Link href="/reports" className="btn secondary small">
          Reports
        </Link>
        <button type="button" className="btn small" onClick={() => window.print()}>
          Print / Save as PDF
        </button>
      </div>

      {error ? <div className="error no-print">{error}</div> : null}

      {report ? (
        <article className="print-sheet panel">
          <header className="print-header">
            <div>
              <p className="brand-print">Field Service</p>
              <h1>Service report</h1>
              <p className="muted">{report.print_hint}</p>
            </div>
            <div className="print-meta">
              <div>
                <span className="badge">{report.work_order.status}</span>
              </div>
              <div className="muted">
                Job ID: {report.work_order.id.slice(0, 8)}…
              </div>
            </div>
          </header>

          <section>
            <h2>{report.work_order.title}</h2>
            <p>{report.work_order.description ?? "No description."}</p>
            <dl className="report-dl">
              <div>
                <dt>Customer</dt>
                <dd>{report.customer_name ?? "—"}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>{report.location_label ?? "—"}</dd>
              </div>
              <div>
                <dt>Asset</dt>
                <dd>{report.asset_name ?? "—"}</dd>
              </div>
              <div>
                <dt>Technician</dt>
                <dd>{report.work_order.technician_name ?? "Unassigned"}</dd>
              </div>
              <div>
                <dt>Scheduled</dt>
                <dd>
                  {report.work_order.scheduled_start
                    ? new Date(report.work_order.scheduled_start).toLocaleString()
                    : "—"}
                </dd>
              </div>
            </dl>
          </section>

          <section>
            <h2>Notes</h2>
            {report.notes.length === 0 ? (
              <p className="muted">No notes recorded.</p>
            ) : (
              <ul>
                {report.notes.map((n) => (
                  <li key={n.id}>
                    {n.note}{" "}
                    <span className="muted">
                      ({new Date(n.occurred_at).toLocaleString()})
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2>Checklist</h2>
            {report.checklists.length === 0 ? (
              <p className="muted">No checklist.</p>
            ) : (
              report.checklists.map((cl) => (
                <div key={cl.name}>
                  <strong>{cl.name}</strong>
                  <ul>
                    {cl.items.map((item) => (
                      <li key={item.label}>
                        {item.is_completed ? "☑" : "☐"} {item.label}
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            )}
          </section>

          <section>
            <h2>Labor</h2>
            <p>
              Total: <strong>{report.labor_minutes_total}</strong> minutes
            </p>
            <ul>
              {report.time_entries.map((t, idx) => (
                <li key={`${t.started_at}-${idx}`}>
                  {t.technician_name ?? "Tech"} · {t.minutes ?? "?"} min
                  {t.notes ? ` — ${t.notes}` : ""}
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2>Parts</h2>
            {report.parts.length === 0 ? (
              <p className="muted">No parts logged.</p>
            ) : (
              <table className="data">
                <thead>
                  <tr>
                    <th>Part</th>
                    <th>Qty</th>
                    <th>Line</th>
                  </tr>
                </thead>
                <tbody>
                  {report.parts.map((p) => (
                    <tr key={p.id}>
                      <td>{p.part_name}</td>
                      <td>{p.quantity}</td>
                      <td>{p.line_total ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {report.parts_cost_total ? (
              <p>
                Parts total: <strong>{report.parts_cost_total}</strong>
              </p>
            ) : null}
          </section>

          <section>
            <h2>Customer acknowledgement</h2>
            <p className="muted">
              Acknowledgement only — not a certified electronic signature.
            </p>
            {report.signoffs.length === 0 ? (
              <p className="muted">No acknowledgement recorded yet.</p>
            ) : (
              <ul>
                {report.signoffs.map((s) => (
                  <li key={s.id}>
                    <strong>{s.signer_name}</strong> ·{" "}
                    {new Date(s.signed_at).toLocaleString()}
                    <div className="muted">{s.acknowledgement_text}</div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </article>
      ) : null}

      <form className="panel no-print stack" onSubmit={onSignoff}>
        <h2>Capture acknowledgement</h2>
        <p className="muted">
          Labelled as customer acknowledgement, not certified e-sign. Timestamp is
          stored server-side on submit.
        </p>
        <label className="field">
          Signer name
          <input
            value={signerName}
            onChange={(e) => setSignerName(e.target.value)}
            required
            placeholder="Customer name"
          />
        </label>
        <SignaturePad onChange={setSignatureDataUrl} disabled={saving} />
        <button className="btn" type="submit" disabled={saving || !signerName}>
          {saving ? "Saving…" : "Record acknowledgement"}
        </button>
      </form>
    </div>
  );
}
