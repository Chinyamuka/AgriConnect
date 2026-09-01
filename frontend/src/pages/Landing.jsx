/**
 * Landing.jsx - The Homepage of AgriConnect
 * 
 * This is the first page users see when they visit the website.
 * 
 * What it includes:
 * 1. Navigation bar (logo, Sign In, Get Started)
 * 2. Hero section (headline, description, CTA buttons, stats)
 * 3. Features section (3 features: SMS-First, Escrow, Languages)
 * 4. How It Works section (3 steps)
 * 5. Footer (links, copyright)
 */

// ============================================================================
// IMPORTS
// ============================================================================

// React is required for JSX
import React from 'react';

// Link: React Router component for navigation
// Unlike <a href="...">, Link prevents page refresh
// It changes the URL and renders the new component without reloading
import { Link } from 'react-router-dom';

// ============================================================================
// LANDING COMPONENT
// ============================================================================

/**
 * Landing Component
 * 
 * This is a functional component.
 * It returns JSX that describes what the user sees.
 * 
 * Key concepts:
 * - className: Tailwind classes for styling
 * - style={{ color: '#14532d' }}: Inline styles (for single properties)
 * - { }: JavaScript expressions inside JSX
 * - <Link to="/login">: Navigation without page reload
 */
const Landing = () => {
  return (
    <div>
      {/* ================================================================
           NAVIGATION
           ================================================================ */}
      {/* 
        Navigation bar (navbar):
        - sticky top-0: Sticks to the top when scrolling
        - z-50: Stays on top of other elements
        - bg-white: White background
        - shadow-sm: Subtle shadow for depth
      */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            
            {/* 
              Logo:
              - Link to="/": Clicking logo goes to homepage
              - text-2xl font-bold: Large, bold text
              - style={{ color: '#14532d' }}: Brand green color
            */}
            <Link to="/" className="text-2xl font-bold"
                  style={{ color: '#010a05' }}>
              AgriConnect
            </Link>
            
            {/* 
              Navigation links:
              - flex: Horizontal layout
              - items-center: Vertically centered
              - gap-4: Space between items
            */}
            <div className="flex items-center gap-4">
              
              {/* 
                Sign In link:
                - text-gray-600: Default text color
                - hover:text-gray-900: Darkens on hover
                - transition: Smooth color change
              */}
              <Link to="/login" className="text-gray-600 hover:text-gray-900 transition">
                Sign In
              </Link>
              
              {/* 
                Get Started button:
                - className="btn-primary": Uses the custom button style
                - This is the primary call-to-action (CTA)
              */}
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* ================================================================
           HERO SECTION
           ================================================================ */}
      {/* 
        Hero section:
        - gradient-hero: Green-brown gradient background
        - minHeight: '80vh': Takes 80% of viewport height
        - display: 'flex', alignItems: 'center': Vertically centers content
        - padding: '80px 0': Spacing on top and bottom
      */}
      <section className="gradient-hero" style={{ 
        minHeight: '80vh', 
        display: 'flex', 
        alignItems: 'center', 
        padding: '80px 0' 
      }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* 
            Grid layout:
            - grid md:grid-cols-2: 2 columns on medium screens, 1 on mobile
            - gap-12: Space between columns
            - items-center: Vertically centers content
          */}
          <div className="grid md:grid-cols-2 gap-12 items-center">
            
            {/* ======= LEFT COLUMN: TEXT CONTENT ======= */}
            <div className="text-white">
              
              {/* 
                Headline:
                - text-4xl md:text-5xl: Large on mobile, larger on desktop
                - font-bold: Bold weight
                - leading-tight: Tight line height for headlines
              */}
              <h1 className="text-4xl md:text-5xl font-bold leading-tight">
                Connecting Zambian Farmers
                <br />
                <span style={{ color: '#4be507' }}>Directly to the Market</span>
              </h1>
              
              {/* 
                Description:
                - text-lg: Larger than normal text
                - mt-4: Margin top
                - opacity-90: Slightly transparent (softer)
                - max-w-lg: Limits width for readability
              */}
              <p className="text-lg mt-4 opacity-90 max-w-lg">
                AgriConnect is a digital marketplace that connects smallholder farmers
                directly with buyers. No middlemen. Fair prices. Secure transactions.
              </p>
              
              {/* 
                Call-to-Action Buttons:
                - flex flex-wrap: Horizontal layout, wraps on small screens
                - gap-4: Space between buttons
                - mt-8: Margin top
              */}
              <div className="mt-8 flex flex-wrap gap-4">
                <Link to="/register" className="btn-primary" style={{ background: 'rgba(255,255,255,0.2)' }}>
                  Get Started Free
                </Link>
                <Link to="#how-it-works" className="btn-outline">
                  Learn More
                </Link>
              </div>
              
              {/* 
                Stats:
                - mt-12: Margin top
                - flex flex-wrap: Horizontal layout, wraps on small screens
                - gap-8: Space between stats
              */}
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

            {/* ======= RIGHT COLUMN: GLASS CARD ======= */}
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

      {/* ================================================================
           FEATURES SECTION
           ================================================================ */}
      {/* 
        Features section:
        - py-16: Padding top and bottom
        - bg-white: White background (contrasts with hero gradient)
      */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Section header */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold" style={{ color: '#14532d' }}>
              Why Choose AgriConnect
            </h2>
            <p className="text-gray-600 mt-2">Built for Zambian farmers and buyers</p>
          </div>
          
          {/* 
            3-column grid:
            - grid md:grid-cols-3: 3 columns on desktop, 1 on mobile
            - gap-8: Space between cards
          */}
          <div className="grid md:grid-cols-3 gap-8">
            
            {/* Feature 1: SMS-First */}
            <div className="text-center p-6 border rounded-xl hover:shadow-lg transition">
              <div className="text-4xl mb-4" style={{ color: '#15803d' }}>📱</div>
              <h5 className="font-bold">SMS-First Platform</h5>
              <p className="text-gray-600 text-sm mt-2">
                Works on any phone. No internet or smartphone required.
              </p>
            </div>
            
            {/* Feature 2: Secure Escrow */}
            <div className="text-center p-6 border rounded-xl hover:shadow-lg transition">
              <div className="text-4xl mb-4" style={{ color: '#15803d' }}>🔒</div>
              <h5 className="font-bold">Secure Escrow Payments</h5>
              <p className="text-gray-600 text-sm mt-2">
                Funds are held securely until delivery is confirmed.
              </p>
            </div>
            
            {/* Feature 3: Local Languages */}
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

      {/* ================================================================
           HOW IT WORKS SECTION
           ================================================================ */}
      {/* 
        How It Works section:
        - backgroundColor: '#f8f9fa': Light gray (subtle contrast from white)
      */}
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

      {/* ================================================================
           FOOTER
           ================================================================ */}
      {/* 
        Footer:
        - backgroundColor: '#0a2e1a': Dark green
        - color: 'rgba(255,255,255,0.7)': White with opacity
        - py-12: Padding top and bottom
      */}
      <footer className="py-12" style={{ backgroundColor: '#0a2e1a', color: 'rgba(255,255,255,0.7)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            
            {/* Column 1: Brand */}
            <div>
              <h5 className="font-bold text-white">AgriConnect</h5>
              <p className="text-sm mt-2">
                Zambia's SMS-First Farmer-to-Buyer Marketplace.
              </p>
            </div>
            
            {/* Column 2: Platform */}
            <div>
              <h6 className="font-bold text-white">Platform</h6>
              <ul className="text-sm space-y-1 mt-2">
                <li><a href="#" className="hover:text-white transition">How It Works</a></li>
                <li><a href="#" className="hover:text-white transition">For Farmers</a></li>
                <li><a href="#" className="hover:text-white transition">For Buyers</a></li>
              </ul>
            </div>
            
            {/* Column 3: Company */}
            <div>
              <h6 className="font-bold text-white">Company</h6>
              <ul className="text-sm space-y-1 mt-2">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            
            {/* Column 4: Legal */}
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

// Export the component so App.jsx can import it
export default Landing;
