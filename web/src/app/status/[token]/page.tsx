"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import {
  fetchPublicJobStatus,
  type CustomerJobStatus,
} from "@/lib/api";

export default function CustomerStatusPage() {
  const params = useParams<{ token: string }>();
  const token = typeof params.token === "string" ? params.token : "";
  const [data, setData] = useState<CustomerJobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setError("Missing status link");
      setLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const status = await fetchPublicJobStatus(token);
        if (!cancelled) {
          setData(status);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "This status link is invalid, expired, or revoked."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <main className="status-page">
      <header className="status-hero">
        <p className="brand">Field Service</p>
        <h1>Job status</h1>
        <p className="page-sub">
          Read-only visit update for your service appointment.
        </p>
      </header>

      {loading ? <p className="muted">Loading…</p> : null}
      {error ? <div className="error">{error}</div> : null}

      {data ? (
        <section className="panel status-panel">
          <h2>{data.title}</h2>
          <p>
            <span className="badge">{data.status.replaceAll("_", " ")}</span>
          </p>
          <dl className="status-dl">
            <div>
              <dt>Customer</dt>
              <dd>{data.customer_name ?? "—"}</dd>
            </div>
            <div>
              <dt>Location</dt>
              <dd>{data.location_label ?? "—"}</dd>
            </div>
            <div>
              <dt>Asset</dt>
              <dd>{data.asset_name ?? "—"}</dd>
            </div>
            <div>
              <dt>Scheduled visit</dt>
              <dd>
                {data.scheduled_start
                  ? `${new Date(data.scheduled_start).toLocaleString()}${
                      data.scheduled_end
                        ? ` → ${new Date(data.scheduled_end).toLocaleString()}`
                        : ""
                    }`
                  : "Not scheduled"}
              </dd>
            </div>
            <div>
              <dt>Service summary</dt>
              <dd>{data.service_summary ?? "No public summary yet."}</dd>
            </div>
            {data.checklist_progress ? (
              <div>
                <dt>Checklist progress</dt>
                <dd>
                  {data.checklist_progress.completed} of{" "}
                  {data.checklist_progress.total} items complete
                </dd>
              </div>
            ) : null}
            {data.parts.length > 0 ? (
              <div>
                <dt>Parts used</dt>
                <dd>
                  <ul>
                    {data.parts.map((p) => (
                      <li key={`${p.part_name}-${p.quantity}`}>
                        {p.part_name} × {p.quantity}
                      </li>
                    ))}
                  </ul>
                </dd>
              </div>
            ) : null}
            <div>
              <dt>Acknowledgement</dt>
              <dd>
                {data.acknowledgement_recorded
                  ? `Recorded${
                      data.acknowledged_at
                        ? ` · ${new Date(data.acknowledged_at).toLocaleString()}`
                        : ""
                    }`
                  : "Not recorded yet"}
              </dd>
            </div>
          </dl>
          <p className="muted">
            Link expires {new Date(data.link_expires_at).toLocaleString()}.
          </p>
        </section>
      ) : null}
    </main>
  );
}
