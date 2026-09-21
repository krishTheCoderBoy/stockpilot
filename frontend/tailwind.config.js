/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--color-ink)",
        surface: "var(--color-surface)",
        border: "var(--color-border)",
        text: { DEFAULT: "var(--color-text)", muted: "var(--color-text-muted)" },
        accent: { DEFAULT: "#D9A441", muted: "#B8862F" },
        flow: { DEFAULT: "#4FB7B3", muted: "#3A8C89" },
        danger: "#E2555F",
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: { sm: "6px", md: "10px" },
    },
  },
  plugins: [],
};