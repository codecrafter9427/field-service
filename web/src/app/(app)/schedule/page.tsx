"use client";

import { useCallback, useEffect, useState } from "react";

import {
  apiGet,
  type ScheduleItem,
  type Technician,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function SchedulePage() {
  const [items, setItems] = useState<ScheduleItem[]>([]);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [technicianId, setTechnicianId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      const techs = await apiGet<Technician[]>("/assignments/technicians", token);
      setTechnicians(techs);
      const qs = technicianId ? `?technician_id=${technicianId}` : "";
      const schedule = await apiGet<ScheduleItem[]>(`/schedule${qs}`, token);
      setItems(schedule);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load schedule");
    }
  }, [technicianId]);

  useEffect(() => {
    void load();
  }, [load]);

  const overlapCount = items.filter((i) => i.overlap_warning).length;

  return (
    <>
      <h1 className="page-title">Schedule</h1>
      <p className="page-sub">
        Dispatch list with server-side overlap warnings for the same technician.
      </p>
      {error ? <div className="error">{error}</div> : null}

      <div className="toolbar">
        <label className="field">
          Technician filter
          <select
            value={technicianId}
            onChange={(e) => setTechnicianId(e.target.value)}
          >
            <option value="">All technicians</option>
            {technicians.map((t) => (
              <option key={t.id} value={t.id}>
                {t.display_name}
              </option>
            ))}
          </select>
        </label>
        <button className="btn secondary small" type="button" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      <p className="muted">
        {items.length} jobs · {overlapCount} with overlap warnings
      </p>

      <div className="panel">
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Job</th>
                <th>Technician</th>
                <th>Status</th>
                <th>Window</th>
                <th>Overlap</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.work_order_id}>
                  <td>
                    <strong>{item.title}</strong>
                    <div className="muted">{item.priority}</div>
                  </td>
                  <td>{item.technician_name ?? "Unassigned"}</td>
                  <td>
                    <span className="badge">{item.status}</span>
                  </td>
                  <td className="muted">
                    {item.scheduled_start
                      ? `${new Date(item.scheduled_start).toLocaleString()} → ${
                          item.scheduled_end
                            ? new Date(item.scheduled_end).toLocaleString()
                            : "?"
                        }`
                      : "No window"}
                  </td>
                  <td>
                    {item.overlap_warning ? (
                      <span className="badge warn">
                        warn ({item.overlapping_work_order_ids.length})
                      </span>
                    ) : (
                      <span className="badge ok">ok</span>
                    )}
                  </td>
                </tr>
              ))}
              {!items.length ? (
                <tr>
                  <td colSpan={5} className="muted">
                    No scheduled jobs in range.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
