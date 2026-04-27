const STATS = [['50K+','Teams worldwide'],['1M+','Tasks completed daily'],['4.9★','Average rating'],['99.9%','Uptime SLA']]
export default function Stats() {
  return (
    <section className="stats-section">
      <div className="stats-grid">
        {STATS.map(([n,l]) => (
          <div key={l}>
            <div className="stat-num">{n}</div>
            <div className="stat-lbl">{l}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
