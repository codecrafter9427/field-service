"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearSession, getUser, type DemoUser } from "@/lib/auth";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/customers", label: "Customers" },
  { href: "/work-orders", label: "Work Orders" },
  { href: "/schedule", label: "Schedule" },
  { href: "/assets", label: "Assets" },
  { href: "/reports", label: "Reports" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<DemoUser | null>(null);

  useEffect(() => {
    const u = getUser();
    if (!u) {
      router.replace("/login");
      return;
    }
    setUser(u);
  }, [router]);

  function logout() {
    clearSession();
    router.replace("/login");
  }

  if (!user) {
    return <main className="main">Loading…</main>;
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">Field Service</div>
        <nav className="nav" aria-label="Primary">
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={active ? "active" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div style={{ marginTop: "auto", fontSize: "0.85rem", color: "var(--muted)" }}>
          <div>{user.display_name}</div>
          <div>{user.role}</div>
          <button
            type="button"
            className="btn"
            style={{ marginTop: "0.75rem" }}
            onClick={logout}
          >
            Sign out
          </button>
        </div>
      </aside>
      <div className="main">{children}</div>
    </div>
  );
}
