# PSD Simulator — Claude Code Handoff Prompt

## Context
You are taking over development of an interactive Toyota Power Split Device (PSD) simulator that will be embedded as a WordPress plugin on hybridautopart.com. This is an SEO play — the page already has 57,724 impressions/year but low CTR. A working interactive simulator will earn backlinks from Toyota forums, Reddit communities, and engineering sites, driving 10x traffic growth.

## Project location
```
psd-simulator/
├── plugin/
│   ├── psd-simulator.php   ← WordPress plugin (shortcode: [psd_simulator])
│   └── dist/               ← Vite build output (auto-generated, don't edit)
├── react-app/
│   ├── src/
│   │   ├── main.jsx        ← mounts React to #psd-root
│   │   ├── App.jsx         ← main simulator component
│   │   ├── App.css
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js      ← builds to ../plugin/dist/
│   └── package.json
└── README.md
```

## Current state
- Basic working prototype with speed + throttle sliders
- Canvas-based animated power flow diagram (ICE, MG1, MG2, Wheels nodes)
- 7 operating modes detected: stopped, ev_start, ev_low, regen, full_accel, highway, normal
- Scenario buttons for quick mode testing
- Mounts to `#psd-root` div (WordPress shortcode injects this div)

## What needs to be built next

### Priority 1 — Accuracy (your engineering task)
The planetary gear math needs to be implemented properly using the Willis equation:

```
ω_ring = (1 + ρ) × ω_carrier − ρ × ω_sun
where ρ = Zsun / Zring (tooth ratio, ~0.385 for Prius)
```

- ICE connects to planet carrier
- MG1 connects to sun gear
- MG2 + drive wheels connect to ring gear
- At any speed, calculate actual RPM of ICE, MG1, MG2 from wheel speed + throttle
- Show real RPM values on each node, not just % contribution
- Add battery SoC bar (0–100%) that depletes in EV mode, charges in regen

### Priority 2 — Visual improvements
- Animate the planetary gears rotating (sun, planet, ring) using canvas arcs
  - Sun gear (center, small) — connected to MG1
  - Planet gears (3x, orbiting) — connected to ICE carrier
  - Ring gear (outer) — connected to MG2 + wheels
- Show torque flow direction with arrow thickness proportional to power
- Add smooth transitions between operating modes
- Color-code power arrows by source (blue=ICE, green=MG2, amber=MG1, red=regen)

### Priority 3 — UX enhancements
- Add a battery state of charge (SoC) slider so user can set starting battery level
- Show fuel economy impact indicator (MPG estimate based on mode)
- Add "ECO mode" toggle that adjusts throttle mapping
- Add "PWR mode" toggle that increases throttle sensitivity
- Mobile touch support (already works via range inputs, verify on small screens)
- Add a "What's happening?" text explanation panel below diagram that updates with mode

### Priority 4 — WordPress integration polish
- Add `height` and `theme` shortcode attributes: `[psd_simulator height="700px" theme="dark"]`
- Make the plugin detect WordPress theme color scheme and adapt
- Add a WordPress admin settings page (Settings → PSD Simulator) for config

## Build and deploy workflow
```bash
# Development
cd react-app
npm install
npm run dev          # runs at localhost:5173

# Build for WordPress
npm run build        # outputs to plugin/dist/

# Deploy plugin to server
scp -r plugin/ user@hybridautopart.com:/var/www/html/wp-content/plugins/psd-simulator/

# In WordPress
# Admin → Plugins → Activate "PSD Simulator"
# Add [psd_simulator] shortcode to post: /blog-en/toyota-prius-power-split-device/
```

## Key technical facts about the Toyota PSD
- Prius Gen 3/4 (2010–2022): ρ = 0.385 (sun/ring tooth ratio)
- ICE max RPM: ~4500 rpm, optimal efficiency: 1800–2800 rpm
- MG1 max RPM: ~10,000 rpm (acts as generator, speed-controls ICE via CVT effect)
- MG2 max RPM: ~13,500 rpm (main drive motor, always connected to wheels)
- At highway speed, MG1 spins in reverse direction to maintain ICE efficiency
- EV mode: ICE disconnected, MG2 only — only works below ~25 mph and ~40% throttle
- Regenerative braking: MG2 becomes generator, MG1 freewheels

## Target deployment page
https://hybridautopart.com/blog-en/toyota-prius-power-split-device/
- Add shortcode in WordPress Gutenberg editor using HTML block
- Place it after the intro paragraph, before the Construction section
- Add caption: "Interactive simulator — drag the sliders to see how power flows"

## Owner context
- Vik Thomas, embedded systems engineer (motor control background)
- Comfortable with React/Vite, learning WordPress
- Server access via SFTP/SSH
- WordPress hosted on GoDaddy Managed WordPress
- Yoast SEO plugin installed (free version)

## Success criteria
- Simulator loads correctly on the live WordPress page
- All 7 operating modes show correct power flow
- Planetary gear animation is visually accurate
- Page loads fast — JS bundle under 150KB gzipped
- Works on mobile (touch sliders)
- No console errors in production build
