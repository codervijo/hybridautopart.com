import { useState, useEffect, useRef } from 'react'
import './App.css'

// ─── Physical constants — Prius Gen 3/4 (2010–2022) ──────────────────────────
const RHO         = 0.385   // Zsun / Zring (sun-to-ring tooth ratio)
const FINAL_DRIVE = 3.267   // Ring-gear-to-axle ratio
const K_WHEEL     = 14.0    // Wheel RPM per mph  (205/55R16, circ ≈ 1.924 m)

// Power limits (kW)
const ICE_MAX_KW  = 73
const MG2_MAX_KW  = 60

// Animation scale (show at 4% of real speed so gears are visually readable)
const ANIM_SCALE  = 0.04

// ─── Willis equation ──────────────────────────────────────────────────────────
//   ω_ring = (1 + ρ) · ω_carrier  −  ρ · ω_sun
//   ⟹  ω_sun = ((1 + ρ) · ω_carrier  −  ω_ring) / ρ
//
//   Mapping:  carrier = ICE,  sun = MG1,  ring = MG2
function mg1FromWillis(iceRpm, mg2Rpm) {
  return ((1 + RHO) * iceRpm - mg2Rpm) / RHO
}

// ─── Operating mode detection ─────────────────────────────────────────────────
function detectMode(speed, thr, soc) {
  if (speed < 0.5 && thr < 0.02)                   return 'stopped'
  if (speed < 2   && thr > 0.01 && soc > 0.20)     return 'ev_start'
  if (speed < 2   && thr > 0.01)                   return 'ice_start'
  if (thr < 0.02  && speed > 0.5)                  return 'regen'
  if (speed < 25  && thr < 0.45 && soc > 0.20)     return 'ev_low'
  if (thr > 0.75)                                  return 'full_accel'
  if (speed > 40  && thr < 0.55)                   return 'highway'
  return 'normal'
}

// ─── ICE RPM target (HV ECU control law, simplified) ─────────────────────────
function targetIceRpm(mode, speed, thr) {
  switch (mode) {
    case 'stopped':    return 0
    case 'ev_start':   return 0
    case 'ev_low':     return 0
    case 'regen':      return speed > 12 ? 800 : 0   // idle during high-speed regen
    case 'ice_start':  return 900  + thr * 1200
    case 'highway':    return 1800 + thr * 900  + speed * 3
    case 'full_accel': return 2800 + thr * 1700
    case 'normal':     return 1400 + thr * 1300 + speed * 8
    default:           return 0
  }
}

// ─── Full system state ────────────────────────────────────────────────────────
function computeState(speedMph, thr01, soc01) {
  const mode    = detectMode(speedMph, thr01, soc01)
  const wheelRpm = speedMph * K_WHEEL
  const mg2Rpm   = wheelRpm * FINAL_DRIVE         // ring gear (wheels drive this)
  const iceRpm   = targetIceRpm(mode, speedMph, thr01)
  const mg1Rpm   = mg1FromWillis(iceRpm, mg2Rpm)  // derived — cannot be set independently

  // Power flows in kW (positive = delivering mechanical power to wheels or grid)
  let icePow = 0, mg1Pow = 0, mg2Pow = 0, battPow = 0
  const t = thr01
  const s = Math.min(speedMph / 80, 1)

  switch (mode) {
    case 'stopped':
      break
    case 'ev_start':
    case 'ev_low':
      mg2Pow  =  t * MG2_MAX_KW * 0.70
      battPow = -mg2Pow                            // battery discharges
      break
    case 'regen':
      mg2Pow  = -s * MG2_MAX_KW * 0.45            // MG2 as generator
      battPow = -mg2Pow * 0.92                     // battery charges (loss ~8%)
      break
    case 'ice_start':
      icePow  =  t * ICE_MAX_KW * 0.40
      mg1Pow  = -icePow * 0.45                     // MG1 absorbs ICE reaction (sun held)
      battPow =  icePow * 0.18                     // net charge from MG1 generation
      mg2Pow  =  icePow * 0.22                     // some power reaches wheels
      break
    case 'highway':
      icePow  = (t * 0.50 + s * 0.30) * ICE_MAX_KW
      mg1Pow  =  icePow * 0.28                     // MG1 generating (positive = current to battery)
      battPow =  mg1Pow * 0.90                     // trickle charge
      mg2Pow  =  icePow * 0.72                     // ICE power split reaching ring via planets
      break
    case 'full_accel':
      icePow  =  t * ICE_MAX_KW
      mg2Pow  =  t * MG2_MAX_KW * 0.80            // MG2 electric boost
      battPow = -mg2Pow * 0.85                     // battery supplies MG2 boost
      mg1Pow  = -icePow * 0.10                     // small reaction on sun gear
      break
    case 'normal':
      icePow  =  t * ICE_MAX_KW * 0.55
      mg1Pow  =  icePow * 0.22
      battPow =  mg1Pow * 0.80
      mg2Pow  =  icePow * 0.65 + (-battPow) * 0.20
      break
  }

  return { mode, wheelRpm, mg2Rpm, iceRpm, mg1Rpm, icePow, mg1Pow, mg2Pow, battPow }
}

// ─── Mode display metadata ────────────────────────────────────────────────────
const MODE_COLOR = {
  stopped:    '#64748b',
  ev_start:   '#22c55e',
  ev_low:     '#10b981',
  regen:      '#3b82f6',
  ice_start:  '#f59e0b',
  highway:    '#8b5cf6',
  full_accel: '#ef4444',
  normal:     '#06b6d4',
}

const MODE_LABEL = {
  stopped:    'Stopped',
  ev_start:   'EV Start',
  ev_low:     'EV Mode',
  regen:      'Regenerative Braking',
  ice_start:  'Engine Start',
  highway:    'Highway Cruise',
  full_accel: 'Full Acceleration',
  normal:     'Normal Drive',
}

const MODE_DESC = {
  stopped:    'All systems idle. No power flow.',
  ev_start:   'Starting from rest on battery. MG2 drives wheels via ring gear. ICE off — MG1 freewheels backward (satisfies Willis).',
  ev_low:     'Low speed, light throttle: electric only. ICE stays off. MG1 spins negative to balance the planetary gear.',
  regen:      'Decelerating: wheels backdrive ring gear → MG2 acts as generator → battery charges. ICE off or idling.',
  ice_start:  'Battery low — ICE starts. MG1 applies reaction torque to sun gear; battery trickle-charges from MG1 output.',
  highway:    'ICE in efficiency sweet spot (1800–2800 RPM). MG1 generates from sun gear to top up battery. Net: high MPG.',
  full_accel: 'Maximum output: ICE at peak + battery discharging through MG2. Both power paths merge at ring gear → wheels.',
  normal:     'Combined drive: ICE power splits via planetary gear between MG1 (generator → battery) and MG2 (wheels).',
}

// ─── Canvas layout constants ──────────────────────────────────────────────────
const CW = 600   // canvas CSS width
const CH = 400   // canvas CSS height

// Gear geometry (all in CSS px)
const GCX    = 290   // gear centre-x
const GCY    = 192   // gear centre-y
const R_RING   = 108
const R_SUN    = Math.round(R_RING * RHO)              // ≈ 42
const R_PLANET = Math.floor((R_RING - R_SUN) / 2)     // ≈ 33
const R_ORBIT  = R_SUN + R_PLANET                      // ≈ 75

// Node centres
const N_ICE  = { x: GCX,       y: 24  }
const N_MG1  = { x: 54,        y: GCY }
const N_MG2  = { x: 488,       y: GCY }
const N_BATT = { x: GCX,       y: 374 }
const N_WHLX = 560   // x of "→ Wheels" label (no circle node)

// ─── Canvas drawing helpers ───────────────────────────────────────────────────
function arrow(ctx, x1, y1, x2, y2, color, kw) {
  const pw = Math.min(11, Math.abs(kw) * 0.14)
  if (pw < 0.7) return
  const ang = Math.atan2(y2 - y1, x2 - x1)
  const HEAD = 11 + pw * 0.3

  ctx.save()
  ctx.globalAlpha = 0.9
  ctx.lineWidth   = pw
  ctx.strokeStyle = color
  ctx.fillStyle   = color
  ctx.lineCap     = 'round'

  // Shaft (stop short of arrowhead)
  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2 - HEAD * Math.cos(ang), y2 - HEAD * Math.sin(ang))
  ctx.stroke()

  // Arrowhead
  ctx.beginPath()
  ctx.moveTo(x2, y2)
  ctx.lineTo(x2 - HEAD * Math.cos(ang - 0.40), y2 - HEAD * Math.sin(ang - 0.40))
  ctx.lineTo(x2 - HEAD * Math.cos(ang + 0.40), y2 - HEAD * Math.sin(ang + 0.40))
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

function node(ctx, x, y, label, sub, color, r = 26) {
  // Glow halo
  const g = ctx.createRadialGradient(x, y, r * 0.3, x, y, r * 2.0)
  g.addColorStop(0, color + '3a')
  g.addColorStop(1, color + '00')
  ctx.beginPath()
  ctx.arc(x, y, r * 2.0, 0, 2 * Math.PI)
  ctx.fillStyle = g
  ctx.fill()

  // Circle body
  ctx.beginPath()
  ctx.arc(x, y, r, 0, 2 * Math.PI)
  ctx.fillStyle = '#1e293b'
  ctx.fill()
  ctx.strokeStyle = color
  ctx.lineWidth   = 2.5
  ctx.stroke()

  // Label
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle    = '#f1f5f9'
  ctx.font         = 'bold 11px system-ui'
  ctx.fillText(label, x, y - 5)
  ctx.font      = '9px system-ui'
  ctx.fillStyle = '#94a3b8'
  ctx.fillText(sub, x, y + 7)
}

function gear(ctx, cx, cy, r, teeth, angle, fill, stroke, tLen = 4) {
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, 2 * Math.PI)
  ctx.fillStyle   = fill
  ctx.fill()
  ctx.strokeStyle = stroke
  ctx.lineWidth   = 2
  ctx.stroke()

  // Teeth
  ctx.strokeStyle = stroke
  ctx.lineWidth   = 2.5
  ctx.lineCap     = 'square'
  for (let i = 0; i < teeth; i++) {
    const a = (i / teeth) * 2 * Math.PI + angle
    ctx.beginPath()
    ctx.moveTo(cx + (r - 1) * Math.cos(a), cy + (r - 1) * Math.sin(a))
    ctx.lineTo(cx + (r + tLen) * Math.cos(a), cy + (r + tLen) * Math.sin(a))
    ctx.stroke()
  }
}

function ringGear(ctx, cx, cy, r, teeth, angle) {
  // Outer rim
  ctx.beginPath()
  ctx.arc(cx, cy, r + 15, 0, 2 * Math.PI)
  ctx.fillStyle   = '#0c1526'
  ctx.fill()
  ctx.strokeStyle = '#1e3a5f'
  ctx.lineWidth   = 15
  ctx.stroke()

  // Internal teeth (pointing inward)
  ctx.strokeStyle = '#334155'
  ctx.lineWidth   = 2.5
  ctx.lineCap     = 'square'
  for (let i = 0; i < teeth; i++) {
    const a = (i / teeth) * 2 * Math.PI + angle
    ctx.beginPath()
    ctx.moveTo(cx + (r + 5) * Math.cos(a), cy + (r + 5) * Math.sin(a))
    ctx.lineTo(cx + (r + 18) * Math.cos(a), cy + (r + 18) * Math.sin(a))
    ctx.stroke()
  }
}

// ─── Main canvas render ───────────────────────────────────────────────────────
function drawFrame(canvas, sys, ang) {
  const dpr = window.devicePixelRatio || 1
  const ctx  = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, CW, CH)

  // Background
  ctx.fillStyle = '#0f172a'
  ctx.fillRect(0, 0, CW, CH)

  const { iceRpm, mg1Rpm, mg2Rpm, icePow, mg1Pow, mg2Pow, battPow } = sys

  // ── Shaft connector lines (faint, under arrows) ───────────────────────────
  const gT = { x: GCX, y: GCY - R_RING - 15 }   // top of ring gear
  const gL = { x: GCX - R_RING - 15, y: GCY }   // left
  const gR = { x: GCX + R_RING + 15, y: GCY }   // right
  const gB = { x: GCX, y: GCY + R_RING + 15 }   // bottom

  ctx.save()
  ctx.setLineDash([4, 6])
  ctx.strokeStyle = '#1e293b'
  ctx.lineWidth   = 1
  // ICE shaft
  ctx.beginPath(); ctx.moveTo(N_ICE.x, N_ICE.y + 26); ctx.lineTo(gT.x, gT.y); ctx.stroke()
  // MG1 shaft
  ctx.beginPath(); ctx.moveTo(N_MG1.x + 26, N_MG1.y); ctx.lineTo(gL.x, gL.y); ctx.stroke()
  // MG2 shaft
  ctx.beginPath(); ctx.moveTo(gR.x, gR.y); ctx.lineTo(N_MG2.x - 26, N_MG2.y); ctx.stroke()
  // Battery connector
  ctx.beginPath(); ctx.moveTo(gB.x, gB.y); ctx.lineTo(N_BATT.x, N_BATT.y - 26); ctx.stroke()
  // MG1 ↔ Battery
  ctx.beginPath(); ctx.moveTo(N_MG1.x + 18, N_MG1.y + 18); ctx.lineTo(N_BATT.x - 18, N_BATT.y - 18); ctx.stroke()
  // Battery ↔ MG2
  ctx.beginPath(); ctx.moveTo(N_BATT.x + 18, N_BATT.y - 18); ctx.lineTo(N_MG2.x - 18, N_MG2.y + 18); ctx.stroke()
  ctx.restore()

  // ── Power flow arrows ─────────────────────────────────────────────────────
  // ICE → carrier (top shaft)
  if (icePow > 0.5)
    arrow(ctx, N_ICE.x, N_ICE.y + 26, gT.x, gT.y, '#f59e0b', icePow)

  // MG1: generating (gear → MG1 → battery) or motoring (battery → MG1 → gear)
  if (mg1Pow > 0.5) {
    arrow(ctx, gL.x, gL.y, N_MG1.x + 26, N_MG1.y, '#a78bfa', mg1Pow)
    arrow(ctx, N_MG1.x + 18, N_MG1.y + 18, N_BATT.x - 18, N_BATT.y - 18, '#a78bfa', mg1Pow)
  } else if (mg1Pow < -0.5) {
    arrow(ctx, N_MG1.x + 26, N_MG1.y, gL.x, gL.y, '#c084fc', -mg1Pow)
  }

  // MG2: motoring (gear → MG2 → wheels) or regen (wheels → MG2 → battery)
  if (mg2Pow > 0.5) {
    arrow(ctx, gR.x, gR.y, N_MG2.x - 26, N_MG2.y, '#34d399', mg2Pow)
  } else if (mg2Pow < -0.5) {
    // Regen: wheels → MG2 → gear
    arrow(ctx, N_MG2.x - 26, N_MG2.y, gR.x, gR.y, '#f87171', -mg2Pow)
    arrow(ctx, gB.x, gB.y, N_BATT.x, N_BATT.y - 26, '#f87171', -battPow)
  }

  // Battery: charging (battPow > 0) or discharging to MG2 (battPow < 0)
  if (battPow > 0.5 && mg2Pow >= 0) {
    // Charge flows from MG1 (already drawn above)
  }
  if (battPow < -0.5) {
    // Battery discharging → MG2
    arrow(ctx, N_BATT.x + 18, N_BATT.y - 18, N_MG2.x - 18, N_MG2.y + 18, '#60a5fa', -battPow)
  }

  // ── Planetary gear animation ──────────────────────────────────────────────
  ringGear(ctx, GCX, GCY, R_RING, 28, ang.ring)

  for (let p = 0; p < 3; p++) {
    const orb = ang.carrier + (p * 2 * Math.PI / 3)
    const px  = GCX + R_ORBIT * Math.cos(orb)
    const py  = GCY + R_ORBIT * Math.sin(orb)
    gear(ctx, px, py, R_PLANET, 10, ang.planet + p * 2.09, '#0f2744', '#3b82f6', 4)
  }

  // Sun gear (centre)
  gear(ctx, GCX, GCY, R_SUN, 10, ang.sun, '#2e1065', '#a78bfa', 4)

  // Centre axle dot
  ctx.beginPath()
  ctx.arc(GCX, GCY, 4.5, 0, 2 * Math.PI)
  ctx.fillStyle = '#c4b5fd'
  ctx.fill()

  // ── Nodes ─────────────────────────────────────────────────────────────────
  const iceSub  = iceRpm > 80 ? `${Math.round(iceRpm)} rpm` : 'off'
  const mg1Sign = mg1Rpm >= 0 ? '' : '−'
  const mg1Sub  = `${mg1Sign}${Math.round(Math.abs(mg1Rpm))} rpm`
  const mg2Sub  = `${Math.round(mg2Rpm)} rpm`
  const battSign = battPow > 0.4 ? '+' : ''
  const battSub  = Math.abs(battPow) > 0.4 ? `${battSign}${battPow.toFixed(1)} kW` : 'idle'

  node(ctx, N_ICE.x,  N_ICE.y,  'ICE',     iceSub,  '#f59e0b')
  node(ctx, N_MG1.x,  N_MG1.y,  'MG1',     mg1Sub,  '#a78bfa')
  node(ctx, N_MG2.x,  N_MG2.y,  'MG2',     mg2Sub,  '#34d399')
  node(ctx, N_BATT.x, N_BATT.y, 'Battery', battSub, '#60a5fa')

  // Wheels label
  const whlColor = mg2Pow > 0.5 ? '#34d399' : mg2Pow < -0.5 ? '#f87171' : '#475569'
  if (mg2Pow > 0.5)
    arrow(ctx, N_MG2.x + 26, N_MG2.y, N_WHLX - 10, N_MG2.y, '#34d399', mg2Pow)
  ctx.fillStyle    = whlColor
  ctx.font         = 'bold 10px system-ui'
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('⚙ Wheels', N_WHLX, N_MG2.y - 8)
  ctx.font      = '9px system-ui'
  ctx.fillStyle = '#475569'
  ctx.fillText(`${speedRef_mph(sys)} mph`, N_WHLX, N_MG2.y + 6)

  // Gear axis labels (faint)
  ctx.fillStyle    = '#334155'
  ctx.font         = '9px system-ui'
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('carrier', GCX + 32, GCY - R_RING - 22)
  ctx.fillText('sun',     GCX - R_RING - 28, GCY - 14)
  ctx.fillText('ring',    GCX + R_RING + 28, GCY - 14)
}

// Helper: recover mph from mg2Rpm (inverse of computeState)
function speedRef_mph(sys) {
  return Math.round(sys.mg2Rpm / FINAL_DRIVE / K_WHEEL)
}

// ─── React component ──────────────────────────────────────────────────────────
export default function App() {
  const [speed,    setSpeed]    = useState(30)   // mph  0–80
  const [throttle, setThrottle] = useState(40)   // %    0–100
  const [soc,      setSoc]      = useState(70)   // %    0–100

  const canvasRef = useRef(null)
  const sysRef    = useRef(null)          // latest system state for anim loop
  const angRef    = useRef({ sun: 0, planet: 0, carrier: 0, ring: 0 })
  const lastRef   = useRef(null)
  const rafRef    = useRef(null)

  // Compute state synchronously so UI reflects slider position immediately
  const sys = computeState(speed, throttle / 100, soc / 100)
  sysRef.current = sys   // expose to animation loop without re-subscribing

  // ── Animation loop ────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Size canvas for DPR
    const dpr = window.devicePixelRatio || 1
    canvas.width  = CW * dpr
    canvas.height = CH * dpr
    canvas.style.width  = CW + 'px'
    canvas.style.height = CH + 'px'

    function animate(ts) {
      if (!lastRef.current) lastRef.current = ts
      const dt = Math.min((ts - lastRef.current) / 1000, 0.1)
      lastRef.current = ts

      const s  = sysRef.current
      const K  = (1 / 60) * 2 * Math.PI * ANIM_SCALE   // rpm → rad/s × scale
      const a  = angRef.current

      a.ring    += s.mg2Rpm  * K * dt
      a.carrier += s.iceRpm  * K * dt
      a.sun     += s.mg1Rpm  * K * dt

      // Planet self-rotation (in lab frame):
      // ω_planet = ω_carrier + (R_SUN/R_PLANET) * (ω_carrier − ω_sun)
      const pScale = R_SUN / R_PLANET
      a.planet  += (s.iceRpm * (1 + pScale) - s.mg1Rpm * pScale) * K * dt

      drawFrame(canvas, s, a)
      rafRef.current = requestAnimationFrame(animate)
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [])   // runs once — sysRef keeps it current

  const modeColor = MODE_COLOR[sys.mode]

  // ── Scenario presets ──────────────────────────────────────────────────────
  const presets = [
    { label: 'EV Start',       s: 0,  t: 40, b: 80 },
    { label: 'EV Cruise',      s: 20, t: 25, b: 75 },
    { label: 'Regen Braking',  s: 35, t: 0,  b: 60 },
    { label: 'Highway Cruise', s: 60, t: 40, b: 65 },
    { label: 'Full Throttle',  s: 30, t: 90, b: 75 },
    { label: 'Low Battery',    s: 0,  t: 30, b: 12 },
  ]

  return (
    <div className="psd">
      <h2 className="psd-title">Toyota Power Split Device — Interactive Simulator</h2>
      <p className="psd-subtitle">Prius Gen 3/4 · ρ = {RHO} · Willis equation · Drag sliders to explore</p>

      <canvas ref={canvasRef} className="psd-canvas" />

      {/* ── Controls ── */}
      <div className="psd-controls">
        <Slider label="Vehicle Speed" value={speed}    min={0} max={80}  unit="mph" onChange={setSpeed}    />
        <Slider label="Throttle"      value={throttle} min={0} max={100} unit="%"   onChange={setThrottle} />
        <Slider label="Battery SoC"   value={soc}      min={0} max={100} unit="%"   onChange={setSoc}      color="#60a5fa" />
      </div>

      {/* ── Battery SoC bar ── */}
      <div className="psd-soc-bar">
        <span>Battery</span>
        <div className="soc-track">
          <div className="soc-fill" style={{
            width: `${soc}%`,
            background: soc > 40 ? '#22c55e' : soc > 20 ? '#f59e0b' : '#ef4444',
          }} />
        </div>
        <span>{soc}%</span>
      </div>

      {/* ── Mode badge + description ── */}
      <div className="psd-mode" style={{ borderColor: modeColor + '60' }}>
        <span className="mode-badge" style={{ background: modeColor }}>
          {MODE_LABEL[sys.mode]}
        </span>
        <p className="mode-desc">{MODE_DESC[sys.mode]}</p>
      </div>

      {/* ── RPM / power readouts ── */}
      <div className="psd-readouts">
        <Readout label="ICE"     color="#f59e0b"
          main={sys.iceRpm > 80 ? Math.round(sys.iceRpm) : 'off'}
          unit={sys.iceRpm > 80 ? 'rpm' : ''}
          note={`${sys.icePow.toFixed(1)} kW`} />
        <Readout label="MG1"     color="#a78bfa"
          main={Math.round(sys.mg1Rpm)}
          unit="rpm"
          note={sys.mg1Pow > 0.5 ? 'generating' : sys.mg1Pow < -0.5 ? 'motoring' : 'idle'} />
        <Readout label="MG2"     color="#34d399"
          main={Math.round(sys.mg2Rpm)}
          unit="rpm"
          note={sys.mg2Pow > 0.5 ? 'motoring' : sys.mg2Pow < -0.5 ? 'regen' : 'idle'} />
        <Readout label="Battery" color="#60a5fa"
          main={(sys.battPow > 0.4 ? '+' : '') + sys.battPow.toFixed(1)}
          unit="kW"
          noteColor={sys.battPow > 0.4 ? '#34d399' : sys.battPow < -0.4 ? '#f87171' : '#475569'}
          note={sys.battPow > 0.4 ? 'charging' : sys.battPow < -0.4 ? 'discharging' : 'idle'} />
      </div>

      {/* ── Scenario buttons ── */}
      <div className="psd-scenarios">
        {presets.map(p => (
          <button key={p.label}
            onClick={() => { setSpeed(p.s); setThrottle(p.t); setSoc(p.b) }}>
            {p.label}
          </button>
        ))}
      </div>

      <p className="psd-footer">
        MG1 negative RPM is physically correct — it spins backward in EV mode to satisfy the Willis constraint.
      </p>
    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function Slider({ label, value, min, max, unit, onChange, color = '#3b82f6' }) {
  return (
    <label className="slider-label">
      <span>{label}</span>
      <div className="slider-row">
        <input
          type="range" min={min} max={max} value={value}
          style={{ '--accent': color }}
          onChange={e => onChange(+e.target.value)}
        />
        <span className="slider-val">{value}{unit}</span>
      </div>
    </label>
  )
}

function Readout({ label, color, main, unit, note, noteColor }) {
  return (
    <div className="readout">
      <span className="readout-lbl" style={{ color }}>{label}</span>
      <span className="readout-main">{main}</span>
      <span className="readout-unit">{unit}</span>
      <span className="readout-note" style={{ color: noteColor || '#64748b' }}>{note}</span>
    </div>
  )
}
