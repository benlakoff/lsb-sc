export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).end();
  const { email, ts } = req.body || {};
  console.log(`[gate] ${ts || new Date().toISOString()} — ${email}`);
  res.status(200).json({ ok: true });
}
