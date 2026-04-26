import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

// ─── Animation ────────────────────────────────────────────────────────────────
const ANIM_SCALE = 0.04   // show at 4% real speed for visual clarity

// ─── Canvas layout ────────────────────────────────────────────────────────────
const CW = 600
const CH = 380
const GCX = 295
const GCY = 182
const R_CANVAS = 108   // fixed canvas radius for ring gear inner edge

// ─── Physics ──────────────────────────────────────────────────────────────────

/** Derived planet tooth count. Returns null if constraints not met. */
function zplanetOf(zsun, zring) {
  const zp = (zring - zsun) / 2
  return Number.isInteger(zp) && zp > 0 ? zp : null
}

/** Full validation — returns array of error strings (empty = valid). */
function validate(zsun, zring) {
  const errs = []
  if (!Number.isInteger(zsun) || zsun < 10) errs.push('Sun teeth must be ≥ 10')
  if (!Number.isInteger(zring) || zring < 14) errs.push('Ring teeth must be ≥ 14')
  if (zring <= zsun + 3) errs.push('Ring must have more teeth than Sun + 3')
  if ((zring - zsun) % 2 !== 0) errs.push('(Ring − Sun) must be even so planet teeth are whole numbers')
  return errs
}

/** Willis equation: ω_ring = (1+ρ)·ω_carrier − ρ·ω_sun  where ρ = Zsun/Zring.
 *  Given fixed shaft (speed=0) and input shaft speed, returns all three shaft speeds
 *  plus the output shaft name and ratio = outputSpeed / inputSpeed.
 */
function computeSpeeds(zsun, zring, fixed, input, inputRpm) {
  const rho = zsun / zring
  let sunRpm, ringRpm, carrierRpm

  if (fixed === 'ring') {
    ringRpm = 0
    if (input === 'sun') {
      sunRpm     = inputRpm
      carrierRpm = (rho / (1 + rho)) * sunRpm
    } else {
      carrierRpm = inputRpm
      sunRpm     = ((1 + rho) / rho) * carrierRpm
    }
  } else if (fixed === 'sun') {
    sunRpm = 0
    if (input === 'carrier') {
      carrierRpm = inputRpm
      ringRpm    = (1 + rho) * carrierRpm
    } else {
      ringRpm    = inputRpm
      carrierRpm = ringRpm / (1 + rho)
    }
  } else {
    // fixed === 'carrier'
    carrierRpm = 0
    if (input === 'sun') {
      sunRpm  = inputRpm
      ringRpm = -rho * sunRpm
    } else {
      ringRpm = inputRpm
      sunRpm  = -(1 / rho) * ringRpm
    }
  }

  const output = ['sun', 'ring', 'carrier'].find(s => s !== fixed && s !== input)
  const outputRpm = { sun: sunRpm, ring: ringRpm, carrier: carrierRpm }[output]
  const ratio = inputRpm !== 0 ? outputRpm / inputRpm : 0

  return { sunRpm, ringRpm, carrierRpm, output, ratio, outputRpm }
}

/** Planet self-rotation in lab frame.
 *  Derived from rolling contact with sun gear:
 *  ω_planet = ω_carrier·(1 + Zsun/Zplanet) − ω_sun·(Zsun/Zplanet)
 */
function computePlanetRpm(sunRpm, carrierRpm, zsun, zplanet) {
  const s = zsun / zplanet
  return carrierRpm * (1 + s) - sunRpm * s
}

// ─── Role colours ─────────────────────────────────────────────────────────────
const ROLE_COLOR = {
  input:  '#22c55e',   // green
  output: '#f59e0b',   // amber
  fixed:  '#ef4444',   // red
}

function roleOf(shaft, fixed, input) {
  if (shaft === fixed)  return 'fixed'
  if (shaft === input)  return 'input'
  return 'output'
}

// ─── Canvas drawing ───────────────────────────────────────────────────────────

function gearTeeth(ctx, cx, cy, r, count, angle, color, inward = false, lenPx = 5) {
  ctx.strokeStyle = color
  ctx.lineWidth   = Math.max(1.2, 2.5 - count * 0.04)
  ctx.lineCap     = 'square'
  for (let i = 0; i < count; i++) {
    const a  = (i / count) * 2 * Math.PI + angle
    const r1 = inward ? r + 2   : r - 1
    const r2 = inward ? r + lenPx + 6 : r + lenPx
    ctx.beginPath()
    ctx.moveTo(cx + r1 * Math.cos(a), cy + r1 * Math.sin(a))
    ctx.lineTo(cx + r2 * Math.cos(a), cy + r2 * Math.sin(a))
    ctx.stroke()
  }
}

function drawGear(ctx, cx, cy, r, teeth, angle, fill, stroke) {
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, 2 * Math.PI)
  ctx.fillStyle   = fill
  ctx.fill()
  ctx.strokeStyle = stroke
  ctx.lineWidth   = 2
  ctx.stroke()
  gearTeeth(ctx, cx, cy, r, teeth, angle, stroke)
}

function drawRingGear(ctx, cx, cy, r, teeth, angle, stroke) {
  // Outer rim
  ctx.beginPath()
  ctx.arc(cx, cy, r + 18, 0, 2 * Math.PI)
  ctx.fillStyle   = '#0c1526'
  ctx.fill()
  ctx.strokeStyle = '#1e3a5f'
  ctx.lineWidth   = 18
  ctx.stroke()
  // Internal teeth (pointing inward)
  gearTeeth(ctx, cx, cy, r, teeth, angle, stroke, true, 5)
}

function drawCurvedArrow(ctx, cx, cy, r, color, clockwise) {
  // Small curved arrow around a gear showing rotation direction
  const startA = clockwise ? -0.3 : Math.PI + 0.3
  const endA   = clockwise ? Math.PI * 0.8 : Math.PI * 1.8
  const dir     = clockwise ? 1 : -1

  ctx.save()
  ctx.beginPath()
  ctx.arc(cx, cy, r + 8, startA, endA, !clockwise)
  ctx.strokeStyle = color
  ctx.lineWidth   = 2.5
  ctx.globalAlpha = 0.7
  ctx.stroke()

  // Arrowhead
  const headA = clockwise ? endA : endA
  const hx = cx + (r + 8) * Math.cos(headA)
  const hy = cy + (r + 8) * Math.sin(headA)
  const tang = headA + dir * Math.PI / 2
  ctx.beginPath()
  ctx.moveTo(hx, hy)
  ctx.lineTo(hx - 8 * Math.cos(tang - 0.5), hy - 8 * Math.sin(tang - 0.5))
  ctx.lineTo(hx - 8 * Math.cos(tang + 0.5), hy - 8 * Math.sin(tang + 0.5))
  ctx.closePath()
  ctx.fillStyle = color
  ctx.fill()
  ctx.restore()
}

function shaftLabel(ctx, x, y, name, role, rpm) {
  const color = ROLE_COLOR[role]
  const r     = 30

  // Glow
  const g = ctx.createRadialGradient(x, y, r * 0.2, x, y, r * 2)
  g.addColorStop(0, color + '30')
  g.addColorStop(1, color + '00')
  ctx.beginPath(); ctx.arc(x, y, r * 2, 0, 2 * Math.PI)
  ctx.fillStyle = g; ctx.fill()

  // Circle
  ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI)
  ctx.fillStyle   = '#1e293b'
  ctx.fill()
  ctx.strokeStyle = color
  ctx.lineWidth   = 2.5
  ctx.stroke()

  // Role badge
  const badge = role.toUpperCase()
  ctx.fillStyle    = color
  ctx.font         = 'bold 8px system-ui'
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(badge, x, y - 10)

  // Shaft name
  ctx.fillStyle = '#f1f5f9'
  ctx.font      = 'bold 10px system-ui'
  ctx.fillText(name, x, y + 1)

  // RPM
  const rpmStr = rpm === 0 ? '0 rpm' : `${Math.round(Math.abs(rpm))} rpm`
  ctx.fillStyle = '#94a3b8'
  ctx.font      = '8px system-ui'
  ctx.fillText(rpmStr, x, y + 12)
}

function drawFrame(canvas, state, ang) {
  const dpr = window.devicePixelRatio || 1
  const ctx  = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, CW, CH)
  ctx.fillStyle = '#0f172a'
  ctx.fillRect(0, 0, CW, CH)

  const { zsun, zring, zplanet, fixed, input,
          sunRpm, ringRpm, carrierRpm, ratio } = state

  if (!zplanet) return   // invalid config — nothing to draw

  // Canvas gear radii (proportional to actual tooth counts)
  const rSun    = R_CANVAS * (zsun    / zring)
  const rPlanet = R_CANVAS * (zplanet / zring)
  const rOrbit  = rSun + rPlanet

  const sunRole     = roleOf('sun',     fixed, input)
  const ringRole    = roleOf('ring',    fixed, input)
  const carrierRole = roleOf('carrier', fixed, input)

  const sunCol     = ROLE_COLOR[sunRole]
  const ringCol    = ROLE_COLOR[ringRole]
  const carrierCol = ROLE_COLOR[carrierRole]

  // ── Ring gear ──────────────────────────────────────────────────────────────
  drawRingGear(ctx, GCX, GCY, R_CANVAS, Math.min(zring, 40), ang.ring, ringCol)

  // ── Planet gears (3) ───────────────────────────────────────────────────────
  for (let p = 0; p < 3; p++) {
    const orb = ang.carrier + (p * 2 * Math.PI / 3)
    const px  = GCX + rOrbit * Math.cos(orb)
    const py  = GCY + rOrbit * Math.sin(orb)
    const pAngle = ang.planet + p * (2 * Math.PI / 3) * (zsun / zplanet)

    drawGear(ctx, px, py, rPlanet,
      Math.min(zplanet, 18), pAngle, '#0f2744', carrierCol)

    // Carrier arm (dashed line from centre to planet)
    ctx.save()
    ctx.setLineDash([3, 4])
    ctx.strokeStyle = carrierCol + '55'
    ctx.lineWidth   = 1.5
    ctx.beginPath()
    ctx.moveTo(GCX, GCY)
    ctx.lineTo(px, py)
    ctx.stroke()
    ctx.restore()
  }

  // ── Sun gear ───────────────────────────────────────────────────────────────
  drawGear(ctx, GCX, GCY, rSun,
    Math.min(zsun, 20), ang.sun, '#1c0d38', sunCol)

  // Centre dot
  ctx.beginPath(); ctx.arc(GCX, GCY, 4, 0, 2 * Math.PI)
  ctx.fillStyle = '#c4b5fd'; ctx.fill()

  // ── Rotation direction arrows ──────────────────────────────────────────────
  if (Math.abs(sunRpm) > 10)
    drawCurvedArrow(ctx, GCX, GCY, rSun, sunCol, sunRpm > 0)
  if (Math.abs(carrierRpm) > 10)
    drawCurvedArrow(ctx, GCX, GCY, rOrbit + rPlanet * 0.4, carrierCol, carrierRpm > 0)
  if (Math.abs(ringRpm) > 10)
    drawCurvedArrow(ctx, GCX, GCY, R_CANVAS + 22, ringCol, ringRpm > 0)

  // ── Shaft label nodes ─────────────────────────────────────────────────────
  // Sun: left side
  shaftLabel(ctx, GCX - R_CANVAS - 52, GCY, 'Sun', sunRole, sunRpm)
  // Ring: right side
  shaftLabel(ctx, GCX + R_CANVAS + 52, GCY, 'Ring', ringRole, ringRpm)
  // Carrier: top
  shaftLabel(ctx, GCX, GCY - R_CANVAS - 50, 'Carrier', carrierRole, carrierRpm)

  // ── Gear info overlay (bottom centre) ─────────────────────────────────────
  const rhoStr = (zsun / zring).toFixed(4)
  ctx.fillStyle    = '#334155'
  ctx.font         = '10px monospace'
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'bottom'
  ctx.fillText(
    `Zsun=${zsun}  Zplanet=${zplanet}  Zring=${zring}  ρ=${rhoStr}`,
    GCX, CH - 6
  )
}

// ─── Presets ──────────────────────────────────────────────────────────────────
const PRESETS = [
  { label: 'Toyota HSD',       zsun: 30, zring: 78,  fixed: 'carrier', input: 'sun',     rpm: 1000, note: 'Prius Gen 3/4' },
  { label: 'Simple 4:1',       zsun: 20, zring: 60,  fixed: 'ring',    input: 'sun',     rpm: 1000, note: 'Typical reduction' },
  { label: 'Overdrive',        zsun: 30, zring: 50,  fixed: 'sun',     input: 'carrier', rpm: 1000, note: 'Output faster than input' },
  { label: 'Reverse gear',     zsun: 24, zring: 72,  fixed: 'carrier', input: 'sun',     rpm: 1000, note: 'Fixed carrier reverses output' },
  { label: 'Auto trans 1st',   zsun: 36, zring: 84,  fixed: 'ring',    input: 'sun',     rpm: 2000, note: 'High reduction, same direction' },
  { label: 'Robot joint',      zsun: 16, zring: 64,  fixed: 'ring',    input: 'sun',     rpm: 500,  note: '5:1 actuator reduction' },
]

// ─── Formula builder ──────────────────────────────────────────────────────────
function buildFormula(zsun, zring, fixed, input, inputRpm, speeds) {
  const rho     = (zsun / zring).toFixed(4)
  const { sunRpm, ringRpm, carrierRpm, output, outputRpm } = speeds
  const outVal  = Math.round(outputRpm)
  const inVal   = Math.round(inputRpm)

  const lines = {
    ring: `ω_ring    =  ${Math.round(ringRpm)} rpm`,
    sun:  `ω_sun     =  ${Math.round(sunRpm)} rpm`,
    carrier: `ω_carrier =  ${Math.round(carrierRpm)} rpm`,
  }

  // Show the Willis rearranged for this configuration
  let derived = ''
  if (fixed === 'ring')
    derived = input === 'sun'
      ? `ω_carrier  =  ρ/(1+ρ) × ω_sun  =  ${zsun}/${zsun+zring} × ${inVal}  =  ${outVal} rpm`
      : `ω_sun      =  (1+ρ)/ρ × ω_carrier  =  ${zsun+zring}/${zsun} × ${inVal}  =  ${outVal} rpm`
  else if (fixed === 'sun')
    derived = input === 'carrier'
      ? `ω_ring     =  (1+ρ) × ω_carrier  =  ${zsun+zring}/${zring} × ${inVal}  =  ${outVal} rpm`
      : `ω_carrier  =  ω_ring/(1+ρ)  =  ${inVal} × ${zring}/${zsun+zring}  =  ${outVal} rpm`
  else
    derived = input === 'sun'
      ? `ω_ring     =  −ρ × ω_sun  =  −${zsun}/${zring} × ${inVal}  =  ${outVal} rpm`
      : `ω_sun      =  −(1/ρ) × ω_ring  =  −${zring}/${zsun} × ${inVal}  =  ${outVal} rpm`

  return derived
}

// ─── React component ──────────────────────────────────────────────────────────
const SHAFTS = ['sun', 'ring', 'carrier']

export default function App() {
  const [zsun,     setZsun]     = useState(30)
  const [zring,    setZring]    = useState(78)
  const [fixed,    setFixed]    = useState('carrier')
  const [input,    setInput]    = useState('sun')
  const [inputRpm, setInputRpm] = useState(1000)

  const canvasRef = useRef(null)
  const stateRef  = useRef(null)
  const angRef    = useRef({ sun: 0, planet: 0, carrier: 0, ring: 0 })
  const lastRef   = useRef(null)
  const rafRef    = useRef(null)

  // ── Derived ────────────────────────────────────────────────────────────────
  const errors  = validate(zsun, zring)
  const valid   = errors.length === 0
  const zplanet = valid ? zplanetOf(zsun, zring) : null
  const rho     = zsun / zring
  const output  = SHAFTS.find(s => s !== fixed && s !== input)
  const speeds  = valid ? computeSpeeds(zsun, zring, fixed, input, inputRpm) : null
  const pRpm    = valid && speeds && zplanet
    ? computePlanetRpm(speeds.sunRpm, speeds.carrierRpm, zsun, zplanet)
    : 0

  const evenSpacing = valid && (zsun + zring) % 3 === 0

  // Keep ref current for animation loop
  stateRef.current = { zsun, zring, zplanet, fixed, input, output,
    sunRpm:     speeds?.sunRpm     ?? 0,
    ringRpm:    speeds?.ringRpm    ?? 0,
    carrierRpm: speeds?.carrierRpm ?? 0,
    ratio:      speeds?.ratio      ?? 0,
  }

  // ── Animation loop ─────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const dpr = window.devicePixelRatio || 1
    canvas.width  = CW * dpr
    canvas.height = CH * dpr
    canvas.style.width  = CW + 'px'
    canvas.style.height = CH + 'px'

    function animate(ts) {
      if (!lastRef.current) lastRef.current = ts
      const dt = Math.min((ts - lastRef.current) / 1000, 0.1)
      lastRef.current = ts

      const s = stateRef.current
      const K = (1 / 60) * 2 * Math.PI * ANIM_SCALE

      angRef.current.sun     += s.sunRpm     * K * dt
      angRef.current.ring    += s.ringRpm    * K * dt
      angRef.current.carrier += s.carrierRpm * K * dt

      // Planet self-spin (lab frame)
      const zp = s.zplanet ?? 1
      const ps = s.zsun / zp
      angRef.current.planet += (s.carrierRpm * (1 + ps) - s.sunRpm * ps) * K * dt

      drawFrame(canvas, stateRef.current, angRef.current)
      rafRef.current = requestAnimationFrame(animate)
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [])

  // ── Shaft selector helpers ─────────────────────────────────────────────────
  function handleFixedChange(newFixed) {
    setFixed(newFixed)
    if (input === newFixed)
      setInput(SHAFTS.find(s => s !== newFixed && s !== output) ?? SHAFTS.find(s => s !== newFixed))
  }

  function handleInputChange(newInput) {
    setInput(newInput)
  }

  // ── Preset loader ──────────────────────────────────────────────────────────
  function loadPreset(p) {
    setZsun(p.zsun); setZring(p.zring)
    setFixed(p.fixed); setInput(p.input)
    setInputRpm(p.rpm)
  }

  // ── Ratio display ──────────────────────────────────────────────────────────
  const ratio        = speeds?.ratio ?? 0
  const absRatio     = Math.abs(ratio)
  const gearRatio    = absRatio > 0.001 ? (1 / absRatio).toFixed(3) : '∞'
  const reversed     = ratio < -0.001
  const speedUp      = absRatio > 1.001
  const ratioLabel   = reversed ? 'Reversed' : speedUp ? 'Speed increase' : 'Reduction'

  const formula = valid && speeds
    ? buildFormula(zsun, zring, fixed, input, inputRpm, speeds)
    : null

  return (
    <div className="pgx">
      <h2 className="pgx-title">Planetary (Epicyclic) Gear Ratio Explorer</h2>
      <p className="pgx-sub">
        Set tooth counts and shaft configuration — gear ratios and animation update live.
      </p>

      <canvas ref={canvasRef} className="pgx-canvas" />

      {/* ── Presets ── */}
      <div className="pgx-presets">
        {PRESETS.map(p => (
          <button key={p.label} onClick={() => loadPreset(p)} title={p.note}>
            {p.label}
          </button>
        ))}
      </div>

      {/* ── Tooth count inputs ── */}
      <section className="pgx-section">
        <h3>Tooth Counts</h3>
        <div className="pgx-tooth-grid">
          <TeethInput label="Sun (Zsun)" value={zsun} min={10} max={80}
            color={ROLE_COLOR[roleOf('sun', fixed, input)]}
            onChange={setZsun} />
          <TeethInput label="Ring (Zring)" value={zring} min={zsun + 4} max={200}
            color={ROLE_COLOR[roleOf('ring', fixed, input)]}
            onChange={setZring} />
          <div className="pgx-derived">
            <span className="derived-label">Planet (derived)</span>
            <span className="derived-value" style={{ color: ROLE_COLOR[roleOf('carrier', fixed, input)] }}>
              {zplanet !== null ? zplanet : <span className="err">—</span>}
            </span>
            <span className="derived-note">= (Ring − Sun) / 2</span>
          </div>
          <div className="pgx-derived">
            <span className="derived-label">ρ = Zsun / Zring</span>
            <span className="derived-value" style={{ color: '#94a3b8' }}>
              {rho.toFixed(4)}
            </span>
            <span className="derived-note">{valid ? `${zsun}/${zring}` : ''}</span>
          </div>
        </div>
        {errors.map(e => <p key={e} className="pgx-error">{e}</p>)}
        {valid && !evenSpacing && (
          <p className="pgx-warn">
            (Zsun + Zring) = {zsun + zring} is not divisible by 3 — planets cannot be equally spaced.
            Animation still shown.
          </p>
        )}
      </section>

      {/* ── Shaft configuration ── */}
      <section className="pgx-section">
        <h3>Shaft Configuration</h3>
        <div className="pgx-shafts">
          <ShaftRow label="Fixed (speed = 0)" value={fixed} options={SHAFTS}
            color={ROLE_COLOR.fixed} onChange={handleFixedChange} />
          <ShaftRow label="Input" value={input} options={SHAFTS.filter(s => s !== fixed)}
            color={ROLE_COLOR.input} onChange={handleInputChange} />
          <div className="shaft-row">
            <span className="shaft-label" style={{ color: ROLE_COLOR.output }}>Output (derived)</span>
            <span className="shaft-output">{output?.toUpperCase()}</span>
          </div>
        </div>

        <div className="pgx-rpm-row">
          <label>Input RPM</label>
          <input type="range" min={0} max={3000} step={10} value={inputRpm}
            onChange={e => setInputRpm(+e.target.value)} />
          <span className="rpm-val">{inputRpm} rpm</span>
        </div>
      </section>

      {/* ── Results ── */}
      {valid && speeds && (
        <section className="pgx-section pgx-results">
          <h3>Results</h3>
          <div className="result-grid">
            <ResultCell label="Gear Ratio" value={gearRatio + ' : 1'}
              note={ratioLabel}
              color={reversed ? '#ef4444' : speedUp ? '#f59e0b' : '#22c55e'} />
            <ResultCell label="Output Speed"
              value={`${Math.round(speeds.outputRpm)} rpm`}
              note={reversed ? '← reversed' : '→ same direction'}
              color={ROLE_COLOR.output} />
            <ResultCell label="Planet Speed"
              value={`${Math.round(Math.abs(pRpm))} rpm`}
              note={pRpm >= 0 ? '→' : '← reversed'}
              color={ROLE_COLOR[roleOf('carrier', fixed, input)]} />
            <ResultCell label="Willis ρ"
              value={rho.toFixed(4)}
              note={`${zsun}/${zring}`}
              color="#94a3b8" />
          </div>

          {/* All shaft speeds */}
          <div className="speed-table">
            {[
              { shaft: 'Sun',     rpm: speeds.sunRpm,     role: roleOf('sun',     fixed, input) },
              { shaft: 'Planet',  rpm: pRpm,              role: roleOf('carrier', fixed, input) },
              { shaft: 'Ring',    rpm: speeds.ringRpm,    role: roleOf('ring',    fixed, input) },
              { shaft: 'Carrier', rpm: speeds.carrierRpm, role: roleOf('carrier', fixed, input) },
            ].map(({ shaft, rpm, role }) => (
              <div key={shaft} className="speed-row">
                <span className="speed-shaft" style={{ color: ROLE_COLOR[role] }}>
                  {shaft}
                </span>
                <SpeedBar rpm={rpm} max={Math.max(3000, Math.abs(inputRpm) * 5)} />
                <span className="speed-val" style={{ color: rpm === 0 ? '#475569' : '#f1f5f9' }}>
                  {rpm === 0 ? 'fixed' : `${Math.round(rpm) >= 0 ? '+' : ''}${Math.round(rpm)} rpm`}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Willis equation panel ── */}
      {valid && speeds && (
        <section className="pgx-section pgx-formula">
          <h3>Willis Equation</h3>
          <code className="formula-base">
            ω_ring = (1 + ρ) · ω_carrier − ρ · ω_sun
          </code>
          <code className="formula-base">
            ρ = Zsun / Zring = {zsun}/{zring} = {rho.toFixed(4)}
          </code>
          <div className="formula-divider" />
          <code className="formula-derived">
            {formula}
          </code>
          <p className="formula-config">
            Configuration: <strong>{fixed} fixed</strong> · <strong>{input} input</strong> · <strong>{output} output</strong>
            {reversed && ' · Output direction reversed'}
          </p>
        </section>
      )}

      {/* ── Real-world examples ── */}
      <section className="pgx-section pgx-examples">
        <h3>Real-World Uses of Each Configuration</h3>
        <div className="examples-grid">
          <ExampleCard fixed="Ring" use="Automatic transmission (1st–3rd gear), final drive reduction, robot joints" />
          <ExampleCard fixed="Sun"  use="Overdrive units, stepless CVT assist stage, some wind turbine gearboxes" />
          <ExampleCard fixed="Carrier" use="Reverse gear (output reverses), some differential locking mechanisms" />
        </div>
      </section>
    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function TeethInput({ label, value, min, max, color, onChange }) {
  return (
    <div className="teeth-input">
      <span className="teeth-label" style={{ color }}>{label}</span>
      <div className="teeth-row">
        <input type="range" min={min} max={max} value={value}
          style={{ '--acc': color }}
          onChange={e => onChange(+e.target.value)} />
        <input type="number" min={min} max={max} value={value}
          onChange={e => { const v = parseInt(e.target.value); if (!isNaN(v)) onChange(v) }} />
      </div>
    </div>
  )
}

function ShaftRow({ label, value, options, color, onChange }) {
  return (
    <div className="shaft-row">
      <span className="shaft-label" style={{ color }}>{label}</span>
      <div className="shaft-btns">
        {options.map(s => (
          <button key={s}
            className={`shaft-btn ${value === s ? 'active' : ''}`}
            style={value === s ? { borderColor: color, color } : {}}
            onClick={() => onChange(s)}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>
    </div>
  )
}

function ResultCell({ label, value, note, color }) {
  return (
    <div className="result-cell">
      <span className="rc-label">{label}</span>
      <span className="rc-value" style={{ color }}>{value}</span>
      <span className="rc-note">{note}</span>
    </div>
  )
}

function SpeedBar({ rpm, max }) {
  const pct = Math.min(100, (Math.abs(rpm) / max) * 100)
  const reversed = rpm < 0
  return (
    <div className="speed-bar-track">
      <div className="speed-bar-fill"
        style={{
          width: `${pct}%`,
          background: reversed ? '#ef4444' : '#22c55e',
          marginLeft: reversed ? 'auto' : 0,
        }} />
    </div>
  )
}

function ExampleCard({ fixed, use }) {
  return (
    <div className="example-card">
      <span className="ex-fixed" style={{ color: ROLE_COLOR.fixed }}>Fixed: {fixed}</span>
      <p className="ex-use">{use}</p>
    </div>
  )
}
