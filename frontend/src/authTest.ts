const BASE_URL = "http://127.0.0.1:8000"; // change if needed

let accessToken: string | null = null;

interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ========== REGISTER ==========
export async function registerUser(user: RegisterPayload) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user),
  });

  if (!res.ok) {
    throw new Error(`Register failed: ${await res.text()}`);
  }

  return res.json();
}

// ========== LOGIN ==========
export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Login failed: ${await res.text()}`);
  }

  const data = (await res.json()) as TokenResponse;
  accessToken = data.access_token;
  return data;
}

// ========== GET CURRENT USER ==========
export async function getCurrentUser() {
  if (!accessToken) {
    throw new Error("You must login first");
  }

  const res = await fetch(`${BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch user: ${await res.text()}`);
  }

  return res.json();
}

// ========== CALL PROTECTED ROUTE ==========
export async function callProtected() {
  if (!accessToken) {
    throw new Error("You must login first");
  }

  const res = await fetch(`${BASE_URL}/protected`, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!res.ok) {
    throw new Error(`Protected route failed: ${await res.text()}`);
  }

  return res.json();
}

// ========== Example usage (optional) ==========
async function testFlow() {
  try {
    console.log("Registering user...");
    await registerUser({
      email: "test@example.com",
      full_name: "Test User",
      password: "password123",
    });

    console.log("Logging in...");
    const tokens = await login("test@example.com", "password123");
    console.log("Tokens:", tokens);

    console.log("Getting current user...");
    const me = await getCurrentUser();
    console.log("User:", me);

    console.log("Calling protected route...");
    const protectedData = await callProtected();
    console.log("Protected:", protectedData);
  } catch (err) {
    console.error("Error:", err);
  }
}

// Uncomment if you want automatic testing on page load
// testFlow();
