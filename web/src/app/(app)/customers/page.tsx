"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  apiGet,
  apiSend,
  type Customer,
  type Page,
  type ServiceLocation,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [locations, setLocations] = useState<ServiceLocation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [locName, setLocName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("Springfield");

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      const page = await apiGet<Page<Customer>>("/customers?page_size=100", token);
      setCustomers(page.items);
      if (!selectedId && page.items.length) {
        setSelectedId(page.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load customers");
    }
  }, [selectedId]);

  const loadLocations = useCallback(async (customerId: string) => {
    const token = getToken();
    if (!token) return;
    try {
      const page = await apiGet<Page<ServiceLocation>>(
        `/service-locations?customer_id=${customerId}&page_size=100`,
        token
      );
      setLocations(page.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load locations");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (selectedId) void loadLocations(selectedId);
  }, [selectedId, loadLocations]);

  async function onCreateCustomer(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token) return;
    try {
      const created = await apiSend<Customer>("/customers", token, "POST", {
        name,
        email: email || null,
        phone: phone || null,
      });
      setName("");
      setEmail("");
      setPhone("");
      setSelectedId(created.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function onCreateLocation(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !selectedId) return;
    try {
      await apiSend("/service-locations", token, "POST", {
        customer_id: selectedId,
        name: locName,
        address_line1: address,
        city,
        country: "US",
      });
      setLocName("");
      setAddress("");
      await loadLocations(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Location create failed");
    }
  }

  const selected = customers.find((c) => c.id === selectedId) ?? null;

  return (
    <>
      <h1 className="page-title">Customers</h1>
      <p className="page-sub">
        Customer and service-location directory for dispatch.
      </p>
      {error ? <div className="error">{error}</div> : null}

      <div className="split">
        <div>
          <div className="panel">
            <h2>Directory</h2>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <button
                          type="button"
                          className="btn secondary small"
                          onClick={() => setSelectedId(c.id)}
                        >
                          {c.name}
                        </button>
                      </td>
                      <td>{c.email ?? "—"}</td>
                      <td>{c.phone ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel">
            <h2>Add customer</h2>
            <form className="stack" onSubmit={onCreateCustomer}>
              <label className="field">
                Name
                <input value={name} onChange={(e) => setName(e.target.value)} required />
              </label>
              <div className="grid-2">
                <label className="field">
                  Email
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
                <label className="field">
                  Phone
                  <input value={phone} onChange={(e) => setPhone(e.target.value)} />
                </label>
              </div>
              <button className="btn" type="submit">
                Create customer
              </button>
            </form>
          </div>
        </div>

        <div>
          <div className="panel">
            <h2>Service locations</h2>
            {selected ? (
              <p className="muted">For {selected.name}</p>
            ) : (
              <p className="muted">Select a customer</p>
            )}
            <ul className="stack">
              {locations.map((loc) => (
                <li key={loc.id}>
                  <strong>{loc.name}</strong>
                  <div className="muted">
                    {loc.address_line1}, {loc.city}
                    {loc.region ? `, ${loc.region}` : ""}
                  </div>
                </li>
              ))}
              {!locations.length ? <li className="muted">No locations yet.</li> : null}
            </ul>
          </div>

          <div className="panel">
            <h2>Add location</h2>
            <form className="stack" onSubmit={onCreateLocation}>
              <label className="field">
                Location name
                <input
                  value={locName}
                  onChange={(e) => setLocName(e.target.value)}
                  required
                  disabled={!selectedId}
                />
              </label>
              <label className="field">
                Address
                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  required
                  disabled={!selectedId}
                />
              </label>
              <label className="field">
                City
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  required
                  disabled={!selectedId}
                />
              </label>
              <button className="btn" type="submit" disabled={!selectedId}>
                Create location
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
