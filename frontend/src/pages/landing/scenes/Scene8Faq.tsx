import type { SceneApi } from "../hooks/useScrollScene";
import { REVEAL } from "../lib/reveal";
import { MaskedLines } from "../ui/MaskedLines";
import { sceneMeta } from "./data";
import { Accordion, type AccordionItem } from "./faq/Accordion";
import { SceneShell } from "./SceneShell";

const meta = sceneMeta(8);

// Placeholder answers: review them against how your team actually works.
const FAQ: AccordionItem[] = [
  {
    question: "How does StockPilot know when to reorder?",
    answer:
      "Every item carries a reorder point. When the quantity on hand crosses it you get an alert, early enough to raise a purchase order before the shelf is empty.",
  },
  {
    question: "Can I track stock across more than one warehouse?",
    answer:
      "Yes. Each warehouse keeps its own quantities, and transfers between them are recorded as a movement, so nothing disappears in transit.",
  },
  {
    question: "What happens when a delivery arrives short?",
    answer:
      "You receive what actually turned up against the purchase order. The order stays open for the balance, and the shortfall is visible to everyone who needs to chase it.",
  },
  {
    question: "Who can approve a purchase order?",
    answer:
      "Approval follows roles. People who raise orders cannot sign off their own, and every decision is logged with who made it and when.",
  },
  {
    question: "Is every stock movement recorded?",
    answer:
      "Receipts, issues, transfers and adjustments are all logged with the person and the time, so you can see how any quantity got to where it is.",
  },
  {
    question: "How do I get an account?",
    answer:
      "An administrator creates your account. You then confirm it with a one-time code sent to your email, and can sign in straight away.",
  },
];

function setupFaq({ gsap, scope, motion }: SceneApi) {
  if (!motion) return;
  gsap.from(scope.querySelectorAll(REVEAL.selector), {
    yPercent: REVEAL.yPercent,
    duration: 1.3,
    ease: REVEAL.ease,
    stagger: REVEAL.stagger,
    scrollTrigger: { trigger: scope, start: "top 65%", toggleActions: "play none none reverse" },
  });
  gsap.from(scope.querySelectorAll(".lp-faq__item"), {
    opacity: 0,
    y: 28,
    duration: 0.9,
    ease: REVEAL.ease,
    stagger: 0.07,
    scrollTrigger: { trigger: scope.querySelector(".lp-faq__list"), start: "top 85%", toggleActions: "play none none reverse" },
  });
}

export function Scene8Faq() {
  return (
    <SceneShell index={meta.index} name={meta.name} theme={meta.theme} pin={false} className="lp-faq" setup={setupFaq}>
      <div className="lp-faq__inner">
        <p className="lp-label lp-faq__eyebrow">Questions</p>
        <h2 className="lp-display lp-faq__title">
          <MaskedLines lines={["Answers"]} />
        </h2>
        <Accordion items={FAQ} />
      </div>

      {/* enormous footer wordmark that bleeds off the bottom edge */}
      <div className="lp-faq__wordmark" aria-hidden="true">
        StockPilot
      </div>
    </SceneShell>
  );
}
