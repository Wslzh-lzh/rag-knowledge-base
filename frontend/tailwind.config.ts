import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b1020",
        panel: "#111936",
        line: "#243055",
        accent: "#5eead4",
        accent2: "#93c5fd",
        text: "#e5eefc",
        muted: "#8b9ab7"
      },
      boxShadow: {
        soft: "0 18px 60px rgba(0,0,0,0.25)"
      }
    }
  },
  plugins: []
};

export default config;

