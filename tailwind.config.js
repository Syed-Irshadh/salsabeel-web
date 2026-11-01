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
    'shadow-academic',
    'shadow-academic-hover',
    'shadow-academic-modal'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          canvas: '#F7F4EC',   /* Warm Ivory (Primary Canvas) */
          ivory: '#F7F4EC',    /* Warm Ivory */
          sand: '#E9E3D6',     /* Warm Sand (Four Pillars & Faculty Background) */
          sage: '#DCE9E6',     /* Muted Sage (Hadith ribbon, About Highlight, Course Filters) */
          surface: '#FFFFFF',  /* Pure White for elevated cards */
          border: '#D8D3C5',   /* Warm Visible Hairline Rule */
          ink: '#0A2528',      /* Primary Text (Deep Charcoal-Teal — 13.5:1 AAA) */
          'ink-muted': '#3B4E50', /* Secondary Slate Ink (6.8:1 AA) */
          bronze: '#7A551E',   /* High-Contrast Bronze Text for Light Surfaces (4.9:1 AA) */
          deep: '#174C4B',     /* Deep Teal (Anchor Tone: Footer, CTAs, Admin Sidebar) */
          primary: '#174C4B',  /* Primary Brand Teal */
          muted: '#2A6362',    /* Muted Teal */
          turquoise: '#A9C5C0', /* Muted Turquoise (Hairlines on Sage) */
          gold: '#B78A43',     /* Antique Gold Accent & Rules */
          'gold-light': '#DFC188', /* Luminous Gold (Solely on Deep Teal surfaces) */
          dark: '#0A2528'      /* Dark Petrol Ink */
        },
        /* Preserved legacy mappings for zero-regression template migration */
        navy: '#174C4B',
        emerald: '#2A6362',
        gold: {
          DEFAULT: '#B78A43',
          light: '#DFC188',
          dark: '#7A551E'
        },
        dark: '#0A2528',
        sand: '#E9E3D6'
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
        'academic': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
        'academic-hover': '0 8px 24px -4px rgba(0, 0, 0, 0.08), 0 4px 8px -4px rgba(0, 0, 0, 0.04)',
        'academic-modal': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'editorial': '0 4px 20px -2px rgba(0, 0, 0, 0.06)'
      }
    }
  },
  plugins: []
};
