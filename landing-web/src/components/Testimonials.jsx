const TESTIS = [
  { stars: 5, text: '"We cut our sprint planning meetings from 3 hours to 20 minutes. The AI task decomposition is genuinely magic — it knows our codebase better than some engineers."', name: 'Alex Kim', role: 'VP Engineering · Stripe', initials: 'AK', grad: 'linear-gradient(135deg,#6366f1,#8b5cf6)' },
  { stars: 5, text: '"Every tool we tried before felt like software from 2015. ProManager actually thinks ahead — it predicted a delivery risk two weeks before our team noticed it."', name: 'Sara Mendez', role: 'Head of Product · Vercel', initials: 'SM', grad: 'linear-gradient(135deg,#06b6d4,#6366f1)' },
  { stars: 5, text: '"I manage 14 people across 3 time zones. The real-time sync and async digest feature means nobody falls behind — and my 1:1s are actually useful now."', name: 'James Liu', role: 'Engineering Manager · Figma', initials: 'JL', grad: 'linear-gradient(135deg,#10b981,#06b6d4)' },
]

export default function Testimonials() {
  return (
    <section id="reviews" className="testi-section">
      <div className="text-center">
        <span className="section-tag">Reviews</span>
        <h2 className="section-title">Loved by 50,000+ teams</h2>
        <p className="section-sub">Don't take our word for it — here's what teams like yours are saying.</p>
      </div>
      <div className="testi-grid">
        {TESTIS.map(t => (
          <div key={t.name} className="testi-card">
            <div className="testi-stars">{'★'.repeat(t.stars)}</div>
            <p className="testi-text">{t.text}</p>
            <div className="testi-author">
              <div className="testi-avatar" style={{ background: t.grad }}>{t.initials}</div>
              <div>
                <div className="testi-name">{t.name}</div>
                <div className="testi-role">{t.role}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
