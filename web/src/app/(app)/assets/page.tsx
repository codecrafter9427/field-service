"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  apiGet,
  apiSend,
  type Asset,
  type Customer,
  type Page,
  type ServiceHistoryItem,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [history, setHistory] = useState<ServiceHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const [name, setName] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [serial, setSerial] = useState("");
  const [assetType, setAssetType] = useState("");
  const [notes, setNotes] = useState("");

  const selected = assets.find((a) => a.id === selectedId) ?? null;

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      const query = q.trim() ? `&q=${encodeURIComponent(q.trim())}` : "";
      const [page, cust] = await Promise.all([
        apiGet<Page<Asset>>(`/assets?page_size=100${query}`, token),
        apiGet<Page<Customer>>("/customers?page_size=100", token),
      ]);
      setAssets(page.items);
      setCustomers(cust.items);
      if (!customerId && cust.items.length) setCustomerId(cust.items[0].id);
      if (selectedId && !page.items.some((a) => a.id === selectedId)) {
        setSelectedId(page.items[0]?.id ?? null);
      } else if (!selectedId && page.items.length) {
        setSelectedId(page.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load assets");
    }
  }, [q, customerId, selectedId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    async function run() {
      const token = getToken();
      if (!token || !selectedId) {
        setHistory([]);
        return;
      }
      const rows = await apiGet<ServiceHistoryItem[]>(
        `/assets/${selectedId}/service-history`,
        token
      );
      setHistory(rows);
    }
    void run().catch((err) =>
      setError(err instanceof Error ? err.message : "History failed")
    );
  }, [selectedId]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token) return;
    try {
      const created = await apiSend<Asset>("/assets", token, "POST", {
        customer_id: customerId,
        name,
        serial_number: serial || null,
        asset_type: assetType || null,
        maintenance_notes: notes || null,
      });
      setName("");
      setSerial("");
      setAssetType("");
      setNotes("");
      setSelectedId(created.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function onSaveNotes(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    const token = getToken();
    if (!token) return;
    try {
      await apiSend(`/assets/${selected.id}`, token, "PATCH", {
        maintenance_notes: notes || selected.maintenance_notes,
        name: selected.name,
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function onArchive() {
    if (!selected) return;
    if (!confirm(`Archive asset “${selected.name}”?`)) return;
    const token = getToken();
    if (!token) return;
    try {
      await apiSend(`/assets/${selected.id}`, token, "DELETE");
      setSelectedId(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Archive failed");
    }
  }

  return (
    <>
      <h1 className="page-title">Assets</h1>
      <p className="page-sub">
        Equipment register with create/edit/archive and service history by asset.
      </p>
      {error ? <div className="error">{error}</div> : null}

      <div className="panel">
        <h2>Add asset</h2>
        <form className="stack" onSubmit={onCreate}>
          <div className="grid-2">
            <label className="field">
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
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
              Serial
              <input value={serial} onChange={(e) => setSerial(e.target.value)} />
            </label>
            <label className="field">
              Type
              <input
                value={assetType}
                onChange={(e) => setAssetType(e.target.value)}
                placeholder="HVAC, pump…"
              />
            </label>
          </div>
          <label className="field">
            Maintenance notes
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>
          <button className="btn" type="submit">
            Create asset
          </button>
        </form>
      </div>

      <div className="toolbar">
        <label className="field" style={{ marginBottom: 0, flex: 1 }}>
          Search
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Name, serial, type"
          />
        </label>
        <button type="button" className="btn secondary small" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      <div className="split">
        <div className="panel table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Serial</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr key={a.id}>
                  <td>
                    <button
                      type="button"
                      className="btn secondary small"
                      onClick={() => {
                        setSelectedId(a.id);
                        setNotes(a.maintenance_notes ?? "");
                      }}
                    >
                      {a.name}
                    </button>
                  </td>
                  <td>{a.asset_type ?? "—"}</td>
                  <td>{a.serial_number ?? "—"}</td>
                  <td>{a.maintenance_notes ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="stack">
          <div className="panel">
            <h2>Selected asset</h2>
            {selected ? (
              <>
                <p>
                  <strong>{selected.name}</strong>
                </p>
                <p className="muted">
                  {selected.manufacturer ?? "—"} {selected.model_number ?? ""}
                </p>
                <form className="stack" onSubmit={onSaveNotes}>
                  <label className="field">
                    Maintenance notes
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                    />
                  </label>
                  <div className="toolbar">
                    <button className="btn small" type="submit">
                      Save notes
                    </button>
                    <button
                      type="button"
                      className="btn secondary small"
                      onClick={() => void onArchive()}
                    >
                      Archive
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <p className="muted">Select an asset</p>
            )}
          </div>

          <div className="panel">
            <h2>Service history</h2>
            {history.length === 0 ? (
              <p className="muted">No jobs linked to this asset yet.</p>
            ) : (
              <ul className="stack">
                {history.map((h) => (
                  <li key={h.work_order_id}>
                    <div>
                      <strong>{h.title}</strong>{" "}
                      <span className="badge">{h.status}</span>
                    </div>
                    <div className="muted">
                      {h.customer_name ?? "Customer"} ·{" "}
                      {new Date(h.updated_at).toLocaleString()}
                    </div>
                    {h.completed_note ? (
                      <div className="muted">{h.completed_note}</div>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
