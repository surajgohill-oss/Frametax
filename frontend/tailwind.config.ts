import type { Config } from "tailwindcss";

// Source uses fine-grained alpha modifiers like border-white/7 and bg-white/4
// which are not in Tailwind's default opacity scale — provide every integer.
const fullOpacityScale = Object.fromEntries(
  Array.from({ length: 101 }, (_, i) => [String(i), `${i / 100}`]),
);

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      opacity: fullOpacityScale,
    },
  },
  plugins: [],
};
export default config;
