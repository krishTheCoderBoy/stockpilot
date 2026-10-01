import { useNavigate } from "react-router-dom";
import Spline from "@splinetool/react-spline";
import { motion } from "motion/react";
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

const FEATURES = [
  { icon: ShieldCheck, title: "Role-based access", desc: "Admins, inventory managers, and procurement managers each see and do only what their role allows." },
  { icon: GitBranch, title: "Controlled workflows", desc: "Purchase orders follow a fixed approval path — no arbitrary status jumps, ever." },
  { icon: LineChart, title: "Built for reporting", desc: "Every ledger entry is structured for analysis — from a low-stock alert today to a demand forecast later." },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen overflow-hidden bg-ink">
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10"
      >
        <span className="font-mono text-lg text-accent">StockPilot</span>
        <button
          onClick={() => navigate("/login")}
          className="rounded-sm border border-border px-4 py-1.5 text-sm text-text-muted transition-colors hover:border-accent/50 hover:text-text"
        >
          Sign in
        </button>
      </motion.header>

      <section className="relative min-h-[calc(100svh-72px)] overflow-hidden">
        <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
          <div className="spline-scene absolute inset-0 h-full w-full">
            <Spline scene="https://prod.spline.design/ZLmCjV-qSuJhGi8t/scene.splinecode" />
          </div>
        </div>
        <div
          className="pointer-events-none absolute inset-0 z-[1]"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,13,18,0.32) 0%, rgba(10,13,18,0.42) 48%, rgba(10,13,18,0.82) 100%)",
          }}
        />
        <motion.div
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="relative z-10 mx-auto max-w-3xl px-6 pb-12 pt-14 text-center sm:pt-20"
        >
          <h1 className="text-3xl font-bold leading-[1.1] tracking-tight text-white [text-shadow:0_3px_24px_rgba(3,16,29,0.9)] sm:text-5xl">
            Know exactly what's
            <br />
            <span className="bg-gradient-to-r from-amber-200 via-yellow-300 to-orange-300 bg-clip-text text-transparent [text-shadow:none]">
              in stock, where it is,
            </span>
            <br />
            and what to order next.
          </h1>
          <p className="mx-auto mt-5 max-w-lg rounded-lg border border-white/15 bg-slate-950/35 px-4 py-3 text-sm leading-relaxed text-white shadow-lg shadow-slate-950/20 backdrop-blur-sm sm:text-base">
            StockPilot brings inventory, warehouses, and procurement into one operating
            system — built for teams who need a clear, auditable record of every unit
            that moves.
          </p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <Button onClick={() => navigate("/login")} className="px-6 py-3 text-base">
              Get started
            </Button>
            <button
              onClick={() => navigate("/login")}
              className="px-6 py-3 text-sm font-medium text-white transition-colors hover:text-amber-200"
            >
              Sign in
            </button>
          </div>
        </motion.div>

      </section>

      <section className="mx-auto max-w-5xl px-6 py-16">
        <p className="mb-6 text-center text-sm text-text-muted">
          One system covering every stage of inventory and procurement
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {MODULES.map(({ icon: Icon, label }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
              whileHover={{ y: -3, borderColor: "rgba(217,164,65,0.5)" }}
              className="flex flex-col items-center gap-2 rounded-md border border-border bg-surface px-4 py-5 text-center transition-colors"
            >
              <Icon size={18} className="text-accent" />
              <span className="text-xs text-text-muted">{label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-16">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          {STEPS.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            >
              <span className="font-mono text-xs text-accent">{`0${i + 1}`}</span>
              <h3 className="mt-2 text-base font-medium text-text">{step.title}</h3>
              <p className="mt-2 text-sm text-text-muted">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-y border-border bg-surface">
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-8 px-6 py-14 text-center sm:grid-cols-3">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
            >
              <p className="font-mono text-3xl text-accent">{stat.value}</p>
              <p className="mt-1 text-sm text-text-muted">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-16">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              whileHover={{ y: -4 }}
              className="rounded-md border border-border bg-surface p-5 transition-transform"
            >
              <Icon size={20} className="text-accent" />
              <h3 className="mt-3 text-sm font-medium text-text">{title}</h3>
              <p className="mt-1 text-sm text-text-muted">{desc}</p>
            </motion.div>
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
