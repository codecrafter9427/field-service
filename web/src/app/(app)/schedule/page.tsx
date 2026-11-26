import { ComingSoon } from "@/components/ComingSoon";

export default function SchedulePage() {
  return (
    <>
      <h1 className="page-title">Schedule</h1>
      <p className="page-sub">Calendar and dispatch board.</p>
      <ComingSoon
        title="Schedule / dispatch"
        description="Assignment board and overlap warnings are Coming Soon — not implemented in this scaffold."
      />
    </>
  );
}
