import { useId, useRef, useState, type KeyboardEvent } from "react";

export interface AccordionItem {
  question: string;
  answer: string;
}

/**
 * Accessible accordion (WAI-ARIA "accordion" pattern): each header is a button with
 * aria-expanded / aria-controls, each answer is a labelled region, and Up / Down / Home / End
 * move between headers. Enter and Space toggle, because the headers are real buttons.
 * Height animates through a CSS grid-row transition; closed panels are `visibility: hidden`
 * so their contents cannot be tabbed to.
 */
export function Accordion({ items }: { items: AccordionItem[] }) {
  const baseId = useId();
  const [open, setOpen] = useState<Set<number>>(() => new Set([0]));
  const buttons = useRef<Array<HTMLButtonElement | null>>([]);

  const toggle = (index: number) =>
    setOpen((current) => {
      const next = new Set(current);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const last = items.length - 1;
    let target: number | null = null;
    if (event.key === "ArrowDown") target = index === last ? 0 : index + 1;
    else if (event.key === "ArrowUp") target = index === 0 ? last : index - 1;
    else if (event.key === "Home") target = 0;
    else if (event.key === "End") target = last;
    if (target === null) return;
    event.preventDefault();
    buttons.current[target]?.focus();
  };

  return (
    <ul className="lp-faq__list">
      {items.map((item, index) => {
        const isOpen = open.has(index);
        const buttonId = `${baseId}-q${index}`;
        const panelId = `${baseId}-a${index}`;
        return (
          <li key={item.question} className="lp-faq__item" data-open={isOpen}>
            <h3 className="lp-faq__heading">
              <button
                ref={(node) => {
                  buttons.current[index] = node;
                }}
                id={buttonId}
                type="button"
                className="lp-faq__trigger"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => toggle(index)}
                onKeyDown={(event) => onKeyDown(event, index)}
              >
                <span className="lp-faq__index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="lp-faq__question">{item.question}</span>
                <span className="lp-faq__icon" aria-hidden="true" />
              </button>
            </h3>
            <div id={panelId} role="region" aria-labelledby={buttonId} className="lp-faq__panel" data-open={isOpen}>
              <div className="lp-faq__panel-inner">
                <p className="lp-faq__answer">{item.answer}</p>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
