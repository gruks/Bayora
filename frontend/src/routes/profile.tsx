import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Shell } from "@/components/Shell";

export const Route = createFileRoute("/profile")({
  head: () => ({
    meta: [
      { title: "CENTINELA — Profile" },
      { name: "description", content: "Manage your CENTINELA profile and audit history." },
    ],
  }),
  component: ProfilePage,
});

type Profile = {
  fullName: string;
  organization: string;
  role: string;
  email: string;
  bio: string;
};

const INITIAL: Profile = {
  fullName: "Sarah Chen",
  organization: "Northwind Health",
  role: "CISO",
  email: "sarah.chen@northwind.health",
  bio: "",
};

function ProfilePage() {
  const [profile, setProfile] = useState<Profile>(INITIAL);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Profile>(INITIAL);

  const initials = profile.fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <Shell>
      <div className="max-w-[720px] mx-auto space-y-6">
        {/* Top card */}
        <div className="bg-[#111318] border border-[#2A2D35] rounded-xl p-6 relative">
          <div className="flex items-start gap-5">
            <div className="relative group">
              <div className="w-20 h-20 rounded-full bg-[#3B82F6]/15 text-[#adc6ff] flex items-center justify-center text-2xl font-bold">
                {initials}
              </div>
              {editing && (
                <div className="absolute inset-0 rounded-full bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs cursor-pointer transition-opacity">
                  Upload
                </div>
              )}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white">{profile.fullName}</h1>
              <p className="text-[#94A3B8]">{profile.organization}</p>
              <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full border border-[#3B82F6]/50 text-[#3B82F6] text-xs">
                {profile.role}
              </span>
            </div>
            {!editing && (
              <button
                onClick={() => {
                  setDraft(profile);
                  setEditing(true);
                }}
                className="px-3 py-1.5 rounded-lg border border-[#2A2D35] text-white text-sm hover:bg-white/5 transition-colors"
              >
                Edit Profile
              </button>
            )}
          </div>

          {!editing ? (
            <div className="mt-8 grid grid-cols-2 gap-6">
              <Info label="Email" value={profile.email} />
              <Info label="Organization" value={profile.organization} />
              <Info label="Role / Title" value={profile.role} />
              <Info label="Member Since" value="May 2025" />
            </div>
          ) : (
            <form
              className="mt-8 space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                setProfile(draft);
                setEditing(false);
              }}
            >
              <FormField
                label="Full Name"
                value={draft.fullName}
                onChange={(v) => setDraft({ ...draft, fullName: v })}
              />
              <FormField
                label="Organization"
                value={draft.organization}
                onChange={(v) => setDraft({ ...draft, organization: v })}
              />
              <FormField
                label="Role / Title"
                value={draft.role}
                onChange={(v) => setDraft({ ...draft, role: v })}
              />
              <FormField
                label="Email"
                value={draft.email}
                onChange={(v) => setDraft({ ...draft, email: v })}
              />
              <div>
                <label className="block text-[13px] text-[#94A3B8] mb-1.5">Bio</label>
                <textarea
                  rows={3}
                  placeholder="Brief description for your certificate reports"
                  value={draft.bio}
                  onChange={(e) => setDraft({ ...draft, bio: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-[#0A0B0D] border border-[#2A2D35] text-[#F1F5F9] focus:border-[#3B82F6] focus:outline-none transition-colors"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-lg bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-medium"
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="px-5 py-2.5 rounded-lg border border-[#2A2D35] text-white text-sm hover:bg-white/5"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Audit History */}
        <div className="bg-[#111318] border border-[#2A2D35] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-semibold">Recent Audits</h2>
            <a href="#" className="text-[#3B82F6] text-sm hover:underline">
              View All
            </a>
          </div>
          <table className="w-full text-sm">
            <thead className="text-[#94A3B8] text-xs uppercase tracking-wider">
              <tr className="border-b border-[#2A2D35]">
                <th className="text-left py-2 font-medium">Audit ID</th>
                <th className="text-left py-2 font-medium">Domain</th>
                <th className="text-left py-2 font-medium">Score</th>
                <th className="text-left py-2 font-medium">Status</th>
                <th className="text-left py-2 font-medium">Date</th>
              </tr>
            </thead>
            <tbody className="text-[#F1F5F9]">
              {[
                { id: "AX-772", domain: "Healthcare", score: "95%", status: "Certified", date: "May 22, 2026" },
                { id: "AX-768", domain: "Finance", score: "88%", status: "Certified", date: "May 18, 2026" },
                { id: "AX-741", domain: "Legal", score: "72%", status: "Failed", date: "May 11, 2026" },
              ].map((a) => (
                <tr key={a.id} className="border-b border-[#2A2D35]/50">
                  <td className="py-3 font-mono text-[#A78BFA]">{a.id}</td>
                  <td>{a.domain}</td>
                  <td>{a.score}</td>
                  <td>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs ${
                        a.status === "Certified"
                          ? "bg-emerald-500/15 text-emerald-400"
                          : "bg-red-500/15 text-red-400"
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="text-[#94A3B8]">{a.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Security */}
        <div className="bg-[#111318] border border-[#2A2D35] rounded-xl p-6">
          <h2 className="text-white font-semibold mb-4">Security</h2>
          <div className="divide-y divide-[#2A2D35]">
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-white text-sm">Password</p>
                <p className="text-[#94A3B8] text-sm">••••••••</p>
              </div>
              <a href="#" className="text-[#3B82F6] text-sm hover:underline">
                Change
              </a>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-white text-sm">Two-Factor Auth</p>
                <p className="text-[#94A3B8] text-sm">Not enabled</p>
              </div>
              <a href="#" className="text-[#3B82F6] text-sm hover:underline">
                Enable
              </a>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[12px] uppercase tracking-wider text-[#94A3B8]">{label}</p>
      <p className="text-[15px] text-white mt-1">{value}</p>
    </div>
  );
}

function FormField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-[13px] text-[#94A3B8] mb-1.5">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-11 px-3 rounded-lg bg-[#0A0B0D] border border-[#2A2D35] text-[#F1F5F9] focus:border-[#3B82F6] focus:outline-none transition-colors"
      />
    </div>
  );
}