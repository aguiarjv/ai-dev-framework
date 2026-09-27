---
name: frontend-design
description: Design or substantially reshape a web interface with a distinctive, brief-specific visual direction. Use for UI creation or redesign, not routine styling fixes with an established design system.
license: Apache-2.0; see LICENSE.txt
---

# Frontend Design

Create an interface that belongs to the product and its audience, rather than
one that could be reused unchanged for an unrelated brief. Follow the user's
stated visual direction and the project's design system. Do not replace an
established brand or make product decisions that the user has not authorized.
If the subject, audience, or primary purpose is missing and materially affects
the design, ask for it before choosing a direction.

For a new visual direction, establish a compact design concept before coding:
the focal element, palette, typography, layout rhythm, and one or two principles
that connect those choices to the subject. Use real product content where
available; write clear, specific placeholder copy only where needed. Prefer one
memorable visual idea supported by restrained secondary elements.

Make visual structure carry information. Choose typefaces, scale, line length,
spacing, borders, and motion deliberately. Avoid generic defaults such as
repeated identical cards, decorative gradients, arbitrary numbered labels,
all-caps eyebrow text, and routine fade-up animations unless the brief calls
for them. These are possible choices, not prohibited styles; the user's brief
wins.

For a landing page, make the opening treatment characteristic of the product,
not a stock combination of a large metric and gradient accent. Let typography
carry personality without sacrificing readability. Make interface copy useful:
actions should say what happens, terminology should stay consistent across a
flow, and empty or error states should tell people what to do next.

Keep the result usable: responsive layout, readable contrast, semantic
controls, visible keyboard focus, and reduced-motion support where animation
is used. Review the implementation at relevant viewport sizes, using
screenshots when a browser tool is available. Fix visual or interaction issues
that the review reveals.

Adapted from [Anthropic's frontend-design skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design).
