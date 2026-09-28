export type Intent = 'inv_mgmt_agent' | 'item_transfer_agent' | 'vendor_agent'

export interface ChatResponse {
  session_id: string
  intent: Intent
  message: string
}

// In dev, Vite proxies /chat to the local API. In production (e.g. served from S3),
// set VITE_API_URL to the deployed Lambda function URL at build time.
const API_BASE = import.meta.env.VITE_API_URL ?? ''

export async function sendMessage(sessionId: string, text: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, text }),
  })
  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`)
  }
  return res.json()
}
