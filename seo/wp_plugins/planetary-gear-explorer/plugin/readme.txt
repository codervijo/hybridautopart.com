=== Planetary Gear Ratio Explorer ===
Contributors: hybridautopart
Tags: planetary gear, epicyclic gear, gear ratio, mechanical engineering, calculator
Requires at least: 6.0
Tested up to: 6.7
Stable tag: 0.1.0
Requires PHP: 7.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Interactive planetary (epicyclic) gear ratio calculator and live gear animator. Enter tooth counts, pick a shaft configuration, see ratios and animation update instantly.

== Description ==

**Planetary Gear Ratio Explorer** embeds a fully interactive planetary gear simulator into any WordPress post or page via a simple shortcode.

**Features:**

* Live animated planetary gear diagram — sun, planet, and ring gears rotate at correct relative speeds
* Correct physics using the Willis equation: ω_ring = (1+ρ)·ω_carrier − ρ·ω_sun
* All six shaft configurations: any combination of fixed / input / output across sun, ring, and carrier
* Color-coded shafts — green = input, amber = output, red = fixed
* Rotation direction arrows show clockwise vs counter-clockwise for each shaft
* Gear ratio, output speed, and planet speed computed in real time
* Willis equation displayed with actual numbers substituted for the current configuration
* Six real-world presets: Toyota Hybrid Synergy Drive, automatic transmission, overdrive, reverse gear, robot joint
* Tooth count sliders with instant validation (even planet constraint, spacing constraint)
* Responsive — works on mobile and tablet
* Dark theme, zero external dependencies, self-contained JS bundle (~50 kB gzipped)

**Shortcode:**

`[planetary_gear_explorer]`

With optional attributes:

`[planetary_gear_explorer zsun="30" zring="78" fixed="carrier" input="sun" rpm="1000" height="700px"]`

**Attribute defaults:**

* `zsun` — Sun gear tooth count (default: 30)
* `zring` — Ring gear tooth count (default: 78)
* `fixed` — Fixed shaft: sun | ring | carrier (default: carrier)
* `input` — Input shaft: sun | ring | carrier, must differ from fixed (default: sun)
* `rpm` — Input shaft speed in RPM (default: 1000)
* `height` — Minimum height of the container (default: 700px)

**Ideal for:**

* Mechanical engineering education sites
* Automotive technical blogs (Toyota hybrid systems, automatic transmissions)
* Robotics and maker communities
* Teachers embedding gear ratio lessons

== Installation ==

1. Upload the plugin zip via **Plugins → Add New → Upload Plugin**, or install directly from the WordPress.org plugin directory.
2. Activate the plugin via **Plugins → Installed Plugins**.
3. Add `[planetary_gear_explorer]` to any post or page.

== Frequently Asked Questions ==

= What is the Willis equation? =

The Willis equation describes the relationship between the rotational speeds of the three shafts in a planetary gear system: ω_ring = (1+ρ)·ω_carrier − ρ·ω_sun, where ρ = Zsun/Zring. Given one shaft is fixed and one is the input, the output speed is fully determined.

= Why does planet tooth count have to be a whole number? =

Gears require a whole number of teeth to mesh correctly. The planet tooth count is (Zring − Zsun) / 2, so (Zring − Zsun) must be even. The plugin validates this and shows an error if the constraint is not met.

= Why does the "equally spaced planets" warning appear? =

For three planets to sit at exactly 120° intervals, (Zsun + Zring) must be divisible by 3. This is a manufacturing constraint. The animation still runs correctly; the spacing warning is purely informational.

= Can I show the fixed-ring configuration by default? =

Yes: `[planetary_gear_explorer fixed="ring" input="sun"]`

= Does the plugin work with page builders? =

Yes — the shortcode works in Gutenberg (use a Shortcode block), Elementor, Divi, and any builder that supports standard WordPress shortcodes.

= Does it require any API keys or external services? =

No. All computation and rendering happens in the browser. No data is sent to any external server.

== Screenshots ==

1. Live gear animation with Toyota HSD preset (Zsun=30, Zring=78, carrier fixed)
2. Shaft configuration panel — green=input, amber=output, red=fixed
3. Results panel showing gear ratio, output speed, and Willis equation with substituted values
4. Tooth count inputs with real-time validation
5. Mobile view — responsive layout

== Changelog ==

= 0.1.0 =
* Initial release
* All six planetary shaft configurations
* Willis equation display with live number substitution
* Six real-world presets including Toyota Hybrid Synergy Drive
* Mobile-responsive layout
* Full tooth-count validation (even constraint, equal-spacing check)

== Upgrade Notice ==

= 0.1.0 =
Initial release.
