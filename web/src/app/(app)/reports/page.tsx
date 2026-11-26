"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  apiGet,
  type Page,
  type ServiceSummaryReport,
  type WorkOrder,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function ReportsPage() {
  const [summary, setSummary] = useState<ServiceSummaryReport | null>(null);
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const token = getToken();
      if (!token) return;
      try {
        const [report, wo] = await Promise.all([
          apiGet<ServiceSummaryReport>("/reports/service", token),
          apiGet<Page<WorkOrder>>("/work-orders?page_size=50", token),
        ]);
        setSummary(report);
        setOrders(wo.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load reports");
      }
    }
    void load();
  }, []);

  return (
    <>
      <h1 className="page-title">Reports</h1>
      <p className="page-sub">
        Job status, labor/parts summary, and printable service reports (browser print —
        no paid PDF API).
      </p>
      {error ? <div className="error">{error}</div> : null}

      {summary ? (
        <div className="grid-2">
          <div className="panel">
            <h2>Completion</h2>
            <p style={{ fontSize: "2rem", margin: 0 }}>{summary.completion_rate}%</p>
            <p className="muted">
              {summary.completed_jobs} of {summary.total_jobs} jobs completed
            </p>
          </div>
          <div className="panel">
            <h2>Labor minutes</h2>
            <p style={{ fontSize: "2rem", margin: 0 }}>
              {summary.total_labor_minutes}
            </p>
            <p className="muted">Across all technicians</p>
          </div>
        </div>
      ) : null}

      {summary ? (
        <div className="split">
          <div className="panel table-wrap">
            <h2>Jobs by status</h2>
            <table className="data">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Count</th>
                </tr>
              </thead>
              <tbody>
                {summary.jobs_by_status.map((row) => (
                  <tr key={row.status}>
                    <td>
                      <span className="badge">{row.status}</span>
                    </td>
                    <td>{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="panel table-wrap">
            <h2>Labor by technician</h2>
            <table className="data">
              <thead>
                <tr>
                  <th>Technician</th>
                  <th>Minutes</th>
                  <th>Entries</th>
                </tr>
              </thead>
              <tbody>
                {summary.labor.map((row) => (
                  <tr key={row.technician_id ?? "none"}>
                    <td>{row.technician_name ?? "—"}</td>
                    <td>{row.total_minutes}</td>
                    <td>{row.entry_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {summary ? (
        <div className="panel table-wrap">
          <h2>Parts summary</h2>
          {summary.parts_total_cost ? (
            <p className="muted">Parts cost total: {summary.parts_total_cost}</p>
          ) : null}
          <table className="data">
            <thead>
              <tr>
                <th>Part</th>
                <th>Qty</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {summary.parts.map((p) => (
                <tr key={p.part_name}>
                  <td>{p.part_name}</td>
                  <td>{p.total_quantity}</td>
                  <td>{p.total_cost ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <div className="panel table-wrap">
        <h2>Printable service reports</h2>
        <p className="muted">
          Open a job report, capture acknowledgement, then use browser Print.
        </p>
        <table className="data">
          <thead>
            <tr>
              <th>Job</th>
              <th>Status</th>
              <th>Tech</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.title}</td>
                <td>
                  <span className="badge">{o.status}</span>
                </td>
                <td>{o.technician_name ?? "—"}</td>
                <td>
                  <Link
                    className="btn secondary small"
                    href={`/reports/print/${o.id}`}
                  >
                    Open report
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
