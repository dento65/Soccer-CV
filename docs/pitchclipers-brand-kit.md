# PitchClipers Pixel Brand Kit

## Core Direction

PitchClipers should feel like a football highlight tool with arcade energy: fast, readable, playful, and technical enough for SaaS. The strongest logo direction combines three signals:

- Football pitch: bright green field, white markings, dark border.
- Clip creation: clipper teeth cutting grass and throwing pixels.
- Video highlights: clapperboard top and play triangle on the clipper body.

## Palette

| Token | Hex | Usage |
| --- | --- | --- |
| Ink | `#052b23` | Outlines, sidebar, heavy UI text |
| Ink 2 | `#0b4034` | Secondary dark surfaces |
| Pitch Green | `#32b521` | Primary brand/action color |
| Stripe Green | `#65d92f` | Field stripes and UI highlights |
| Lime Burst | `#a7f20f` | Pixels, sparks, motion accents |
| Grass Pixel | `#16991d` | Texture details |
| White | `#ffffff` | Field lines, wordmark contrast |

## Motion Rules

Use stepped animation instead of smooth easing when possible. The logo should feel like a tiny game loop:

- Clipper nudges down into the pitch in 3-5 stepped frames.
- Clapper top snaps open/closed like a highlight capture cue.
- Lime pixels burst from the blade and hold briefly before resetting.
- A subtle bob can run on hover, but keep it under 8px.

## Website Translation

Use the logo's pitch grid and clipping particles as product UI language:

- Primary buttons should be green/dark-green rather than blue.
- Upload and timeline areas can use field-stripe patterns.
- Detection/export events can use small square pixels, not glowing blobs.
- Keep panels compact and operational. This is a SaaS workspace, not a landing-page poster.

## Deliverables

- React logo component: `src/components/PitchClipersPixelLogo.jsx`
- Interface styling and logo animation rules: `src/styles.css`
