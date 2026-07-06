import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0E27",
        "bg-secondary": "#1A1A2E",
        panel: "rgba(255, 255, 255, 0.05)",
        line: "rgba(255, 255, 255, 0.08)",
        primary: "#4F46E5",
        secondary: "#7C3AED",
        accent: "#F59E0B",
        "accent-cyan": "#5eead4",
        "accent-blue": "#93c5fd",
        text: "#FFFFFF",
        muted: "#94A3B8",
        success: "#10B981",
        error: "#EF4444",
        "glass-border": "rgba(255, 255, 255, 0.1)"
      },
      boxShadow: {
        soft: "0 18px 60px rgba(0,0,0,0.25)",
        glow: "0 0 30px rgba(79, 70, 229, 0.3)",
        "glow-amber": "0 0 20px rgba(245, 158, 11, 0.3)",
        glass: "0 8px 32px rgba(0, 0, 0, 0.3)"
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)",
        "gradient-navy": "linear-gradient(180deg, #0A0E27 0%, #1A3A8A 100%)",
        "gradient-radial": "radial-gradient(ellipse at top, rgba(79, 70, 229, 0.15), transparent 50%)",
        "glass-gradient": "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.02) 100%)"
      },
      animation: {
        "float": "float 6s ease-in-out infinite",
        "float-slow": "float 8s ease-in-out infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "bounce-slow": "bounce 2s infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "fade-in-up": "fadeInUp 0.6s ease-out",
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-in-right": "slideInRight 0.4s ease-out",
        "count-up": "countUp 1.5s ease-out"
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" }
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(79, 70, 229, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(79, 70, 229, 0.5)" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" }
        },
        countUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      backdropBlur: {
        xs: "2px"
      }
    }
  },
  plugins: []
};

export default config;

