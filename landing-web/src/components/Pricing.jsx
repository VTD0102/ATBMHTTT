const PLANS = [
  {
    name: 'Free', price: '0', desc: 'Perfect for individuals and small teams getting started.',
    features: ['Up to 5 projects','10 team members','5 GB storage','Basic analytics','Community support'],
    cta: 'Get Started Free', outline: true,
  },
  {
    name: 'Pro', price: '12', desc: 'For growing teams that need more power and automation.',
    features: ['Unlimited projects','Unlimited members','100 GB storage','Advanced analytics & AI','200+ integrations','Priority API access','Priority support'],
    cta: 'Start Pro Trial', popular: true,
  },
  {
    name: 'Enterprise', price: null, desc: 'For large organizations with advanced security and compliance needs.',
    features: ['Everything in Pro','SSO & SAML','Custom contracts & SLA','Dedicated infrastructure','Compliance exports','24/7 dedicated support'],
    cta: 'Contact Sales', outline: true,
  },
]

export default function Pricing() {
  return (
    <section id="pricing" className="pricing-section">
      <div className="text-center">
        <span className="section-tag">Pricing</span>
        <h2 className="section-title">Simple, transparent pricing</h2>
        <p className="section-sub">Start free, scale when you're ready. No hidden fees.</p>
      </div>
      <div className="pricing-grid">
        {PLANS.map(p => (
          <div key={p.name} className={`price-card${p.popular ? ' popular' : ''}`}>
            {p.popular && <div className="popular-badge">⚡ Most Popular</div>}
            <div className="price-plan">{p.name}</div>
            <div className="price-amount">
              {p.price !== null ? <><sup>$</sup>{p.price}<span className="price-period"> / mo</span></> : <span style={{fontSize:30}}>Custom</span>}
            </div>
            <p className="price-desc">{p.desc}</p>
            <div className="price-divider" />
            <ul className="price-features">
              {p.features.map(f => <li key={f}>{f}</li>)}
            </ul>
            <a
              href="#download"
              className={`btn price-btn ${p.popular ? 'btn-primary' : 'btn-outline'}`}
            >{p.cta}</a>
          </div>
        ))}
      </div>
    </section>
  )
}
