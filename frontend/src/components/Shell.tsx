import { Link, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";

const navItems = [
  { to: "/", icon: "settings", label: "Configure" },
  { to: "/live", icon: "security_update_good", label: "Live Audit" },
  { to: "/results", icon: "analytics", label: "Results" },
] as const;

interface ShellProps {
  children: ReactNode;
  topBar?: ReactNode;
  footer?: ReactNode;
  sidebarFooter?: ReactNode;
}

export function Shell({ children, topBar, footer, sidebarFooter }: ShellProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="min-h-screen bg-[#0A0B0D] text-[#e2e2e9]">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-[240px] flex flex-col py-6 border-r border-[#424754] bg-[#111318] z-40">
        <div className="px-4 mb-8">
          <h1 className="text-xl font-bold tracking-tight">CENTINELA</h1>
          <p className="text-[12px] font-semibold tracking-[0.05em] text-[#c2c6d6] mt-1 opacity-80">
            Security Audit v2.4
          </p>
        </div>

        <nav className="flex-grow space-y-1 px-2">
          {navItems.map((item) => {
            const active = pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={
                  "flex items-center gap-4 px-4 py-2 rounded transition-colors duration-200 " +
                  (active
                    ? "bg-[#4f319c] text-[#bea8ff] border-l-4 border-[#adc6ff]"
                    : "text-[#c2c6d6] hover:text-[#e2e2e9] hover:bg-[#282a2f]")
                }
              >
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span className="text-sm">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto px-3 pt-4 border-t border-[#424754]/40">
          {sidebarFooter ?? (
            <div className="flex items-center gap-2 px-4 py-2 rounded bg-[#282a2f] mb-4">
              <span
                className="material-symbols-outlined text-[#adc6ff] text-[20px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                verified
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#adc6ff]">
                Live Audit Active
              </span>
            </div>
          )}
          <a
            href="#"
            className="flex items-center gap-4 px-4 py-2 text-[#c2c6d6] hover:text-[#e2e2e9] transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">biotech</span>
            <span className="text-sm">Demo Mode</span>
          </a>
        </div>
      </aside>

      {/* Topbar */}
      <header className="fixed top-0 left-[240px] right-0 flex justify-between items-center px-6 h-[48px] bg-[#1e2025] border-b border-[#424754] z-30">
        {topBar ?? (
          <div className="flex items-center gap-4">
            <span className="text-[13px] font-mono text-[#adc6ff]">SESSION_ID: AX-772</span>
          </div>
        )}
        <div className="flex items-center gap-4">
          {["notifications", "help", "account_circle"].map((i) => (
            <span
              key={i}
              className="material-symbols-outlined text-[#c2c6d6] cursor-pointer hover:bg-[#33353a] p-1 rounded transition-colors text-[20px]"
            >
              {i}
            </span>
          ))}
        </div>
      </header>

      {/* Main */}
      <main className="ml-[240px] pt-[48px] min-h-screen bg-[#111318] relative">
        <div className="p-6 pb-32">{children}</div>
      </main>

      {footer}

      {/* Ambient bg */}
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-[#adc6ff]/5 rounded-full blur-[120px] pointer-events-none -z-0" />
      <div className="fixed bottom-0 left-[240px] w-[300px] h-[300px] bg-[#4f319c]/10 rounded-full blur-[80px] pointer-events-none -z-0" />
    </div>
  );
}