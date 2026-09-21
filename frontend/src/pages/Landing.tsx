import { useNavigate } from "react-router-dom";
import {
  Package,
  Warehouse,
  Boxes,
  ArrowLeftRight,
  Truck,
  ClipboardList,
  ArrowRight,
  ShieldCheck,
  GitBranch,
  LineChart,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import loginHero from "../assets/login-hero-2.png";

const MODULES = [
  { icon: Package, label: "Products" },
  { icon: Warehouse, label: "Warehouses" },
  { icon: Boxes, label: "Inventory" },
  { icon: ArrowLeftRight, label: "Movements" },
  { icon: Truck, label: "Suppliers" },
  { icon: ClipboardList, label: "Purchase Orders" },
];

const STEPS = [
  {
    title: "Record every movement",
    desc: "Receiving, issuing, transferring, or adjusting stock — each one writes to an immutable ledger, so you always know why a number changed.",
  },
  {
    title: "Approve with a real workflow",
    desc: "Purchase orders move through draft, approval, and receiving with role-based checks — no one status-hops around the process.",
  },
  {
    title: "See it on one dashboard",
    desc: "Inventory value, pending orders, and low-stock signals in one place, pulled straight from the same ledger your team works from.",
  },
];

const STATS = [
  { value: "100%", label: "Auditable movements" },
  { value: "3", label: "Role-based access tiers" },
  { value: "7", label: "State-machine PO stages" },
];

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-ink">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <span className="font-mono text-lg text-accent">StockPilot</span>
        <button
          onClick={() => navigate("/login")}
          className="rounded-sm border border-border px-4 py-1.5 text-sm text-text-muted transition-colors hover:border-accent/50 hover:text-text"
        >
          Sign in
        </button>
      </header>

      <section
        className="relative overflow-hidden"
        style={{
          backgroundImage: `linear-gradient(to bottom, rgba(10,13,18,0.35), rgba(10,13,18,0.96)), url(${loginHero})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="mx-auto max-w-3xl px-6 pb-28 pt-20 text-center sm:pt-32">
          <h1 className="text-4xl font-medium leading-tight text-text sm:text-5xl">
            Know exactly what's in stock,
            <br />
            where it is, and what to order next.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-text-muted">
            StockPilot brings inventory, warehouses, and procurement into one operating
            system — built for teams who need a clear, auditable record of every unit
            that moves.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Button onClick={() => navigate("/login")} className="px-6 py-3 text-base">
              Get started
            </Button>
            <button
              onClick={() => navigate("/login")}
              className="px-6 py-3 text-sm text-text-muted hover:text-text"
            >
              Sign in
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-16">
        <p className="mb-6 text-center text-sm text-text-muted">
          One system covering every stage of inventory and procurement
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {MODULES.map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex flex-col items-center gap-2 rounded-md border border-border bg-surface px-4 py-5 text-center"
            >
              <Icon size={18} className="text-accent" />
              <span className="text-xs text-text-muted">{label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-16">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          {STEPS.map((step, i) => (
            <div key={step.title}>
              <span className="font-mono text-xs text-accent">{`0${i + 1}`}</span>
              <h3 className="mt-2 text-base font-medium text-text">{step.title}</h3>
              <p className="mt-2 text-sm text-text-muted">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-border bg-surface">
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-8 px-6 py-14 text-center sm:grid-cols-3">
          {STATS.map((stat) => (
            <div key={stat.label}>
              <p className="font-mono text-3xl text-accent">{stat.value}</p>
              <p className="mt-1 text-sm text-text-muted">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-16">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            { icon: ShieldCheck, title: "Role-based access", desc: "Admins, inventory managers, and procurement managers each see and do only what their role allows." },
            { icon: GitBranch, title: "Controlled workflows", desc: "Purchase orders follow a fixed approval path — no arbitrary status jumps, ever." },
            { icon: LineChart, title: "Built for reporting", desc: "Every ledger entry is structured for analysis — from a low-stock alert today to a demand forecast later." },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="rounded-md border border-border bg-surface p-5">
              <Icon size={20} className="text-accent" />
              <h3 className="mt-3 text-sm font-medium text-text">{title}</h3>
              <p className="mt-1 text-sm text-text-muted">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-border px-6 py-10 text-center sm:px-10">
        <Button onClick={() => navigate("/login")} className="mx-auto px-6 py-3 text-base">
          Get started <ArrowRight size={16} />
        </Button>
        <p className="mt-6 text-xs text-text-muted">© {new Date().getFullYear()} StockPilot</p>
      </footer>
    </div>
  );
}