import { ComingSoon } from "@/components/ComingSoon";

export default function DashboardPage() {
  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-sub">
        Jobs today, unassigned/overdue, and completion rate will land here.
      </p>
      <ComingSoon
        title="Dispatcher dashboard"
        description="Skeleton only. Metrics and dispatch shortcuts are not wired yet."
      />
    </>
  );
}
