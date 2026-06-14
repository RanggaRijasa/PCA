/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#06152F",
          900: "#0A1E42"
        },
        brand: {
          50: "#EEF0FF",
          500: "#5B4DFF",
          600: "#493EE6"
        }
      },
      boxShadow: {
        panel: "0 12px 35px rgba(15, 23, 42, 0.07)"
      }
    }
  },
  plugins: []
};

