/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        coral: {
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
        },
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
          '50%': { transform: 'translateY(-12px) rotate(2deg)' },
        },
        blob: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%': { transform: 'translate(20px, -20px) scale(1.05)' },
          '66%': { transform: 'translate(-10px, 10px) scale(0.95)' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.92)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
        float: 'float 5s ease-in-out infinite',
        blob: 'blob 8s ease-in-out infinite',
        'gradient-shift': 'gradientShift 6s ease infinite',
        shimmer: 'shimmer 2s linear infinite',
        'scale-in': 'scaleIn 0.35s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
      },
      backgroundImage: {
        'mesh-dark': 'radial-gradient(at 40% 20%, rgb(15 23 42) 0px, transparent 50%), radial-gradient(at 80% 0%, rgb(13 148 136 / 0.25) 0px, transparent 50%), radial-gradient(at 0% 50%, rgb(30 41 59) 0px, transparent 50%), radial-gradient(at 80% 50%, rgb(15 23 42) 0px, transparent 50%)',
        'mesh-hero': 'radial-gradient(ellipse 80% 50% at 50% -20%, rgb(20 184 166 / 0.2), transparent), radial-gradient(ellipse 60% 40% at 100% 0%, rgb(244 63 94 / 0.08), transparent), radial-gradient(ellipse 50% 30% at 0% 50%, rgb(20 184 166 / 0.12), transparent)',
        'grid-pattern': 'linear-gradient(to right, rgb(0 0 0 / 0.04) 1px, transparent 1px), linear-gradient(to bottom, rgb(0 0 0 / 0.04) 1px, transparent 1px)',
        'gradient-teal-coral': 'linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #f43f5e 100%)',
      },
      backgroundSize: {
        grid: '24px 24px',
        'mesh': '200% 200%',
      },
      boxShadow: {
        glow: '0 0 40px -12px rgb(20 184 166 / 0.4)',
        'glow-coral': '0 0 40px -12px rgb(244 63 94 / 0.35)',
        'card-hover': '0 24px 48px -16px rgb(0 0 0 / 0.14)',
        'inner-glow': 'inset 0 0 0 1px rgb(255 255 255 / 0.08)',
      },
    },
  },
  plugins: [],
};
