export default function Download() {
  return (
    <section id="download" className="download-section">
      <div className="download-box">
        <div className="dl-icon">⬇️</div>
        <h3 className="dl-title">Download ProManager Suite</h3>
        <p className="dl-sub">
          Free to download. Activate instantly with the API key
          sent to your email after registration.
        </p>
        <a
          href="/ProManagerSuite.exe"
          download="ProManagerSuite.exe"
          className="btn btn-primary btn-lg"
          style={{ width: '100%', justifyContent: 'center', marginBottom: 10 }}
        >
          ⬇ &nbsp;Download ProManagerSuite.exe
        </a>
        <p className="dl-note">Version 3.2.1 &nbsp;·&nbsp; 14 MB &nbsp;·&nbsp; Linux x86-64</p>
        <div className="dl-email-hint">
          📧 &nbsp;Your API key will be sent to your registered email
        </div>
        <div className="demo-banner">⚠ DEMO ONLY — Academic / Educational Environment</div>
      </div>
    </section>
  )
}
