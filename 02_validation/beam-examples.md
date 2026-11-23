# Reference beam cases

Use E = 29,000 ksi, I = 204 in⁴, and S = 33.4 in³ for illustrative W12×26. Loads below exclude self-weight. The material sources and assumptions are in `01_data/illustrative-properties.md`.

1. Simply supported, 20 ft, 1 kip/ft over the full span: reactions 10 kip each; maximum moment wL²/8 = 50 kip-ft; maximum deflection 5wL⁴/(384EI) = 0.608519 in.
2. Cantilever fixed at the left, 20 ft, 1 kip/ft over the full span: vertical reaction 20 kip, internal fixed-end moment −wL²/2 = −200 kip-ft; tip deflection wL⁴/(8EI) = 5.841785 in.
3. Simply supported, 20 ft, 1 kip/ft from 5 to 15 ft: reactions 5 kip each and maximum moment 37.5 kip-ft at midspan. For a centered loaded length c = 10 ft, maximum deflection is wc(8L³ − 4Lc² + c³)/(384EI) = 0.433569 in at midspan (use consistent inch and kip units).
4. Zero load: reactions, moment, shear, and deflection are zero for either support condition.
5. Cantilever fixed at the left, 20 ft, 1 kip/ft from 5 to 15 ft: vertical reaction 10 kip, internal fixed-end moment −100 kip-ft, and tip deflection w[L(b³ − a³) − (b⁴ − a⁴)/4]/(6EI) = 2.555781 in (a = 60 in, b = 180 in, L = 240 in, w = 1/12 kip/in). Shear is −10 kip to 5 ft, rises linearly to zero at 15 ft, and remains zero to the tip.

For the steel example, the additional safety factor changes only the 33 ksi illustrative bending limit: factor 2 gives 16.5 ksi. Deflection limit for 20 ft is 240/360 = 0.666667 in. The lumber example is a property-data example; it is not a separate beam acceptance case yet.
