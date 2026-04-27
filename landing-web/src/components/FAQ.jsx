import { useState } from 'react'

const FAQS = [
  { q: 'Is ProManager Suite really free?', a: 'Yes. The Free plan is free forever — no trial period, no credit card required. You get unlimited access to core features immediately upon download and activation.' },
  { q: 'How does the API key activation work?', a: 'Download the app, then activate it with the API key sent to your email. The app connects to our license server to validate and configure your workspace — usually takes under 10 seconds.' },
  { q: 'What AI models power ProManager Suite?', a: 'We use GPT-4o for task decomposition and deadline prediction, and a proprietary fine-tuned model for project risk analysis trained on over 10 million anonymized project datasets.' },
  { q: 'Is my project data secure?', a: 'Absolutely. We are SOC 2 Type II certified. All data is encrypted at rest (AES-256) and in transit (TLS 1.3). We never sell or share your data with third parties.' },
  { q: 'Can I migrate from Asana, Jira, or Notion?', a: 'Yes — one-click import from Asana, Jira, Trello, Monday, Notion, and Basecamp. Our migration wizard completes in under 5 minutes with zero data loss.' },
]

export default function FAQ() {
  const [open, setOpen] = useState(null)
  return (
    <section id="faq" className="faq-section">
      <div className="text-center">
        <span className="section-tag">FAQ</span>
        <h2 className="section-title">Common questions</h2>
        <p className="section-sub" style={{ marginBottom: 40 }}>Everything you need to know before getting started.</p>
      </div>
      <div className="faq-list">
        {FAQS.map((f, i) => (
          <div key={i} className="faq-item">
            <div className="faq-q" onClick={() => setOpen(open === i ? null : i)}>
              {f.q}
              <span className={`faq-arrow${open === i ? ' open' : ''}`}>＋</span>
            </div>
            <div className={`faq-a${open === i ? ' open' : ''}`}>{f.a}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
