// Text reveal from docs/landing-spec.md: split by line, masked, translateY(110%) to 0,
// stagger 0.08, expo.out. Lines are authored with <MaskedLines> and found by this attribute.
export const REVEAL = {
  selector: "[data-reveal-line]",
  yPercent: 110,
  stagger: 0.08,
  ease: "expo.out",
} as const;
