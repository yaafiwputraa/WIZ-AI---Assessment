import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17221d",
        sage: "#60766b",
        mist: "#eff5f1",
        emerald: "#087f5b",
        lime: "#d8f26a",
        sand: "#fbfaf5"
      },
      boxShadow: {
        panel: "0 24px 80px rgba(25, 56, 43, 0.10)",
      },
    },
  },
  plugins: [],
} satisfies Config;

