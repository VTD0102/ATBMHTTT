const DB_PROJECTS = [
  { name: 'Q4 Marketing Campaign', status: 'Active', statusBg: '#dcfce7', statusFg: '#166534', prog: 72 },
  { name: 'Product Launch 2025',   status: 'In Progress', statusBg: '#fef9c3', statusFg: '#854d0e', prog: 45 },
  { name: 'Client Onboarding',     status: 'Active', statusBg: '#dcfce7', statusFg: '#166534', prog: 88 },
  { name: 'Brand Redesign',        status: 'Planning', statusBg: '#ede9fe', statusFg: '#5b21b6', prog: 15 },
]
const DB_TASKS = [
  { name: 'Review campaign brief',    due: 'Today',     dueFg: '#dc2626' },
  { name: 'Send weekly report',       due: 'Tomorrow',  dueFg: '#64748b' },
  { name: 'Update onboarding docs',   due: 'Apr 29',    dueFg: '#64748b' },
  { name: 'Prepare launch checklist', due: 'Apr 30',    dueFg: '#64748b' },
  { name: 'Design review meeting',    due: 'May 1',     dueFg: '#64748b' },
]

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-badge">
        <span className="hero-badge-dot" />
        New: GPT-4o Integration is live
      </div>
      <h1>
        The AI-Powered Project Manager<br />
        <span className="gradient-text">Your Team Deserves</span>
      </h1>
      <p className="hero-sub">
        Automate workflows, predict deadlines, and collaborate in real-time —
        all in one intelligent workspace trusted by 50,000+ teams.
      </p>
      <div className="hero-btns">
        <a href="#download" className="btn btn-primary btn-lg">🚀&nbsp; Download Free</a>
        <a href="#features" className="btn btn-outline btn-lg">See features →</a>
      </div>
      <div className="hero-meta">
        <span>Free forever plan</span>
        <span>Setup in 2 minutes</span>
        <span>GDPR compliant</span>
      </div>

      {/* Dashboard preview */}
      <div className="db-wrap">
        <div className="db-topbar">
          <span className="db-dot" style={{ background: '#ff5f57' }} />
          <span className="db-dot" style={{ background: '#ffbd2e' }} />
          <span className="db-dot" style={{ background: '#28c840' }} />
          <span className="db-topbar-title">ProManager Suite — Dashboard</span>
        </div>
        <div className="db-body">
          {/* Sidebar */}
          <div className="db-sidebar">
            {[['◉','Dashboard',true],['▤','Projects'],['✓','My Tasks'],['📊','Analytics'],['👥','Team'],['💬','Inbox']].map(([icon,label,active]) => (
              <div key={label} className={`db-nav-item${active?' active':''}`}><span>{icon}</span>{label}</div>
            ))}
          </div>
          {/* Main */}
          <div className="db-main">
            <div className="db-stats-row">
              {[['12','Active Projects','#6366f1'],['47','Open Tasks','#059669'],['3','Due Today','#dc2626'],['8','Team Members','#d97706']].map(([n,l,c]) => (
                <div key={l} className="db-stat">
                  <div className="db-stat-num" style={{ color: c }}>{n}</div>
                  <div className="db-stat-lbl">{l}</div>
                </div>
              ))}
            </div>
            <div className="db-cards-row">
              <div className="db-card">
                <div className="db-card-title">Recent Projects</div>
                {DB_PROJECTS.map(p => (
                  <div key={p.name}>
                    <div className="db-row">
                      <span>📁 {p.name}</span>
                      <span className="db-tag" style={{ background: p.statusBg, color: p.statusFg }}>{p.status}</span>
                    </div>
                    <div className="db-progress">
                      <div className="db-progress-fill" style={{ width: `${p.prog}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="db-card">
                <div className="db-card-title">My Tasks</div>
                {DB_TASKS.map(t => (
                  <div key={t.name} className="db-row">
                    <span>○ {t.name}</span>
                    <span style={{ marginLeft: 'auto', fontSize: 10, color: t.dueFg }}>{t.due}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
