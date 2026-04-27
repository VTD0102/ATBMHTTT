export default function Navbar() {
  return (
    <nav className="navbar">
      <a className="nav-logo" href="#">
        <span className="nav-logo-icon">📋</span>
        ProManager Suite
      </a>
      <ul className="nav-links">
        <li><a href="#features">Features</a></li>
        <li><a href="#pricing">Pricing</a></li>
        <li><a href="#reviews">Reviews</a></li>
        <li><a href="#faq">FAQ</a></li>
      </ul>
      <div className="nav-cta">
        <a href="#" className="btn btn-ghost">Sign in</a>
        <a href="#download" className="btn btn-primary">Download Free</a>
      </div>
    </nav>
  )
}
