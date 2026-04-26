# VIN Checker Plugin

## What it does

A free, client-side VIN decoder and recall lookup tool for WordPress.

The user enters a 17-character Vehicle Identification Number (VIN). The tool:

1. Decodes the VIN using the free NHTSA vPIC API (no auth, CORS-enabled)
   - URL: `https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{VIN}?format=json`
   - Returns: Year, Make, Model, Trim, Body Style, Engine, Drive Type, Fuel Type, GVWR, Plant Country

2. Fetches active safety recalls from NHTSA Recalls API
   - URL: `https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}`
   - Returns: recall campaigns, component, defect description, remedy description

3. Highlights hybrid/EV status prominently:
   - If Fuel Type contains "Electric", "Hybrid", "PHEV", "HEV" — show a green badge
   - For Toyota/Ford/Honda/Chevy hybrids, show model-specific notes (e.g. "Toyota Prius uses Nickel-Metal Hydride battery in 2010–2015, Lithium-Ion from 2016+")

4. Shows a parts CTA after results — "Need OEM parts for your [Year Make Model]? Shop hybridautopart.com"

## UI layout

- Top: VIN input field + "Check VIN" button + example VINs (Toyota Prius, Honda Civic Hybrid, Ford Escape Hybrid)
- Middle: Vehicle summary card (Year, Make, Model, Trim, Engine, Fuel Type, Body)
- Below that: Hybrid/EV badge section (shown only if applicable)
- Below that: Recalls section — count badge + expandable list of recall campaigns
- Bottom: Parts CTA callout

## Shortcode

`[vin_checker]`

Optional attributes:
- `placeholder` — input placeholder text (default: "Enter 17-character VIN")
- `show_examples` — whether to show example VINs (default: "true")
- `height` — min-height of container (default: "auto")

## Notes

- No API keys needed — NHTSA APIs are free and public
- Must handle invalid VIN format (not 17 chars, non-alphanumeric)
- Must handle "no recalls found" gracefully
- Should validate VIN character set (no I, O, Q allowed)
- The decode API returns many fields — filter to the useful ones only
- Show a loading spinner during API calls
- Both API calls should fire in parallel (Promise.all)
