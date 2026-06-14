/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // --- Colors (resolved via CSS variables in src/index.css) ---
      colors: {
        primary:        "var(--color-primary)",
        ink:            "var(--color-ink)",
        muted:          "var(--color-muted)",
        surface:        "var(--color-surface)",
        "surface-raised": "var(--color-surface-raised)",
        border:         "var(--color-border)",
        success:        "var(--color-success)",
        warning:        "var(--color-warning)",
        danger:         "var(--color-danger)",
      },

      // --- Spacing (extends defaults, all multiples of 8px base unit) ---
      spacing: {
        xs:  "4px",
        sm:  "8px",
        md:  "16px",
        lg:  "24px",
        xl:  "40px",
        "2xl": "64px",
      },

      // --- Border radius ---
      borderRadius: {
        "radius-sm": "6px",
        "radius-md": "10px",
        "radius-lg": "16px",
      },

      // --- Box shadows ---
      boxShadow: {
        "card":     "0 2px 8px 0 rgba(0, 0, 0, 0.35), 0 1px 2px 0 rgba(0, 0, 0, 0.25)",
        "dropdown": "0 4px 16px 0 rgba(0, 0, 0, 0.45), 0 2px 4px 0 rgba(0, 0, 0, 0.3)",
        "modal":    "0 8px 32px 0 rgba(0, 0, 0, 0.55), 0 4px 8px 0 rgba(0, 0, 0, 0.4)",
      },

      // --- Font families ---
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },

      // --- Motion durations ---
      transitionDuration: {
        fast:   "120ms",
        base:   "200ms",
        slow:   "300ms",
      },
    },
  },
  plugins: [],
};
