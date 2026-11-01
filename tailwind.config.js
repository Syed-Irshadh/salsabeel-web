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
          canvas: '#FAFAF7',   /* Warm Scholarly Vellum / Architectural Off-White */
          surface: '#FFFFFF',  /* Luminous White Card Surface */
          border: '#E5E3DA',   /* Hairline 1px Structural Rules */
          ink: '#0A2528',      /* Deep Scholarly Charcoal-Teal (13.8:1 AAA contrast) */
          'ink-muted': '#4A5A5C', /* Secondary Slate Ink (5.8:1 AA contrast) */
          bronze: '#8A6220',   /* Deep Antique Bronze Text on Light (4.8:1 AA contrast) */
          deep: '#06383A',     /* Deep Teal (Anchor Tone: Footer, CTAs, Admin Sidebar) */
          primary: '#08535C',  /* Primary Brand Teal */
          muted: '#0E6873',    /* Muted Turquoise */
          gold: '#C49851',     /* Antique Gold Accent */
          'gold-light': '#DFC188', /* Luminous Gold (Solely on Deep Teal surfaces) */
          ivory: '#FAFAF7',    /* Replaced muddy cream with Warm Canvas */
          dark: '#04272C'      /* Dark Petrol Night */
        },
        /* Preserved legacy mappings for zero-regression template migration */
        navy: '#08535c',
        emerald: '#0e6873',
        gold: {
          DEFAULT: '#8A6220',
          light: '#DFC188',
          dark: '#684A15'
        },
        dark: '#04272c',
        sand: '#FAFAF7'
      },
      fontFamily: {
        serif: ['"Newsreader"', 'Georgia', 'serif'],
        heading: ['"Newsreader"', 'Georgia', 'serif'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        body: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        arabic: ['"Amiri"', '"Traditional Arabic"', 'serif'],
        tamil: ['"Noto Sans Tamil"', 'sans-serif'],
        'tamil-serif': ['"Noto Serif Tamil"', 'serif']
      },
      boxShadow: {
        'academic': '0 1px 3px 0 rgba(4, 39, 44, 0.04), 0 1px 2px -1px rgba(4, 39, 44, 0.04)',
        'academic-hover': '0 8px 24px -4px rgba(4, 39, 44, 0.08), 0 4px 8px -4px rgba(4, 39, 44, 0.04)',
        'academic-modal': '0 25px 50px -12px rgba(4, 39, 44, 0.25)',
        'editorial': '0 4px 20px -2px rgba(6, 56, 58, 0.06)'
      }
    }
  },
  plugins: []
};
