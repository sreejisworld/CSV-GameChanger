/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#020810',
          900: '#050d1f',
          800: '#0a1628',
          700: '#0d1b2a',
          600: '#0f2137',
          500: '#1e3a5f',
          400: '#2d5080',
        },
        accent: { DEFAULT: '#3b82f6', dark: '#1d4ed8' },
        success: '#22c55e',
        warning: '#f0a500',
        danger:  '#f87171',
        muted:   '#94a3b8',
      },
      animation: {
        'fade-in':  'fadeIn 0.15s ease-out',
        'glow-red': 'glowRed 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0, transform: 'translateY(-4px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        glowRed: { '0%,100%': { boxShadow: '0 0 4px #f87171' }, '50%': { boxShadow: '0 0 12px #f87171, 0 0 4px #f87171' } },
      },
    },
  },
  plugins: [],
}
