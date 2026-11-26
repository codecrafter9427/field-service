"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet, type Page, type ScheduleItem, type WorkOrder } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function DashboardPage() {
  const [todayCount, setTodayCount] = useState(0);
  const [unassigned, setUnassigned] = useState(0);
  const [overlaps, setOverlaps] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const token = getToken();
      if (!token) return;
      try {
        const [orders, schedule] = await Promise.all([
          apiGet<Page<WorkOrder>>("/work-orders?page_size=100", token),
          apiGet<ScheduleItem[]>("/schedule", token),
        ]);
        const start = new Date();
        start.setHours(0, 0, 0, 0);
        const end = new Date();
        end.setHours(23, 59, 59, 999);
        const today = schedule.filter((s) => {
          if (!s.scheduled_start) return false;
          const t = new Date(s.scheduled_start).getTime();
          return t >= start.getTime() && t <= end.getTime();
        });
        setTodayCount(today.length);
        setUnassigned(orders.items.filter((o) => !o.technician_id).length);
        setOverlaps(schedule.filter((s) => s.overlap_warning).length);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      }
    }
    void load();
  }, []);

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-sub">
        Dispatcher snapshot — jobs today, unassigned, and overlap warnings.
      </p>
      {error ? <div className="error">{error}</div> : null}

      <div className="grid-2">
        <div className="panel">
          <h2>Jobs today</h2>
          <p style={{ fontSize: "2rem", margin: 0 }}>{todayCount}</p>
        </div>
        <div className="panel">
          <h2>Unassigned</h2>
          <p style={{ fontSize: "2rem", margin: 0 }}>{unassigned}</p>
        </div>
        <div className="panel">
          <h2>Overlap warnings</h2>
          <p style={{ fontSize: "2rem", margin: 0 }}>{overlaps}</p>
        </div>
        <div className="panel">
          <h2>Quick links</h2>
          <div className="stack">
            <Link href="/work-orders">Create / assign work order</Link>
            <Link href="/schedule">Open schedule board</Link>
            <Link href="/ai">AI Assist / Service Memory</Link>
            <Link href="/customers">Customer directory</Link>
          </div>
        </div>
      </div>
    </>
  );
}
