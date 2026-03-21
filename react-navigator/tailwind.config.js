/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // ── Deep dark navy base ──────────────────────────────────
        navy: {
          950: '#020810',
          900: '#050d1f',
          800: '#0a1628',
          700: '#0d1b2a',
          600: '#0f2137',
          500: '#1e3a5f',
          400: '#2d5080',
        },
        // ── EVOLV brand accents ──────────────────────────────────
        accent:  { DEFAULT: '#3b82f6', dark: '#1d4ed8', dim: 'rgba(59,130,246,0.12)' },
        lime:    { DEFAULT: '#32CD32', dark: '#28a428', dim: 'rgba(50,205,50,0.10)' },
        // ── Semantic ─────────────────────────────────────────────
        success: '#22c55e',
        warning: '#f0a500',
        danger:  '#f87171',
        muted:   '#94a3b8',
        // ── Glassmorphism surfaces ───────────────────────────────
        glass: {
          light: 'rgba(255,255,255,0.04)',
          mid:   'rgba(255,255,255,0.07)',
          hard:  'rgba(255,255,255,0.11)',
        },
      },

      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'ui-monospace', 'monospace'],
      },

      letterSpacing: {
        tightest: '-0.04em',
        tighter:  '-0.03em',
        tight:    '-0.02em',
        wide:     '0.04em',
        widest:   '0.12em',
      },

      borderRadius: {
        xl:  '12px',
        '2xl': '16px',
        '3xl': '20px',
      },

      boxShadow: {
        // Soft-UI neumorphism-lite for dark theme
        'neu':    '4px 4px 10px rgba(0,0,0,0.35), -2px -2px 8px rgba(255,255,255,0.03)',
        'neu-sm': '2px 2px 6px  rgba(0,0,0,0.25), -1px -1px 4px rgba(255,255,255,0.02)',
        // Glow accents
        'lime':   '0 0 0 1px rgba(50,205,50,0.4), 0 0 16px rgba(50,205,50,0.15)',
        'blue':   '0 0 0 1px rgba(59,130,246,0.4), 0 0 16px rgba(59,130,246,0.15)',
        // Card elevations
        'card':   '0 1px 4px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)',
        'card-md':'0 4px 16px rgba(0,0,0,0.35), 0 2px 4px rgba(0,0,0,0.2)',
        'card-lg':'0 8px 32px rgba(0,0,0,0.45), 0 4px 8px rgba(0,0,0,0.25)',
      },

      backgroundImage: {
        // Gradient workspace background
        'workspace': 'linear-gradient(160deg, #020810 0%, #050d1f 55%, #020810 100%)',
        // Card glassmorphism gradient
        'glass-card': 'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)',
        // Lime glow gradient for active states
        'lime-glow': 'linear-gradient(135deg, rgba(50,205,50,0.15) 0%, rgba(50,205,50,0.04) 100%)',
      },

      animation: {
        'fade-in':   'fadeIn   0.18s ease-out',
        'slide-in':  'slideIn  0.22s cubic-bezier(0.22,1,0.36,1)',
        'glow-lime': 'glowLime 2.5s ease-in-out infinite',
        'glow-blue': 'glowBlue 2.5s ease-in-out infinite',
        'pulse-dot': 'pulseDot 2s   ease-in-out infinite',
        'thought':   'thoughtIn 0.3s cubic-bezier(0.22,1,0.36,1) forwards',
      },

      keyframes: {
        fadeIn:   {
          from: { opacity: 0, transform: 'translateY(-4px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        slideIn:  {
          from: { opacity: 0, transform: 'translateX(24px)' },
          to:   { opacity: 1, transform: 'translateX(0)' },
        },
        glowLime: {
          '0%,100%': { boxShadow: '0 0 4px rgba(50,205,50,0.4)' },
          '50%':     { boxShadow: '0 0 16px rgba(50,205,50,0.7), 0 0 4px rgba(50,205,50,0.9)' },
        },
        glowBlue: {
          '0%,100%': { boxShadow: '0 0 4px rgba(59,130,246,0.4)' },
          '50%':     { boxShadow: '0 0 16px rgba(59,130,246,0.7), 0 0 4px rgba(59,130,246,0.9)' },
        },
        pulseDot: {
          '0%,100%': { opacity: 1, transform: 'scale(1)' },
          '50%':     { opacity: 0.5, transform: 'scale(1.4)' },
        },
        thoughtIn: {
          from: { opacity: 0, transform: 'translateX(-8px)' },
          to:   { opacity: 1, transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
