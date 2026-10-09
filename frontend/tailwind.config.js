/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#2563EB',
          light: '#E8F3FF',
          ultralight: '#F0F7FF',
          bg: '#F7FAFC',
          card: '#FFFFFF',
          text: '#172033',
          secondary: '#64748B',
          border: '#E2E8F0',
          success: '#16A34A',
          warning: '#F59E0B',
          danger: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'card-hover': '0 10px 15px -3px rgba(37, 99, 235, 0.08), 0 4px 6px -2px rgba(37, 99, 235, 0.05)',
      }
    },
  },
  plugins: [],
}
