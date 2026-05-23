import { Link } from "@tanstack/react-router";

export function Footer() {
  return (
    <footer className="bg-[#0A0B0D] border-t border-[#2A2D35] pt-12 pb-8 px-8">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="material-symbols-outlined text-[#3B82F6]">shield</span>
            <span className="font-bold text-white tracking-tight">CENTINELA</span>
          </div>
          <p className="text-sm text-[#94A3B8]">
            Forensically auditable AI safety validation.
          </p>
        </div>
        <FooterCol
          title="Product"
          links={[
            { label: "Configure", to: "/config" },
            { label: "Live Audit", to: "/audit" },
            { label: "Results", to: "/results" },
            { label: "Sample Certificate", href: "#" },
          ]}
        />
        <FooterCol
          title="Compliance"
          links={[
            { label: "HIPAA", href: "#" },
            { label: "SOX", href: "#" },
            { label: "GDPR", href: "#" },
            { label: "EU AI Act", href: "#" },
          ]}
        />
        <FooterCol
          title="Company"
          links={[
            { label: "About", href: "#" },
            { label: "Pricing", href: "/#pricing" },
            { label: "Contact", href: "#" },
            { label: "Privacy Policy", href: "#" },
          ]}
        />
      </div>
      <div className="max-w-6xl mx-auto mt-10 pt-6 border-t border-[#2A2D35] flex flex-col md:flex-row justify-between text-[13px] text-[#475569]">
        <span>© 2025 CENTINELA. Built for Bayora Hackathon.</span>
        <span>Made with ♥ for AI Safety</span>
      </div>
    </footer>
  );
}

type LinkItem = { label: string; to?: string; href?: string };

function FooterCol({ title, links }: { title: string; links: LinkItem[] }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-white mb-3">{title}</h4>
      <ul className="space-y-2 text-sm text-[#94A3B8]">
        {links.map((l) => (
          <li key={l.label}>
            {l.to ? (
              <Link to={l.to} className="hover:text-white transition-colors">
                {l.label}
              </Link>
            ) : (
              <a href={l.href} className="hover:text-white transition-colors">
                {l.label}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}