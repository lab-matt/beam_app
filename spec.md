# Beam Designer

## Purpose
Shear, moment, and deflection diagrams for a beam, with separate checks
of bending stress and deflection for the specified loading.

## Inputs
- Simply supported or cantilever, and the span (ft)
- Uniform loads (kip/ft); no point loads
- A steel W-shape or a lumber size, with species and grade for lumber
- Additional safety factor, default 1.0 and minimum 1.0

## Material and member properties
- Define elastic modulus E, moment of inertia I, section modulus S, and
  allowable bending stress for each selectable material and member.
- Document the sources, units, and basis of these properties, including
  any adjustments used for lumber allowable bending stress.
- Use published allowable stresses consistently. The additional safety
  factor is an extra reduction of the allowable stress, not a second
  application of safety provisions already included in the source values.

## Calculations
- Reactions, shear, and moment from statics
- Deflection
- Bending stress fb = M/S, using the maximum absolute bending moment
- Bending stress limit = published allowable bending stress / additional
  safety factor; bending passes when the stress does not exceed this limit
- Deflection compared to L/360
- Apply the additional safety factor to the bending stress limit only;
  keep the deflection limit at L/360

## Outputs
- The beam with its loads, and the three diagrams
- Separate Bending PASS/FAIL and Deflection PASS/FAIL results
- Show the stress and deflection values alongside their respective limits
- Do not present an overall safety verdict; these results cover only the
  bending and deflection checks included in this app

## Look and feel
Clean and professional, with an example beam loaded when it opens.
Use the uniform-load-only validation example below for the initial beam,
without the mockup's point load.
- Inputs in a panel on the left
- beam and diagrams on the right
- window that can be resized
- Make sure that it's esailiy navigatable using the keyboard, including tabbing through inputs and pressing
  Calculate with Enter or Space.
- Uniform loads may cover the full span or a partial span.

## Input validation and recalculation
- Require finite numeric inputs, a span greater than zero, and an
  additional safety factor of at least 1.0.
- Reject any load positions or extents outside the beam if those fields
  are offered.
- Give invalid fields a red border and a short explanation next to the
  field; do not rely on color alone.
- Do not calculate while required inputs are invalid or missing.
- After an analysis input changes, mark existing results as needing
  recalculation until Calculate is pressed successfully.

## Validation
20 ft simply supported W12x26 with 1 kip/ft: M = 50.0 kip-ft,
deflection 0.609 in.

- Record the material properties and reference calculations used for
  each validation case in `02_validation/`.
- Check reactions, shear, moment, deflection, and diagram shapes for
  uniform loads on both simply supported and cantilever beams.
- Include an unloaded beam and partial-span uniform loading if that
  loading option is supported.
- Verify bending and deflection results below, at, and above their limits.
- Verify that increasing the additional safety factor lowers the bending
  stress limit without changing reactions, diagrams, or the L/360 limit.
- Check invalid and missing inputs, red field styling and error messages,
  and the need-to-recalculate state after an input changes.

## Platform
- Python desktop app using Tkinter, started with `python app.py`
- Calculations with numpy, kept in their own module, separate from
  the window code
- Diagrams drawn with matplotlib, embedded in the window

## Out of scope
Point loads, continuous beams, buckling, shear-strength checks, and
connection design.
