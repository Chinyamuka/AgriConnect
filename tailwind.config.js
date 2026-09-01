/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        agri: {
          green: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
            950: '#0a2e1a',
          },
          brown: {
            50: '#f8f3e9',
            100: '#f0e6d5',
            200: '#e0cdb0',
            300: '#d4a373',
            400: '#c48b5a',
            500: '#b07d4b',
            600: '#9a6a3d',
            700: '#7f4f24',
            800: '#6b3f1d',
            900: '#5a3316',
          },
        },
      },
    },
  },
  plugins: [],
}
