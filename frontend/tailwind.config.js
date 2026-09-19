/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0D12",
        surface: "#12161F",
        border: "#232838",
        text: { DEFAULT: "#E7E9EE", muted: "#8B93A7" },
        accent: { DEFAULT: "#D9A441", muted: "#B8862F" },
        flow: { DEFAULT: "#4FB7B3", muted: "#3A8C89" },
        danger: "#E2555F",
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
      },
    },
  },
  plugins: [],
};