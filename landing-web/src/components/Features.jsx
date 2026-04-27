const FEATURES = [
  { icon: '🤖', bg: '#ede9fe', title: 'AI Task Assistant', desc: 'Describe a goal in plain English — AI breaks it into tasks, assigns owners, and sets realistic deadlines automatically.' },
  { icon: '📊', bg: '#dcfce7', title: 'Smart Analytics', desc: 'Real-time dashboards and burn-down charts give instant visibility into project health, team velocity, and blockers.' },
  { icon: '⚡', bg: '#dbeafe', title: 'Automation Engine', desc: 'Build powerful no-code automations. When a task moves to Done, auto-notify clients, update Slack, and log to your CRM.' },
  { icon: '🔗', bg: '#fef9c3', title: '200+ Integrations', desc: 'Connect with Slack, GitHub, Figma, Jira, Google Workspace, Zapier and more — all in one central command center.' },
  { icon: '🔒', bg: '#fee2e2', title: 'Enterprise Security', desc: 'SOC 2 Type II certified. End-to-end encryption, SSO, custom permissions, and full audit logs for every action.' },
  { icon: '📱', bg: '#e0f2fe', title: 'Cross-Platform', desc: 'Native apps for Web, macOS, Windows, iOS, and Android. Work from anywhere with offline sync and instant updates.' },
]

export default function Features() {
  return (
    <section id="features" className="features-section">
      <div className="text-center">
        <span className="section-tag">Features</span>
        <h2 className="section-title">Everything you need to move faster</h2>
        <p className="section-sub">AI-powered tools that eliminate busywork and keep your team in flow.</p>
      </div>
      <div className="features-grid">
        {FEATURES.map(f => (
          <div key={f.title} className="feat-card">
            <div className="feat-icon" style={{ background: f.bg }}>{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
