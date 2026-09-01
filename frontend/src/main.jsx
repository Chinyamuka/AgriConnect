/**
 * main.jsx - The entry point of our React application
 *
 * This is the FIRST JavaScript file that runs.
 * It:
 * 1. Imports React and ReactDOM
 * 2. Imports the App component
 * 3. Imports global styles (index.css)
 * 4. Renders the App component into the DOM
 */

// ============================================================================
// IMPORTS
// ============================================================================

// React is the core library. Without this, JSX won't work.
import React from 'react';

// ReactDOM is responsible for rendering React components in the browser.
// 'client' is the new API for React 18+.
import ReactDOM from 'react-dom/client';

// The App component is the root of our entire application.
// Every other component is nested inside App.
import App from './App.jsx';

// Global styles that apply to the entire app.
// This includes Tailwind directives and custom CSS.
import './index.css';

// ============================================================================
// RENDER THE APP
// ============================================================================

// Step 1: Find the root element in index.html
// document.getElementById('root') returns the div with id="root"
const rootElement = document.getElementById('root');

// Step 2: Create a React root
// ReactDOM.createRoot() creates a React rendering context
const root = ReactDOM.createRoot(rootElement);

// Step 3: Render the App component into the root
// root.render() tells React to render the App component
// React.StrictMode is a development tool that helps catch bugs
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);