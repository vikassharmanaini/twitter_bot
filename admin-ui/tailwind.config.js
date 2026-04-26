/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
        display: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
      },
      colors: {
        canvas: "hsl(var(--canvas) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        card: {
          DEFAULT: "hsl(var(--card) / <alpha-value>)",
          foreground: "hsl(var(--card-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "hsl(var(--muted) / <alpha-value>)",
          foreground: "hsl(var(--muted-foreground) / <alpha-value>)",
        },
        border: "hsl(var(--border) / <alpha-value>)",
        accent: {
          DEFAULT: "hsl(var(--accent) / <alpha-value>)",
          secondary: "hsl(var(--accent-secondary) / <alpha-value>)",
          tertiary: "hsl(var(--accent-tertiary) / <alpha-value>)",
        },
        success: "hsl(var(--success) / <alpha-value>)",
        danger: "hsl(var(--danger) / <alpha-value>)",
        warning: "hsl(var(--warning) / <alpha-value>)",
      },
      boxShadow: {
        soft: "0 8px 32px -8px hsl(var(--accent) / 0.25), 0 4px 16px -4px hsl(0 0% 0% / 0.08)",
        "soft-lg":
          "0 24px 48px -12px hsl(var(--accent-secondary) / 0.2), 0 12px 24px -8px hsl(0 0% 0% / 0.12)",
        glow: "0 0 40px -8px hsl(var(--accent) / 0.45)",
        inset: "inset 0 1px 0 0 hsl(0 0% 100% / 0.06)",
      },
      borderRadius: {
        "4xl": "1.75rem",
        "5xl": "2rem",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(2%, -3%) scale(1.02)" },
          "66%": { transform: "translate(-2%, 2%) scale(0.98)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 hsl(var(--accent) / 0.45)" },
          "70%": { boxShadow: "0 0 0 14px hsl(var(--accent) / 0)" },
          "100%": { boxShadow: "0 0 0 0 hsl(var(--accent) / 0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        "fade-in": "fade-in 0.35s ease-out forwards",
        float: "float 18s ease-in-out infinite",
        "float-slow": "float 24s ease-in-out infinite reverse",
        shimmer: "shimmer 2.5s linear infinite",
        "pulse-ring": "pulse-ring 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        mesh: "linear-gradient(135deg, hsl(var(--accent) / 0.12) 0%, transparent 50%, hsl(var(--accent-secondary) / 0.1) 100%)",
      },
    },
  },
  plugins: [],
};
