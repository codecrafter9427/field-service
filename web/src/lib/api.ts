const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8003/api/v1";

export type DemoLoginResult = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    role: string;
    organization_id: string;
    display_name: string;
  };
};

export async function demoLogin(
  email: string,
  password: string
): Promise<DemoLoginResult> {
  const res = await fetch(`${API_BASE}/auth/demo-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    let message = "Login failed";
    try {
      const data = await res.json();
      message = data?.detail?.error?.message ?? data?.error?.message ?? message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json();
}
