/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#0a1120",
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
        },
        brand: {
          50: "#eef4ff",
          100: "#d9e6ff",
          500: "#2f5fd9",
          600: "#254bb0",
          700: "#1c3a8a",
        },
        hot: "#dc2626",
        high: "#ea580c",
        medium: "#ca8a04",
        low: "#64748b",
      },
      fontFamily: {
        sans: ["Assistant", "Rubik", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
