export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div>
          <div className="footer-logo">📋 ProManager Suite</div>
          <p className="footer-brand-text">AI-powered project management for modern teams. Ship faster. Stress less.</p>
        </div>
        {[
          ['Product', ['Features','Pricing','Changelog','Roadmap','API Docs']],
          ['Company', ['About','Blog','Careers','Press','Contact']],
          ['Legal',   ['Privacy Policy','Terms of Service','Cookie Policy','Security']],
        ].map(([title, links]) => (
          <div key={title} className="footer-col">
            <h4>{title}</h4>
            <ul>{links.map(l => <li key={l}><a href="#">{l}</a></li>)}</ul>
          </div>
        ))}
      </div>
      <div className="footer-bottom">
        <span>© 2024 ProManager Suite, Inc. All rights reserved.</span>
        <div className="footer-links">
          <a href="#">Twitter</a>
          <a href="#">LinkedIn</a>
          <a href="#">GitHub</a>
        </div>
        <span className="demo-note">⚠ DEMO ONLY — Academic Project</span>
      </div>
    </footer>
  )
}
