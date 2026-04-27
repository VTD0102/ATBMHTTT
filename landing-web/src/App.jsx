import './App.css'
import Navbar       from './components/Navbar'
import Hero         from './components/Hero'
import Logos        from './components/Logos'
import Features     from './components/Features'
import Stats        from './components/Stats'
import Pricing      from './components/Pricing'
import Testimonials from './components/Testimonials'
import Download     from './components/Download'
import FAQ          from './components/FAQ'
import CTABanner    from './components/CTABanner'
import Footer       from './components/Footer'

export default function App() {
  return (
    <>
      <Navbar />
      <Hero />
      <Logos />
      <Features />
      <Stats />
      <Pricing />
      <Testimonials />
      <Download />
      <FAQ />
      <CTABanner />
      <Footer />
    </>
  )
}
