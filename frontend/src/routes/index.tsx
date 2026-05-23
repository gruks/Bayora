import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Footer } from "@/components/Footer";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "CENTINELA — Independent AI Safety Audits" },
      {
        name: "description",
        content:
          "Adversarial red-team audits with signed, tamper-proof certificates for HIPAA, SOX, GDPR, and EU AI Act compliance.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-[#0A0B0D] text-[#F1F5F9]">
      <Navbar />
      <Hero />
      <HowItWorks />
      <Pricing />
      <Footer />
    </div>
  );
}

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 h-14 flex items-center px-8 backdrop-blur-md transition-colors ${
        scrolled ? "border-b border-[#2A2D35]" : ""
      }`}
      style={{ backgroundColor: "rgba(10,11,13,0.9)" }}
    >
      <Link to="/" className="flex items-center gap-2">
        <span className="material-symbols-outlined text-[#3B82F6]">shield</span>
        <span className="font-bold tracking-tight">CENTINELA</span>
      </Link>
      <nav className="ml-auto flex items-center gap-6 text-sm">
        <a href="#how" className="text-[#94A3B8] hover:text-white transition-colors">
          How It Works
        </a>
        <a href="#pricing" className="text-[#94A3B8] hover:text-white transition-colors">
          Pricing
        </a>
        <Link
          to="/login"
          className="px-4 py-2 rounded-lg border border-white/80 text-white text-sm hover:bg-white/5 transition-colors"
        >
          Log In
        </Link>
        <Link
          to="/login"
          className="px-4 py-2 rounded-lg bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm transition-colors"
        >
          Get Started
        </Link>
      </nav>
    </header>
  );
}

function Hero() {
  return (
    <section
      className="min-h-screen flex items-center px-8 pt-14"
      style={{
        background:
          "radial-gradient(ellipse 80% 50% at 50% 40%, rgba(59,130,246,0.07) 0%, transparent 70%), #0A0B0D",
      }}
    >
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-20 items-center w-full">
        <div>
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#2A2D35] text-[#3B82F6] text-xs font-medium mb-6">
            🛡 AI Safety Infrastructure
          </span>
          <h1 className="text-[48px] leading-[1.05] font-bold text-white tracking-tight">
            Independent AI Safety
            <br />
            Audits. Forensically{" "}
            <span className="text-[#3B82F6]">Certified.</span>
          </h1>
          <p className="mt-6 text-[18px] text-[#94A3B8] max-w-[480px]">
            CENTINELA runs adversarial red-team attacks against any AI deployment and produces
            signed, tamper-proof certificates that satisfy HIPAA, SOX, GDPR, and the EU AI Act.
          </p>
          <div className="mt-8 flex gap-4 flex-wrap">
            <Link
              to="/config"
              className="px-6 py-3 rounded-lg bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-medium transition-colors"
            >
              Start Free Audit →
            </Link>
            <a
              href="#"
              className="px-6 py-3 rounded-lg border border-[#2A2D35] text-white hover:bg-white/5 transition-colors"
            >
              View Sample Certificate
            </a>
          </div>
          <div className="mt-8 flex flex-wrap gap-6 text-[13px] text-[#94A3B8]">
            {[
              "Provider agnostic",
              "Ed25519 signed certificates",
              "Merkle-chained audit logs",
            ].map((t) => (
              <span key={t} className="flex items-center gap-2">
                <span className="material-symbols-outlined text-emerald-400 text-[16px]">
                  check
                </span>
                {t}
              </span>
            ))}
          </div>
        </div>
        <div
          className="rounded-xl border border-[#2A2D35] overflow-hidden bg-[#111318]"
          style={{
            boxShadow: "0 0 80px rgba(59,130,246,0.12)",
            animation: "floaty 4s ease-in-out infinite",
          }}
        >
          <div className="aspect-[3/2] flex items-center justify-center border border-dashed border-[#2A2D35] m-4 rounded-lg">
            <span className="text-[#475569] text-sm">Dashboard Preview</span>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes floaty {
          0%,100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      icon: "settings",
      title: "Configure",
      desc: "Define your target model, domain profile, and attack budget in under 2 minutes.",
    },
    {
      icon: "bolt",
      title: "Attack",
      desc: "CENTINELA fires adaptive adversarial prompts and records every response in a Merkle-chained audit log.",
    },
    {
      icon: "verified_user",
      title: "Certify",
      desc: "Download your Ed25519-signed PDF certificate, ready for compliance submission.",
    },
  ];
  return (
    <section id="how" className="py-24 px-8 bg-[#0A0B0D]">
      <div className="max-w-6xl mx-auto">
        <p className="text-[#3B82F6] uppercase text-xs tracking-widest font-semibold">
          How It Works
        </p>
        <h2 className="text-[36px] text-white font-bold mt-2 mb-12">
          From configuration to certificate in minutes
        </h2>
        <div className="relative grid md:grid-cols-3 gap-8">
          <div className="hidden md:block absolute top-12 left-[16%] right-[16%] border-t border-dashed border-[#2A2D35]" />
          {steps.map((s, i) => (
            <div
              key={s.title}
              className="relative bg-[#111318] rounded-xl border border-[#2A2D35] p-8"
            >
              <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#3B82F6] text-white text-sm font-bold flex items-center justify-center">
                {i + 1}
              </div>
              <span className="material-symbols-outlined text-[#3B82F6] text-[32px]">
                {s.icon}
              </span>
              <h3 className="text-white font-semibold text-lg mt-4 mb-2">{s.title}</h3>
              <p className="text-[#94A3B8] text-sm leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  const tiers = [
    {
      name: "Free",
      price: "$0",
      cadence: "/ month",
      sub: "For evaluation",
      features: [
        "3 audits per month",
        "Up to 50 attacks per audit",
        "General domain profile only",
        "PDF certificate (watermarked)",
        "Community support",
      ],
      cta: "Get Started Free",
      highlight: false,
    },
    {
      name: "Pro",
      price: "$99",
      cadence: "/ month",
      sub: "For compliance teams",
      features: [
        "Unlimited audits",
        "Up to 500 attacks per audit",
        "All domain profiles (Healthcare, Finance, Legal)",
        "Signed PDF certificates (no watermark)",
        "Merkle audit log export",
        "Priority support",
      ],
      cta: "Start Pro Trial",
      highlight: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      cadence: "",
      sub: "For regulated industries",
      features: [
        "Everything in Pro",
        "Custom attack profiles",
        "On-premise deployment",
        "SOC 2 Type II report",
        "Dedicated audit environment",
        "SLA + compliance consulting",
      ],
      cta: "Contact Sales",
      highlight: false,
    },
  ];
  return (
    <section id="pricing" className="py-24 px-8 bg-[#0A0B0D]">
      <div className="max-w-6xl mx-auto">
        <p className="text-[#3B82F6] uppercase text-xs tracking-widest font-semibold">
          Pricing
        </p>
        <h2 className="text-[36px] text-white font-bold mt-2">
          Simple, transparent pricing
        </h2>
        <p className="text-[#94A3B8] mt-2 mb-12">
          Start free. Scale as your compliance needs grow.
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {tiers.map((t) => (
            <div
              key={t.name}
              className={`relative rounded-xl p-8 bg-[#111318] border ${
                t.highlight ? "border-[#3B82F6]" : "border-[#2A2D35]"
              }`}
              style={
                t.highlight
                  ? { background: "linear-gradient(180deg, rgba(59,130,246,0.08), #111318)" }
                  : undefined
              }
            >
              {t.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-[#3B82F6] text-white text-xs font-semibold">
                  MOST POPULAR
                </span>
              )}
              <h3 className="text-white text-xl font-semibold">{t.name}</h3>
              <p className="text-[#94A3B8] text-sm mt-1">{t.sub}</p>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-white text-[36px] font-bold">{t.price}</span>
                <span className="text-[#94A3B8] text-sm">{t.cadence}</span>
              </div>
              <ul className="mt-6 space-y-3">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[#94A3B8]">
                    <span className="material-symbols-outlined text-emerald-400 text-[18px] mt-0.5">
                      check
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                to="/login"
                className={`mt-8 block text-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  t.highlight
                    ? "bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white"
                    : "border border-[#2A2D35] text-white hover:bg-white/5"
                }`}
              >
                {t.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}