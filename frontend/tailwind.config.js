/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Party colors
        democratic: {
          DEFAULT: '#3B82F6',
          light: '#60A5FA',
          dark: '#1D4ED8',
        },
        republican: {
          DEFAULT: '#EF4444',
          light: '#F87171',
          dark: '#B91C1C',
        },
        independent: {
          DEFAULT: '#8B5CF6',
          light: '#A78BFA',
          dark: '#6D28D9',
        },
      },
    },
  },
  plugins: [],
}
