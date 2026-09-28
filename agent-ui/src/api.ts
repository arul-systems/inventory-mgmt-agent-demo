export type Intent = 'inv_mgmt_agent' | 'item_transfer_agent' | 'vendor_agent'

export interface ChatResponse {
  session_id: string
  intent: Intent
  message: string
}

export async function sendMessage(sessionId: string, text: string): Promise<ChatResponse> {
  const res = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, text }),
  })
  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`)
  }
  return res.json()
}
