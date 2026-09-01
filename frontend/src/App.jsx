/**
 * App.jsx - The Main Component of AgriConnect
 *
 * This is the PARENT component that holds all other components.
 * It:
 * 1. Sets up routing (which page shows for which URL)
 * 2. Manages global state (like user authentication)
 * 3. Renders the current page based on the URL
 */

// ============================================================================
// IMPORTS
// ============================================================================

// React is needed for JSX
import React from 'react';

// BrowserRouter: Provides routing functionality
// Routes: Container for all route definitions
// Route: Defines a single route (URL → Component mapping)
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Pages: Each page is a separate component
// Landing: The homepage
import Landing from './pages/Landing';

// ============================================================================
// THE APP COMPONENT
// ============================================================================

/**
 * App Component
 *
 * This is the root component. Every other component is nested inside this one.
 *
 * When the user visits a URL:
 * - / (root) → Shows Landing page
 * - More routes will be added later (/login, /register, /dashboard)
 */
function App() {
  // The return statement contains JSX - HTML-like syntax in JavaScript
  return (
    // BrowserRouter: Enables routing throughout the app
    // All routing must be inside this component
    <BrowserRouter>
      {/* Routes: Wraps all Route definitions */}
      <Routes>
        {/*
          Route: Maps a URL path to a component
          path="/" → When user visits the root URL (http://localhost:5173/)
          element={<Landing />} → Render the Landing component
        */}
        <Route path="/" element={<Landing />} />

        {/*
          We'll add more routes later:
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
        */}
      </Routes>
    </BrowserRouter>
  );
}

// Export the App component so main.jsx can import it
export default App;