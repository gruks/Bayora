import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Shell } from "@/components/Shell";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "CENTINELA — Results & Certification" },
      { name: "description", content: "Review audit results, attack log and download the signed safety certificate." },
    ],
  }),
  component: Results,
});

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
const attacks: { vec: string; sev: Severity; result: string; ts: string }[] = [
  { vec: "LLM_INJECTION_PROMPT_v4", sev: "CRITICAL", result: "REJECTED", ts: "12:04:11.02" },
  { vec: "SENSITIVE_DATA_EXFIL", sev: "HIGH", result: "BLOCKED", ts: "12:05:22.45" },
  { vec: "ADVERSARIAL_SUFFIX_GEN", sev: "MEDIUM", result: "REJECTED", ts: "12:07:01.89" },
  { vec: "RBAC_BYPASS_ATTEMPT_7", sev: "CRITICAL", result: "DEFLECTED", ts: "12:10:44.33" },
  { vec: "XSS_INLINE_STYLING_AI", sev: "MEDIUM", result: "SCRUBBED", ts: "12:12:19.00" },
  { vec: "PII_LEAK_MASKING_TEST", sev: "LOW", result: "VERIFIED", ts: "12:15:00.12" },
];

const sevStyles: Record<Severity, string> = {
  CRITICAL: "bg-[#EF4444]/20 text-[#EF4444]",
  HIGH: "bg-[#F97316]/20 text-[#F97316]",
  MEDIUM: "bg-[#EAB308]/20 text-[#EAB308]",
  LOW: "bg-[#22C55E]/20 text-[#22C55E]",
};

function Results() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <Shell
      topBar={
        <div className="flex items-center gap-4">
          <span className="text-[13px] font-mono text-[#c2c6d6]">NODE: 0x82...F3A</span>
          <span className="h-4 w-px bg-[#424754]" />
          <span className="text-[13px] font-mono text-[#adc6ff]">STATUS: AUDIT_COMPLETE</span>
        </div>
      }
      sidebarFooter={
        <div className="px-4 py-2 bg-[#4d8eff]/10 rounded mb-4">
          <div className="flex items-center gap-2 text-[#adc6ff] mb-1">
            <span className="material-symbols-outlined text-[18px]">verified</span>
            <span className="text-[12px] font-semibold tracking-[0.05em]">Audit Finalized</span>
          </div>
          <button
            onClick={() => setDrawerOpen(true)}
            className="text-[13px] text-[#e2e2e9] hover:underline cursor-pointer"
          >
            View History Deltas
          </button>
        </div>
      }
    >
      <div className="relative z-10">
        {/* Summary header */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="md:col-span-2 glass-panel p-6 rounded-xl flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[12px] font-semibold uppercase tracking-widest text-[#c2c6d6]">
                  Audit Session
                </span>
                <span className="font-mono text-[#adc6ff] text-[13px]">#CN-2023-99128</span>
              </div>
              <h2 className="text-[32px] leading-[40px] font-bold tracking-tight">
                Aegis Dynamics Cloud
              </h2>
              <p className="text-sm text-[#c2c6d6] mt-1">
                Organization Level: Enterprise Tier Security
              </p>
            </div>
            <div className="flex flex-col items-end gap-4">
              <div className="bg-[#adc6ff]/10 text-[#adc6ff] border border-[#adc6ff] px-4 py-2 rounded-full flex items-center gap-2">
                <span
                  className="material-symbols-outlined text-[20px]"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  check_circle
                </span>
                <span className="font-bold tracking-tight">CERTIFIED</span>
              </div>
              <div className="text-right">
                <span className="text-[12px] font-semibold tracking-[0.05em] text-[#c2c6d6] block">
                  COMPLIANCE WINDOW
                </span>
                <span className="text-[13px] font-mono">EXP: 12 OCT 2024</span>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-xl flex flex-col justify-center items-center text-center">
            <span className="text-[12px] font-semibold tracking-[0.05em] text-[#c2c6d6] mb-1">
              SAFETY SCORE
            </span>
            <div className="relative h-24 w-24 flex items-center justify-center">
              <svg className="absolute inset-0 -rotate-90" viewBox="0 0 96 96">
                <circle cx="48" cy="48" fill="transparent" r="44" stroke="#1A1D24" strokeWidth="8" />
                <circle
                  cx="48"
                  cy="48"
                  fill="transparent"
                  r="44"
                  stroke="#3B82F6"
                  strokeDasharray="276"
                  strokeDashoffset="14"
                  strokeWidth="8"
                />
              </svg>
              <span className="text-[32px] font-bold">95</span>
            </div>
            <span className="text-[13px] text-[#adc6ff] mt-2">+3.2% from prev.</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <StatCard
            icon="bolt"
            iconBg="bg-[#33353a]"
            iconColor="text-[#adc6ff]"
            value="1,248"
            label="ATTACKS EXECUTED"
          />
          <StatCard
            icon="gpp_maybe"
            iconBg="bg-[#ffb4ab]/10"
            iconColor="text-[#ffb4ab]"
            value="0"
            valueColor="text-[#ffb4ab]"
            label="FAILURES DETECTED"
          />
          <StatCard
            icon="draw"
            iconBg="bg-[#df7412]/20"
            iconColor="text-[#ffb786]"
            value="SIGNED"
            valueColor="text-[#ffb786]"
            label="CERTIFICATE STATUS"
          />
        </div>

        {/* Two columns */}
        <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
          {/* Attack log */}
          <div className="lg:col-span-6 glass-panel rounded-xl flex flex-col overflow-hidden">
            <div className="p-4 border-b border-[#424754] flex items-center justify-between bg-[#282a2f]/30">
              <h3 className="text-base font-semibold">Attack Log</h3>
              <div className="flex gap-2">
                <div className="relative">
                  <input
                    placeholder="Filter..."
                    className="bg-[#111318] border border-[#424754] rounded px-2 py-1 pl-8 text-[13px] w-48 focus:border-[#adc6ff] outline-none"
                  />
                  <span className="material-symbols-outlined absolute left-2 top-1.5 text-[18px] opacity-50">
                    search
                  </span>
                </div>
                <button className="bg-[#33353a] hover:bg-[#37393f] text-[#e2e2e9] px-2 py-1 rounded text-[12px] font-semibold flex items-center gap-1 border border-[#424754]">
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  EXPORT CSV
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-[#1a1b21] border-b border-[#424754] text-[12px] font-semibold tracking-[0.05em] text-[#c2c6d6]">
                  <tr>
                    <th className="p-4">ATTACK VECTOR</th>
                    <th className="p-4">SEVERITY</th>
                    <th className="p-4">RESULT</th>
                    <th className="p-4">TIMESTAMP</th>
                  </tr>
                </thead>
                <tbody className="text-[13px]">
                  {attacks.map((a) => (
                    <tr
                      key={a.vec}
                      className="border-b border-[#424754] hover:bg-[#282a2f] transition-colors"
                    >
                      <td className="p-4 font-mono">{a.vec}</td>
                      <td className="p-4">
                        <span
                          className={
                            "px-2 py-1 rounded text-[10px] font-bold uppercase " + sevStyles[a.sev]
                          }
                        >
                          {a.sev}
                        </span>
                      </td>
                      <td className="p-4 text-[#adc6ff] font-medium">{a.result}</td>
                      <td className="p-4 text-[#c2c6d6]">{a.ts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Certificate */}
          <div className="lg:col-span-4 glass-panel rounded-xl overflow-hidden flex flex-col">
            <div className="bg-[#111318] p-6 flex-1 relative border-b border-[#424754] overflow-hidden group">
              <div
                className="absolute inset-0 opacity-10 pointer-events-none"
                style={{
                  backgroundImage: "radial-gradient(#3B82F6 1px, transparent 1px)",
                  backgroundSize: "20px 20px",
                }}
              />
              <div className="relative z-10 border border-[#424754]/30 p-4 h-full bg-[#1a1b21] flex flex-col items-center">
                <div className="w-full flex justify-between items-start mb-6">
                  <span className="text-[10px] font-mono text-[#c2c6d6]">ID: 882-990-AX</span>
                  <div className="text-right">
                    <div className="text-[8px] text-[#c2c6d6]">TIMESTAMP</div>
                    <div className="text-[10px] font-mono">2023-10-12T14:30Z</div>
                  </div>
                </div>
                <div className="mb-4 text-center">
                  <h4 className="text-base font-bold tracking-tight text-[#adc6ff]">
                    CENTINELA SAFETY SEAL
                  </h4>
                  <div className="h-[2px] w-12 bg-[#adc6ff] mx-auto mt-1" />
                </div>
                <p className="text-[10px] leading-relaxed text-[#c2c6d6] px-4 text-center mb-6">
                  This document certifies that the target system has undergone a rigorous
                  automated safety audit. All critical vectors were addressed and mitigated within
                  acceptable risk parameters defined in ISO/IEC 42001.
                </p>
                <div className="w-full mt-auto bg-[#111318]/50 p-2 border border-[#424754]/50 rounded flex flex-col gap-2">
                  <div>
                    <span className="text-[8px] font-bold text-[#c2c6d6]">
                      ED25519_DIGITAL_SIGNATURE
                    </span>
                    <div className="text-[9px] font-mono break-all leading-none opacity-60">
                      z3f8H2k9L1m...S8X0qP4w7Z1v6M2n9B8c7X
                    </div>
                  </div>
                  <div>
                    <span className="text-[8px] font-bold text-[#c2c6d6]">MERKLE_ROOT_HASH</span>
                    <div className="text-[9px] font-mono break-all leading-none text-[#adc6ff]">
                      0xae37f1b82d9910c4f83b27651a029c3d4f8e...
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-4 flex items-center gap-4 bg-[#1e2025]">
              <button className="flex-1 bg-[#adc6ff] text-[#002e6a] font-bold py-2 rounded flex items-center justify-center gap-2 hover:opacity-90 transition-opacity">
                <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
                DOWNLOAD PDF
              </button>
              <button className="bg-[#33353a] border border-[#424754] p-2 rounded text-[#e2e2e9] hover:text-[#adc6ff] transition-colors">
                <span className="material-symbols-outlined text-[20px]">content_copy</span>
              </button>
            </div>
          </div>
        </div>

        {/* Verification panel */}
        <div className="mt-6 glass-panel p-4 rounded-xl flex items-center justify-between border-dashed">
          <div className="flex items-center gap-4">
            <div className="bg-[#adc6ff]/10 p-2 rounded-full">
              <span className="material-symbols-outlined text-[#adc6ff]">gpp_good</span>
            </div>
            <div>
              <h4 className="text-base font-semibold">Verify Audit Integrity</h4>
              <p className="text-[13px] text-[#c2c6d6]">
                Input a Centinela Audit ID to check its current cryptographic validity on the
                ledger.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              placeholder="CN-XXXX-XXXXX"
              className="bg-[#1e2025] border border-[#424754] rounded px-4 py-2 font-mono text-[13px] w-64 focus:border-[#adc6ff] outline-none"
            />
            <button className="bg-[#adc6ff] text-[#002e6a] px-6 py-2 rounded font-bold hover:bg-[#d8e2ff] transition-colors">
              VERIFY
            </button>
          </div>
        </div>
      </div>

      {/* Drawer */}
      <div
        className={
          "fixed right-0 top-0 h-full w-[400px] bg-[#1a1b21] border-l border-[#424754] shadow-2xl z-[60] transition-transform duration-300 ease-in-out " +
          (drawerOpen ? "translate-x-0" : "translate-x-full")
        }
      >
        <div className="p-6 h-full flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-semibold">Audit Deltas</h3>
            <button
              onClick={() => setDrawerOpen(false)}
              className="material-symbols-outlined hover:bg-[#33353a] p-2 rounded-full"
            >
              close
            </button>
          </div>
          <div className="space-y-6 overflow-y-auto flex-1 pr-2">
            <div className="p-4 bg-[#282a2f] rounded border border-[#424754]">
              <div className="flex justify-between items-center mb-4">
                <span className="text-[12px] font-semibold tracking-[0.05em] text-[#c2c6d6]">
                  COMPARED SESSIONS
                </span>
                <span className="text-[10px] font-mono bg-[#adc6ff]/20 text-[#adc6ff] px-1 rounded">
                  v2.4 vs v2.3
                </span>
              </div>
              <div className="space-y-4">
                <DeltaRow label="Safety Score" from="91.8" to="95.0" up />
                <DeltaRow label="Vulnerabilities Found" from="12" to="0" down />
                <DeltaRow label="Response Latency" from="420ms" to="280ms" up arrow="arrow_downward" />
              </div>
            </div>
            <div>
              <h4 className="text-[12px] font-bold mb-4 text-[#c2c6d6] tracking-[0.05em]">
                KEY IMPROVEMENTS
              </h4>
              <div className="space-y-2">
                {[
                  "Resolved critical injection risk in the inference pipeline.",
                  "Enhanced rate limiting for recursive adversarial queries.",
                ].map((t) => (
                  <div key={t} className="flex items-start gap-2">
                    <span className="material-symbols-outlined text-[#adc6ff] text-[20px]">
                      check_circle
                    </span>
                    <p className="text-[13px]">{t}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-auto pt-6 border-t border-[#424754]">
            <button className="w-full border border-[#adc6ff] text-[#adc6ff] py-4 rounded font-bold hover:bg-[#adc6ff]/5 transition-colors">
              GENERATE DELTA REPORT
            </button>
          </div>
        </div>
      </div>
      {drawerOpen && (
        <div
          onClick={() => setDrawerOpen(false)}
          className="fixed inset-0 bg-black/40 z-50"
        />
      )}
    </Shell>
  );
}

function StatCard({
  icon,
  iconBg,
  iconColor,
  value,
  valueColor = "",
  label,
}: {
  icon: string;
  iconBg: string;
  iconColor: string;
  value: string;
  valueColor?: string;
  label: string;
}) {
  return (
    <div className="bg-[#1a1b21] border border-[#424754] p-4 rounded-lg flex items-center gap-4">
      <div className={iconBg + " p-2 rounded"}>
        <span className={"material-symbols-outlined " + iconColor}>{icon}</span>
      </div>
      <div>
        <div className={"text-base font-semibold " + valueColor}>{value}</div>
        <div className="text-[12px] font-semibold tracking-[0.05em] text-[#c2c6d6]">{label}</div>
      </div>
    </div>
  );
}

function DeltaRow({
  label,
  from,
  to,
  up,
  down,
  arrow = "arrow_forward",
}: {
  label: string;
  from: string;
  to: string;
  up?: boolean;
  down?: boolean;
  arrow?: string;
}) {
  const color = down ? "text-[#ffb4ab]" : up ? "text-[#adc6ff]" : "text-[#e2e2e9]";
  return (
    <div className="flex justify-between">
      <span className="text-[13px]">{label}</span>
      <div className="flex items-center gap-1">
        <span className="text-[#c2c6d6]">{from}</span>
        <span className={"material-symbols-outlined text-[14px] " + color}>{arrow}</span>
        <span className={"font-bold " + color}>{to}</span>
      </div>
    </div>
  );
}