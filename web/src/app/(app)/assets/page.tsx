"use client";

import { useEffect, useState } from "react";

import { apiGet, type Asset, type Page } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const token = getToken();
      if (!token) return;
      try {
        const page = await apiGet<Page<Asset>>("/assets?page_size=100", token);
        setAssets(page.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load assets");
      }
    }
    void load();
  }, []);

  return (
    <>
      <h1 className="page-title">Assets</h1>
      <p className="page-sub">
        Equipment register (read-only in M3). Use AI Assist → Service Memory to search
        recurring failures by asset.
      </p>
      {error ? <div className="error">{error}</div> : null}
      <div className="panel table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Serial</th>
              <th>Maintenance notes</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((a) => (
              <tr key={a.id}>
                <td>{a.name}</td>
                <td>{a.asset_type ?? "—"}</td>
                <td>{a.serial_number ?? "—"}</td>
                <td>{a.maintenance_notes ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
