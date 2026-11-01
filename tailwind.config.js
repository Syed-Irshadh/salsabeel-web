/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"
  ],
  safelist: [
    'hidden',
    'active',
    '-translate-x-full',
    'toast-item',
    'bg-emerald/10',
    'bg-emerald/15',
    'bg-emerald/20',
    'bg-emerald/30',
    'bg-gold/15',
    'bg-gold/20',
    'bg-gold/25',
    'bg-amber-50',
    'bg-red-50',
    'border-emerald/20',
    'border-emerald/40',
    'border-emerald/50',
    'border-gold/20',
    'border-gold/30',
    'border-gold/40',
    'border-amber-200',
    'border-amber-300',
    'border-red-200',
    'text-emerald',
    'text-navy',
    'text-gold',
    'text-red-500',
    'text-red-600',
    'text-amber-500',
    'text-amber-900',
    'text-gray-400',
    'text-gray-600',
    'text-gray-800',
    'shadow-glow-teal',
    'shadow-glow-gold',
    'shadow-academic',
    'shadow-academic-hover',
    'shadow-academic-modal'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          deep: '#06383A',     /* Deep Teal (Sidebar & Dark Surface) */
          primary: '#08535C',  /* Primary Brand Teal */
          muted: '#0E6873',    /* Muted Turquoise */
          gold: '#C49851',     /* Antique Gold */
          ivory: '#F8F7F2',    /* Ivory Background Canvas */
          dark: '#04272C'      /* Dark Petrol Night */
        },
        /* Preserved legacy mappings for zero-regression template migration */
        navy: '#08535c',
        emerald: '#0e6873',
        gold: {
          DEFAULT: '#c49851',
          light: '#dfb76c',
          dark: '#a17936'
        },
        dark: '#04272c',
        sand: '#f8f7f2'
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        body: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        tamil: ['"Noto Sans Tamil"', '"Plus Jakarta Sans"', 'sans-serif'],
        arabic: ['"Amiri"', '"Traditional Arabic"', 'serif']
      },
      boxShadow: {
        'academic': '0 1px 3px 0 rgba(4, 39, 44, 0.04), 0 1px 2px -1px rgba(4, 39, 44, 0.04)',
        'academic-hover': '0 10px 25px -5px rgba(4, 39, 44, 0.08), 0 8px 10px -6px rgba(4, 39, 44, 0.04)',
        'academic-modal': '0 25px 50px -12px rgba(4, 39, 44, 0.25)',
        'glow-gold': '0 0 24px rgba(196, 152, 81, 0.35)',
        'glow-teal': '0 0 28px rgba(14, 104, 115, 0.35)'
      }
    }
  },
  plugins: []
};
