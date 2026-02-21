/**
 * API helpers — all requests go through the Vite dev proxy (/api → localhost:8000).
 */

// ── Auth ─────────────────────────────────────────────────────

export async function loginUser(email, password) {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function registerUser(name, email, password) {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed');
  }
  return res.json();
}

export async function getMe(userId) {
  const res = await fetch(`/api/auth/me/${userId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch user');
  }
  return res.json();
}

export async function submitOnboarding(userId, patientData) {
  const res = await fetch(`/api/auth/onboarding/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patientData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Onboarding failed');
  }
  return res.json();
}

// ── Bill Verification ────────────────────────────────────────

const BILLS_BASE = '/api/bills';

export async function uploadBill(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BILLS_BASE}/upload`, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function getBillStatus(billUuid) {
  const res = await fetch(`${BILLS_BASE}/status/${billUuid}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Status check failed (${res.status})`);
  }
  return res.json();
}

export async function getBillReport(billUuid) {
  const res = await fetch(`${BILLS_BASE}/report/${billUuid}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Report fetch failed (${res.status})`);
  }
  return res.json();
}
