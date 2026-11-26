import { ComingSoon } from "@/components/ComingSoon";

export default function ReportsPage() {
  return (
    <>
      <h1 className="page-title">Reports</h1>
      <p className="page-sub">Job status, labor/parts, and printable service reports.</p>
      <ComingSoon
        title="Service reports"
        description="Reporting and browser-print service reports are Coming Soon."
      />
    </>
  );
}
