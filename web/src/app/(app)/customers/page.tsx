import { ComingSoon } from "@/components/ComingSoon";

export default function CustomersPage() {
  return (
    <>
      <h1 className="page-title">Customers</h1>
      <p className="page-sub">Customer and service-location directory.</p>
      <ComingSoon
        title="Customers"
        description="CRUD for customers and service locations is Coming Soon."
      />
    </>
  );
}
