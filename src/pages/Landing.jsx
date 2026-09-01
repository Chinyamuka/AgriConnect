import React from 'react';
import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div>
      {/* ===== NAVIGATION ===== */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="text-2xl font-bold" style={{ color: '#14532d' }}>
              AgriConnect
            </Link>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-gray-600 hover:text-gray-900 transition">
                Sign In
              </Link>
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section className="gradient-hero" style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', padding: '80px 0' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div className="text-white">
              <h1 className="text-4xl md:text-5xl font-bold leading-tight">
                Connecting Zambian Farmers
                <br />
                <span style={{ color: '#86efac' }}>Directly to the Market</span>
              </h1>
              <p className="text-lg mt-4 opacity-90 max-w-lg">
                AgriConnect is a digital marketplace that connects smallholder farmers
                directly with buyers. No middlemen. Fair prices. Secure transactions.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <Link to="/register" className="btn-primary" style={{ background: 'rgba(255,255,255,0.2)' }}>
                  Get Started Free
                </Link>
                <Link to="#how-it-works" className="btn-outline">
                  Learn More
                </Link>
              </div>
              {/* Stats */}
              <div className="mt-12 flex flex-wrap gap-8">
                <div>
                  <div className="text-3xl font-bold text-white">1,200+</div>
                  <div className="text-sm opacity-75">Registered Farmers</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-white">K 4.2M</div>
                  <div className="text-sm opacity-75">Total Trade Value</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-white">98%</div>
                  <div className="text-sm opacity-75">Satisfaction Rate</div>
                </div>
              </div>
            </div>

            {/* Right: Glass Card */}
            <div className="glass-card p-8 text-center">
              <h3 className="text-xl font-bold text-gray-900">Ready to Trade?</h3>
              <p className="text-gray-600 text-sm mt-2">
                Join thousands of farmers and buyers already using AgriConnect.
              </p>
              <Link to="/register" className="btn-primary w-full mt-4 text-center">
                Create Free Account
              </Link>
              <p className="text-gray-500 text-sm mt-3">
                Already have an account?{' '}
                <Link to="/login" className="font-bold" style={{ color: '#15803d' }}>
                  Sign In
                </Link>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold" style={{ color: '#14532d' }}>
              Why Choose AgriConnect
            </h2>
            <p className="text-gray-600 mt-2">Built for Zambian farmers and buyers</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="text-center p-6 border rounded-xl hover:shadow-lg transition">
              <div className="text-4xl mb-4" style={{ color: '#15803d' }}>📱</div>
              <h5 className="font-bold">SMS-First Platform</h5>
              <p className="text-gray-600 text-sm mt-2">
                Works on any phone. No internet or smartphone required.
              </p>
            </div>
            {/* Feature 2 */}
            <div className="text-center p-6 border rounded-xl hover:shadow-lg transition">
              <div className="text-4xl mb-4" style={{ color: '#15803d' }}>🔒</div>
              <h5 className="font-bold">Secure Escrow Payments</h5>
              <p className="text-gray-600 text-sm mt-2">
                Funds are held securely until delivery is confirmed.
              </p>
            </div>
            {/* Feature 3 */}
            <div className="text-center p-6 border rounded-xl hover:shadow-lg transition">
              <div className="text-4xl mb-4" style={{ color: '#15803d' }}>🌍</div>
              <h5 className="font-bold">Local Language Support</h5>
              <p className="text-gray-600 text-sm mt-2">
                Available in English, Nyanja, Bemba, Tonga, and Lozi.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section id="how-it-works" className="py-16" style={{ backgroundColor: '#f8f9fa' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold" style={{ color: '#14532d' }}>
              How It Works
            </h2>
            <p className="text-gray-600 mt-2">Three simple steps to start trading</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div className="text-center">
              <div className="text-6xl font-bold" style={{ color: '#15803d', opacity: 0.2 }}>1</div>
              <h5 className="font-bold mt-2">Register Your Account</h5>
              <p className="text-gray-600 text-sm mt-2">
                Sign up with your phone number and create your profile.
              </p>
            </div>
            {/* Step 2 */}
            <div className="text-center">
              <div className="text-6xl font-bold" style={{ color: '#15803d', opacity: 0.2 }}>2</div>
              <h5 className="font-bold mt-2">List or Discover Produce</h5>
              <p className="text-gray-600 text-sm mt-2">
                Farmers list produce. Buyers browse and place bids.
              </p>
            </div>
            {/* Step 3 */}
            <div className="text-center">
              <div className="text-6xl font-bold" style={{ color: '#15803d', opacity: 0.2 }}>3</div>
              <h5 className="font-bold mt-2">Trade and Get Paid</h5>
              <p className="text-gray-600 text-sm mt-2">
                Accept bids, confirm delivery, get paid securely.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="py-12" style={{ backgroundColor: '#0a2e1a', color: 'rgba(255,255,255,0.7)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h5 className="font-bold text-white">AgriConnect</h5>
              <p className="text-sm mt-2">
                Zambia's SMS-First Farmer-to-Buyer Marketplace.
              </p>
            </div>
            <div>
              <h6 className="font-bold text-white">Platform</h6>
              <ul className="text-sm space-y-1 mt-2">
                <li><a href="#" className="hover:text-white transition">How It Works</a></li>
                <li><a href="#" className="hover:text-white transition">For Farmers</a></li>
                <li><a href="#" className="hover:text-white transition">For Buyers</a></li>
              </ul>
            </div>
            <div>
              <h6 className="font-bold text-white">Company</h6>
              <ul className="text-sm space-y-1 mt-2">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h6 className="font-bold text-white">Legal</h6>
              <ul className="text-sm space-y-1 mt-2">
                <li><a href="#" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <hr className="my-6 border-white/10" />
          <div className="text-center text-sm">
            &copy; 2026 AgriConnect. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
