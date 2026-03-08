/** @type {import('tailwindcss').Config} */
export default {
  // Scan all JSX files for class names so unused styles are purged in production
  content: [
    './index.html',
    './src/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      // PropPulse brand colours — extend as needed
      colors: {
        brand: {
          blue: '#2563eb',
          navy: '#1e3a5f',
          light: '#eff6ff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
