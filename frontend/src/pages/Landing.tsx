import { useNavigate } from "react-router-dom";
import { Package, Boxes, ClipboardList, ArrowRight } from "lucide-react";
import { Button } from "../components/ui/Button";

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-ink">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <span className="font-mono text-lg text-accent">StockPilot</span>
        <div className="flex items-center gap-3">
          <button onClick={() => navigate("/login")} className="text-sm text-text-muted hover:text-text">
            Sign in
          </button>
        </div>
      </header>

      <main className="mx-auto flex max-w-3xl flex-col items-center px-6 pt-20 text-center sm:pt-32">
        <h1 className="text-3xl font-medium leading-tight text-text sm:text-4xl">
          Know exactly what's in stock,<br />where it is, and what to order next.
        </h1>
        <p className="mt-4 max-w-xl text-text-muted">
          StockPilot brings inventory, warehouses, and procurement into one operating system —
          built for teams who need a clear, auditable record of every unit that moves.
        </p>
        <Button onClick={() => navigate("/login")} className="mt-8 px-6 py-3 text-base">
          Get started <ArrowRight size={16} />
        </Button>
      </main>

      <section className="mx-auto mt-24 grid max-w-4xl grid-cols-1 gap-4 px-6 pb-24 sm:grid-cols-3">
        {[
          { icon: Package, title: "Products & Stock", desc: "Track quantity, cost, and reorder points across every warehouse." },
          { icon: Boxes, title: "Movement Ledger", desc: "Every change is recorded — receive, issue, transfer, or adjust, never silent." },
          { icon: ClipboardList, title: "Purchase Orders", desc: "A controlled approval flow from draft through receiving." },
        ].map(({ icon: Icon, title, desc }) => (
          <div key={title} className="rounded-md border border-border bg-surface p-5">
            <Icon size={20} className="text-accent" />
            <h3 className="mt-3 text-sm font-medium text-text">{title}</h3>
            <p className="mt-1 text-sm text-text-muted">{desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}