"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  apiGet,
  apiSend,
  createPortalLink,
  listPortalLinks,
  revokePortalLink,
  type Checklist,
  type Customer,
  type JobActivity,
  type Page,
  type PartUsed,
  type PortalLink,
  type ServiceLocation,
  type Technician,
  type TimeEntry,
  type WorkOrder,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const STATUSES = [
  "draft",
  "scheduled",
  "en_route",
  "in_progress",
  "waiting_for_parts",
  "completed",
  "cancelled",
];

function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInput(value: string): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

export default function WorkOrdersPage() {
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [locations, setLocations] = useState<ServiceLocation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activities, setActivities] = useState<JobActivity[]>([]);
  const [checklists, setChecklists] = useState<Checklist[]>([]);
  const [timeEntries, setTimeEntries] = useState<TimeEntry[]>([]);
  const [parts, setParts] = useState<PartUsed[]>([]);
  const [partName, setPartName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [portalLinks, setPortalLinks] = useState<PortalLink[]>([]);
  const [portalUrl, setPortalUrl] = useState<string | null>(null);
  const [portalBusy, setPortalBusy] = useState(false);

  const [title, setTitle] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [technicianId, setTechnicianId] = useState("");
  const [status, setStatus] = useState("draft");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [note, setNote] = useState("");
  const [assignTechId, setAssignTechId] = useState("");

  const selected = useMemo(
    () => orders.find((o) => o.id === selectedId) ?? null,
    [orders, selectedId]
  );

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      const [wo, cust, techs] = await Promise.all([
        apiGet<Page<WorkOrder>>("/work-orders?page_size=100", token),
        apiGet<Page<Customer>>("/customers?page_size=100", token),
        apiGet<Technician[]>("/assignments/technicians", token),
      ]);
      setOrders(wo.items);
      setCustomers(cust.items);
      setTechnicians(techs);
      if (!selectedId && wo.items.length) setSelectedId(wo.items[0].id);
      if (!customerId && cust.items.length) setCustomerId(cust.items[0].id);
      if (!technicianId && techs.length) setTechnicianId(techs[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load work orders");
    }
  }, [selectedId, customerId, technicianId]);

  const loadDetail = useCallback(async (workOrderId: string) => {
    const token = getToken();
    if (!token) return;
    try {
      const [acts, cls, times, usedParts] = await Promise.all([
        apiGet<JobActivity[]>(`/work-orders/${workOrderId}/activities`, token),
        apiGet<Checklist[]>(`/checklists?work_order_id=${workOrderId}`, token),
        apiGet<TimeEntry[]>(`/time-entries?work_order_id=${workOrderId}`, token),
        apiGet<PartUsed[]>(`/parts-used?work_order_id=${workOrderId}`, token),
      ]);
      setActivities(acts);
      setChecklists(cls);
      setTimeEntries(times);
      setParts(usedParts);
      setPortalUrl(null);
      try {
        const links = await listPortalLinks(token, workOrderId);
        setPortalLinks(links);
      } catch {
        // Technicians cannot list portal links — ignore 403
        setPortalLinks([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load job detail");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (selectedId) void loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  useEffect(() => {
    async function run() {
      const token = getToken();
      if (!token || !customerId) {
        setLocations([]);
        return;
      }
      const page = await apiGet<Page<ServiceLocation>>(
        `/service-locations?customer_id=${customerId}&page_size=100`,
        token
      );
      setLocations(page.items);
      setLocationId(page.items[0]?.id ?? "");
    }
    void run().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load locations")
    );
  }, [customerId]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token) return;
    setWarning(null);
    try {
      const created = await apiSend<WorkOrder>("/work-orders", token, "POST", {
        title,
        customer_id: customerId,
        service_location_id: locationId || null,
        status,
        scheduled_start: fromLocalInput(start),
        scheduled_end: fromLocalInput(end),
        technician_id: technicianId || null,
      });
      if (created.overlap_warning) {
        setWarning(
          `Created with overlap warning against ${created.overlapping_work_order_ids.length} other job(s).`
        );
      }
      setTitle("");
      setSelectedId(created.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function onStatusChange(next: string) {
    if (!selected) return;
    const token = getToken();
    if (!token) return;
    try {
      await apiSend(`/work-orders/${selected.id}`, token, "PATCH", {
        status: next,
        base_updated_at: selected.updated_at,
      });
      await load();
      await loadDetail(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    }
  }

  async function onAssign(e: FormEvent) {
    e.preventDefault();
    if (!selected || !assignTechId) return;
    const token = getToken();
    if (!token) return;
    setWarning(null);
    try {
      const result = await apiSend<{
        overlap_warning: boolean;
        overlapping_work_order_ids: string[];
      }>("/assignments", token, "POST", {
        work_order_id: selected.id,
        technician_id: assignTechId,
      });
      if (result.overlap_warning) {
        setWarning(
          `Assignment overlap warning vs ${result.overlapping_work_order_ids.length} job(s).`
        );
      }
      await load();
      await loadDetail(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assign failed");
    }
  }

  async function onAddNote(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    const token = getToken();
    if (!token) return;
    try {
      await apiSend(`/work-orders/${selected.id}/notes`, token, "POST", { note });
      setNote("");
      await loadDetail(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Note failed");
    }
  }

  async function toggleChecklistItem(itemId: string, isCompleted: boolean) {
    const token = getToken();
    if (!token || !selected) return;
    const item = checklists
      .flatMap((c) => c.items)
      .find((i) => i.id === itemId);
    if (!item) return;
    try {
      await apiSend(`/checklists/items/${itemId}`, token, "PATCH", {
        is_completed: isCompleted,
        base_updated_at: item.updated_at,
      });
      await loadDetail(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checklist update failed");
    }
  }

  async function onAddTime(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    const token = getToken();
    if (!token) return;
    const started = new Date();
    const ended = new Date(started.getTime() + 60 * 60 * 1000);
    try {
      await apiSend("/time-entries", token, "POST", {
        work_order_id: selected.id,
        technician_id: selected.technician_id,
        started_at: started.toISOString(),
        ended_at: ended.toISOString(),
        notes: "Manual dispatcher time entry",
      });
      await loadDetail(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Time entry failed");
    }
  }

  async function onAddPart(e: FormEvent) {
    e.preventDefault();
    if (!selected || !partName.trim()) return;
    const token = getToken();
    if (!token) return;
    try {
      await apiSend("/parts-used", token, "POST", {
        work_order_id: selected.id,
        part_name: partName.trim(),
        quantity: "1",
        unit_cost: "10.00",
      });
      setPartName("");
      await loadDetail(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parts entry failed");
    }
  }

  async function onCreatePortalLink() {
    if (!selected) return;
    const token = getToken();
    if (!token) return;
    setPortalBusy(true);
    setError(null);
    try {
      const created = await createPortalLink(token, selected.id);
      const absolute = `${window.location.origin}${created.url_path}`;
      setPortalUrl(absolute);
      try {
        await navigator.clipboard.writeText(absolute);
      } catch {
        // Clipboard may be denied; URL still shown
      }
      const links = await listPortalLinks(token, selected.id);
      setPortalLinks(links);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not create customer status link"
      );
    } finally {
      setPortalBusy(false);
    }
  }

  async function onRevokePortalLink(linkId: string) {
    if (!selected) return;
    const token = getToken();
    if (!token) return;
    setPortalBusy(true);
    try {
      await revokePortalLink(token, linkId);
      const links = await listPortalLinks(token, selected.id);
      setPortalLinks(links);
      setPortalUrl(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Revoke failed");
    } finally {
      setPortalBusy(false);
    }
  }

  return (
    <>
      <h1 className="page-title">Work Orders</h1>
      <p className="page-sub">
        Create jobs, assign technicians, update status, notes, checklist, parts, and
        open a printable service report.
      </p>
      {error ? <div className="error">{error}</div> : null}
      {warning ? <div className="badge warn">{warning}</div> : null}

      <div className="panel">
        <h2>Create work order</h2>
        <form className="stack" onSubmit={onCreate}>
          <label className="field">
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <div className="grid-2">
            <label className="field">
              Customer
              <select
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                required
              >
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Service location
              <select
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
              >
                <option value="">—</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Status
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Technician
              <select
                value={technicianId}
                onChange={(e) => setTechnicianId(e.target.value)}
              >
                <option value="">Unassigned</option>
                {technicians.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.display_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Scheduled start
              <input
                type="datetime-local"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </label>
            <label className="field">
              Scheduled end
              <input
                type="datetime-local"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
          </div>
          <button className="btn" type="submit">
            Create job
          </button>
        </form>
      </div>

      <div className="split">
        <div className="panel">
          <h2>Jobs</h2>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Tech</th>
                  <th>Window</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td>
                      <button
                        type="button"
                        className="btn secondary small"
                        onClick={() => setSelectedId(o.id)}
                      >
                        {o.title}
                      </button>
                      {o.overlap_warning ? (
                        <div>
                          <span className="badge warn">overlap</span>
                        </div>
                      ) : null}
                    </td>
                    <td>
                      <span className="badge">{o.status}</span>
                    </td>
                    <td>{o.technician_name ?? "—"}</td>
                    <td className="muted">
                      {o.scheduled_start
                        ? new Date(o.scheduled_start).toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="stack">
          <div className="panel">
            <h2>Job detail</h2>
            {selected ? (
              <>
                <p>
                  <strong>{selected.title}</strong>
                </p>
                <p className="muted">
                  {selected.technician_name
                    ? `Assigned to ${selected.technician_name}`
                    : "Unassigned"}
                  {selected.scheduled_start
                    ? ` · ${toLocalInput(selected.scheduled_start)} → ${toLocalInput(selected.scheduled_end)}`
                    : ""}
                </p>
                <label className="field">
                  Status
                  <select
                    value={selected.status}
                    onChange={(e) => void onStatusChange(e.target.value)}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </label>
                <form className="toolbar" onSubmit={onAssign}>
                  <label className="field" style={{ flex: 1 }}>
                    Assign / reassign
                    <select
                      value={assignTechId || selected.technician_id || ""}
                      onChange={(e) => setAssignTechId(e.target.value)}
                    >
                      <option value="">Select technician</option>
                      {technicians.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.display_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button className="btn small" type="submit">
                    Assign
                  </button>
                </form>
                <Link
                  className="btn secondary small"
                  href={`/reports/print/${selected.id}`}
                >
                  Printable service report
                </Link>
                <div className="portal-box">
                  <h3 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>
                    Customer status link
                  </h3>
                  <p className="muted" style={{ marginTop: 0 }}>
                    Share a read-only job status page (no internal notes or rates).
                  </p>
                  <button
                    type="button"
                    className="btn small"
                    disabled={portalBusy}
                    onClick={() => void onCreatePortalLink()}
                  >
                    Create &amp; copy link
                  </button>
                  {portalUrl ? (
                    <p className="portal-url">
                      Copied (shown once): {portalUrl}
                    </p>
                  ) : null}
                  {portalLinks.filter((l) => l.is_active).length > 0 ? (
                    <ul className="stack" style={{ marginTop: "0.75rem" }}>
                      {portalLinks
                        .filter((l) => l.is_active)
                        .map((l) => (
                          <li key={l.id}>
                            Expires {new Date(l.expires_at).toLocaleString()}{" "}
                            <button
                              type="button"
                              className="btn secondary small"
                              disabled={portalBusy}
                              onClick={() => void onRevokePortalLink(l.id)}
                            >
                              Revoke
                            </button>
                          </li>
                        ))}
                    </ul>
                  ) : (
                    <p className="muted">No active links for this job.</p>
                  )}
                </div>
              </>
            ) : (
              <p className="muted">Select a job</p>
            )}
          </div>

          <div className="panel">
            <h2>Notes</h2>
            <form className="stack" onSubmit={onAddNote}>
              <label className="field">
                Add note
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  required
                  disabled={!selected}
                />
              </label>
              <button className="btn small" type="submit" disabled={!selected}>
                Save note
              </button>
            </form>
            <ul className="stack" style={{ marginTop: "0.85rem" }}>
              {activities
                .filter((a) => a.activity_type === "note")
                .map((a) => (
                  <li key={a.id}>
                    <div>{a.note}</div>
                    <div className="muted">
                      {new Date(a.occurred_at).toLocaleString()}
                    </div>
                  </li>
                ))}
            </ul>
          </div>

          <div className="panel">
            <h2>Checklist</h2>
            {checklists.length === 0 ? (
              <p className="muted">No checklist on this job.</p>
            ) : (
              checklists.map((cl) => (
                <div key={cl.id} className="stack">
                  <strong>{cl.name}</strong>
                  {cl.items.map((item) => (
                    <label key={item.id} className="checklist-item">
                      <input
                        type="checkbox"
                        checked={item.is_completed}
                        onChange={(e) =>
                          void toggleChecklistItem(item.id, e.target.checked)
                        }
                      />
                      {item.label}
                    </label>
                  ))}
                </div>
              ))
            )}
          </div>

          <div className="panel">
            <h2>Time entries</h2>
            <form onSubmit={onAddTime}>
              <button className="btn small" type="submit" disabled={!selected}>
                Add 1h time entry
              </button>
            </form>
            <ul className="stack" style={{ marginTop: "0.85rem" }}>
              {timeEntries.map((t) => (
                <li key={t.id}>
                  {t.minutes ?? "?"} min · {t.notes ?? "No notes"}
                </li>
              ))}
            </ul>
          </div>

          <div className="panel">
            <h2>Parts</h2>
            <form className="toolbar" onSubmit={onAddPart}>
              <label className="field" style={{ flex: 1, marginBottom: 0 }}>
                Part name
                <input
                  value={partName}
                  onChange={(e) => setPartName(e.target.value)}
                  disabled={!selected}
                  required
                />
              </label>
              <button className="btn small" type="submit" disabled={!selected}>
                Add part
              </button>
            </form>
            <ul className="stack" style={{ marginTop: "0.85rem" }}>
              {parts.map((p) => (
                <li key={p.id}>
                  {p.part_name} × {p.quantity}
                  {p.line_total ? ` · ${p.line_total}` : ""}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
