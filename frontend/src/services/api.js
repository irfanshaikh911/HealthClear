/**
 * Bill Verification API helpers.
 *
 * All requests go through the Vite dev proxy (/api → localhost:8000).
 */

const API_BASE = '/api/bills';

/**
 * Upload a bill file for verification.
 * @param {File} file - The bill file (PDF/JPG/PNG)
 * @returns {Promise<{bill_uuid: string, message: string, status: string}>}
 */
export async function uploadBill(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }

  return res.json();
}

/**
 * Poll the processing status of a bill.
 * @param {string} billUuid
 * @returns {Promise<{bill_uuid: string, status: string}>}
 */
export async function getBillStatus(billUuid) {
  const res = await fetch(`${API_BASE}/status/${billUuid}`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Status check failed (${res.status})`);
  }

  return res.json();
}

/**
 * Get the full verification report for a completed bill.
 * @param {string} billUuid
 * @returns {Promise<Object>} VerificationReportOut
 */
export async function getBillReport(billUuid) {
  const res = await fetch(`${API_BASE}/report/${billUuid}`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Report fetch failed (${res.status})`);
  }

  return res.json();
}
