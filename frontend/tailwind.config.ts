import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0f1117",
        surface: { 1: "#161b27", 2: "#1e2535", 3: "#252d42" },
        border: "#2a3145",
        accent: "#3b82f6",
        muted: "#6b7280",
      },
    },
  },
  plugins: [],
};
export default config;
