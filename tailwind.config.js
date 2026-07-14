/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./backend/templates/**/*.html",
    "./backend/apps/**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ecfdf8",
          100: "#d1faf0",
          200: "#a7f3e0",
          300: "#6ee7cb",
          400: "#34d3b0",
          500: "#14b89a",
          600: "#0d947c",
          700: "#0f7668",
          800: "#115e55",
          900: "#134e48",
          950: "#042f2c",
        },
      },
      fontFamily: {
        sans: [
          "DM Sans",
          "Segoe UI",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 4px 24px -4px rgb(15 118 104 / 0.12)",
        "card-hover": "0 12px 40px -8px rgb(15 118 104 / 0.22)",
        nav: "0 1px 0 rgb(0 0 0 / 0.05), 0 8px 24px -8px rgb(0 0 0 / 0.08)",
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out forwards",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
