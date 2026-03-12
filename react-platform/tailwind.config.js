/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          base:    '#07070f',
          surface: '#0d0d1c',
          card:    '#111124',
          hover:   '#17172e',
        },
        lime: {
          DEFAULT: '#32CD32',
          50:  '#f0fdf0',
          dim: 'rgba(50,205,50,0.12)',
          glow:'rgba(50,205,50,0.25)',
        },
        blue: {
          DEFAULT: '#007FFF',
          dim: 'rgba(0,127,255,0.12)',
          glow:'rgba(0,127,255,0.25)',
        },
        border: {
          base:   '#1c1c38',
          bright: '#28284a',
          lime:   'rgba(50,205,50,0.3)',
          blue:   'rgba(0,127,255,0.3)',
        },
        text: {
          primary:   '#e2e8f0',
          secondary: '#94a3b8',
          muted:     '#475569',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        'fade-in': {
          from: { opacity: 0, transform: 'translateY(6px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        'slide-in': {
          from: { opacity: 0, transform: 'translateX(-8px)' },
          to:   { opacity: 1, transform: 'translateX(0)' },
        },
        'pulse-lime': {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(50,205,50,0.4)' },
          '50%':     { boxShadow: '0 0 0 6px rgba(50,205,50,0)' },
        },
        'glow-blue': {
          '0%,100%': { boxShadow: '0 0 8px rgba(0,127,255,0.3)' },
          '50%':     { boxShadow: '0 0 20px rgba(0,127,255,0.6)' },
        },
        'float': {
          '0%,100%': { transform: 'translateY(0px) perspective(300px) rotateX(5deg)' },
          '50%':     { transform: 'translateY(-6px) perspective(300px) rotateX(3deg)' },
        },
      },
      animation: {
        'fade-in':   'fade-in 0.25s ease-out',
        'slide-in':  'slide-in 0.2s ease-out',
        'pulse-lime':'pulse-lime 2s ease-in-out infinite',
        'glow-blue': 'glow-blue 2s ease-in-out infinite',
        'float':     'float 4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
