/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#f2f8f5',
          100: '#e1f0e8',
          200: '#c4dfd1',
          300: '#9bc4af',
          400: '#6ea389',
          500: '#4c8669',
          600: '#386a51',
          700: '#2d5542',
          800: '#145338',
          900: '#204033',
          950: '#000402',
        },
        surface: {
          50: '#F7F9FC',
          100: '#F0F3F7',
          200: '#97A09B',
          300: '#6A6E6C',
        }
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        'float': '0 10px 40px -10px rgba(0, 0, 0, 0.08)',
      }
    },
  },
  plugins: [],
}
