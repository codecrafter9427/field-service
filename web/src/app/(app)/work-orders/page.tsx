import { ComingSoon } from "@/components/ComingSoon";

export default function WorkOrdersPage() {
  return (
    <>
      <h1 className="page-title">Work Orders</h1>
      <p className="page-sub">Create, assign, and track field jobs.</p>
      <ComingSoon
        title="Work orders"
        description="Work order lifecycle, checklists, parts, and labor are Coming Soon."
      />
    </>
  );
}
