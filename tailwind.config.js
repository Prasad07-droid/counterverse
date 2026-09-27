/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cv: {
          bg: '#000000',
          surface: {
            1: '#070707',
            2: '#0b0b0b',
            3: '#101010',
            4: '#151515',
            elevated: '#111a2e',
          },
          border: {
            DEFAULT: '#222222',
            subtle: '#181818',
            hover: '#3a3a3a',
            strong: '#555555',
          },
          text: {
            white: '#f7f7f7',
            secondary: '#a5a5a5',
            muted: '#666666',
          },
          cyan: '#00c8ff',
          blue: '#1787ff',
          green: '#00df8f',
          amber: '#f5a623',
          red: '#ee0000',
        }
      },
      fontFamily: {
        sans: ['Geist', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '8px',
        md: '8px',
        lg: '10px',
      }
    },
  },
  plugins: [],
}
