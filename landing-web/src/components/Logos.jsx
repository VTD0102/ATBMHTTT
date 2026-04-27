const LOGOS = ['Shopify','Stripe','Vercel','Figma','Linear','Loom','Retool']
export default function Logos() {
  return (
    <div className="logos-section">
      <p className="logos-label">Trusted by teams at</p>
      <div className="logos-row">
        {LOGOS.map(l => <span key={l} className="logo-item">{l}</span>)}
      </div>
    </div>
  )
}
