import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "CENTINELA — Create Account" },
      { name: "description", content: "Create a new CENTINELA account." },
    ],
  }),
  component: SignupPage,
});

function SignupPage() {
  const navigate = useNavigate();

  return (
    <div
      style={{ fontFamily: "'Lato', 'Slack-Lato', appleLogo, sans-serif" }}
      className="h-screen overflow-hidden bg-[#0A0B0D] text-[#F1F5F9] flex flex-col"
    >
      {/* Header — centered logo like Slack */}
      <header className="flex items-center justify-center py-6 px-4">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-[#3B82F6] flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="text-[22px] font-black tracking-widest text-[#F1F5F9] uppercase">
            CENTINELA
          </span>
        </Link>
      </header>

      {/* Main content — Slack-style centered narrow column */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 overflow-hidden">
        <div className="w-full max-w-[520px] ">

          {/* Heading */}
          <h1 className="text-[28px] sm:text-[45px] font-bold text-[#F1F5F9] text-center leading-tight mb-2">
            First, enter your email
          </h1>
          <p className="text-center text-[#94A3B8] text-[15px] mb-8">
            We suggest using the{" "}
            <strong className="text-[#F1F5F9] font-semibold">
              email address you use at work.
            </strong>
          </p>

          {/* Email form */}
          <form
            className="flex flex-col gap-3 max-w-sm mx-auto"
            onSubmit={(e) => {
              e.preventDefault();
              navigate({ to: "/config" });
            }}
          >
            <label className="sr-only" htmlFor="login_email">
              Email address
            </label>
            <input
              id="login_email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="name@work-email.com"
              className="
                w-full h-[45px] px-4 rounded-lg
                bg-[#111318] border border-[#2A2D35]
                text-[#F1F5F9] placeholder:text-[#475569]
                text-[16px]
                focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]
                transition-colors
              "
            />
            <button
              type="submit"
              className="
                w-full h-[45px] rounded-lg
                bg-[#3B82F6] hover:bg-[#1D4ED8]
                text-white font-bold text-[16px]
                transition-colors duration-150
              "
            >
              Sign In with Email
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6 max-w-sm mx-auto">
            <span className="flex-1 h-px bg-[#2A2D35]" />
            <span className="text-xs font-semibold text-[#475569] tracking-widest">OR</span>
            <span className="flex-1 h-px bg-[#2A2D35]" />
          </div>

          {/* OAuth buttons */}
          <div className="flex flex-row gap-3 max-w-sm mx-auto">
            <button
              type="button"
              className="
                w-full h-[45px] rounded-lg
                border border-[#2A2D35] bg-[#111318]
                hover:bg-[#1A1D24] hover:border-[#3D4250]
                text-[#F1F5F9] text-[15px] font-semibold
                flex items-center justify-center gap-3
                transition-colors duration-150
              "
            >
              <svg width="20" height="20" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 9.5C27.54 9.5 30.71 10.72 33.21 13.1L40.06 6.25C35.9 2.38 30.47 0 24 0C14.62 0 6.51 5.38 2.56 13.22L10.54 19.41C12.43 13.72 17.74 9.5 24 9.5Z" fill="#EA4335" />
                <path d="M46.98 24.55C46.98 22.98 46.83 21.46 46.6 19.99H24V29.01H36.94C36.36 31.97 34.68 34.49 32.16 36.19L39.89 42.19C44.4 38.01 47 31.83 47 24.55Z" fill="#4285F4" />
                <path d="M10.53 28.59C10.05 27.14 9.77 25.6 9.77 24C9.77 22.86 9.98 21.72 10.39 20.65L2.41 14.46C0.92 16.46 0 20.12 0 24C0 27.88 0.92 31.54 2.56 34.78L10.54 28.59H10.53Z" fill="#FBBC05" />
                <path d="M24 48C30.48 48 35.93 45.87 39.89 42.19L32.16 36.19C29.99 37.64 27.22 38.49 24 38.49C17.74 38.49 12.43 34.27 10.53 28.58L2.56 34.77C6.51 42.62 14.62 48 24 48Z" fill="#34A853" />
              </svg>
              <span>Google</span>
            </button>

            <button
              type="button"
              className="
                w-full h-[45px] rounded-lg
                border border-[#2A2D35] bg-[#111318]
                hover:bg-[#1A1D24] hover:border-[#3D4250]
                text-[#F1F5F9] text-[15px] font-semibold
                flex items-center justify-center gap-3
                transition-colors duration-150
              "
            >
              <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.16 0C7.8 0.56 6.9 2.1 6.86 4.14C7.76 4.06 8.27 3.96 8.99 3.23C9.84 2.37 10.22 1.26 10.22 0.43C10.22 0.22 10.2 0.13 10.16 0Z" fill="#F1F5F9" />
                <path d="M10.33 3.84C9.86 3.84 9.28 3.95 8.59 4.19C7.94 4.42 7.46 4.54 7.16 4.54C6.92 4.54 6.46 4.43 5.77 4.23C5.07 4.03 4.47 3.92 3.99 3.92C1.69 3.92 0 6.11 0 9.22C0 10.86 0.49 12.58 1.48 14.35C2.47 16.12 3.49 17 4.5 17C4.84 17 5.29 16.89 5.83 16.65C6.36 16.41 6.84 16.32 7.26 16.32C7.69 16.32 8.2 16.43 8.77 16.64C9.39 16.87 9.85 17 10.18 17C11.9 17 13.48 14.12 14 12.41C12.8 12.05 11.72 10.53 11.72 8.85C11.72 7.3 12.46 6.44 13.52 5.53C12.82 4.66 11.93 3.84 10.33 3.84Z" fill="#F1F5F9" />
              </svg>
              <span>Apple</span>
            </button>
          </div>

          {/* Terms */}
          <p className="mt-6 text-center text-[13px] text-[#475569] leading-relaxed max-w-sm mx-auto">
            By continuing, you're agreeing to our{" "}
            <a href="/legal" className="text-[#3B82F6] hover:text-[#1D4ED8] hover:underline">
              Main Services Agreement
            </a>
            ,{" "}
            <a href="/terms" className="text-[#3B82F6] hover:text-[#1D4ED8] hover:underline">
              User Terms of Service
            </a>
            , and{" "}
            <a href="/supplemental-terms" className="text-[#3B82F6] hover:text-[#1D4ED8] hover:underline">
              Supplemental Terms
            </a>
            . Additional disclosures are available in our{" "}
            <a href="/privacy-policy" className="text-[#3B82F6] hover:text-[#1D4ED8] hover:underline">
              Privacy Policy
            </a>{" "}
            and{" "}
            <a href="/cookie-policy" className="text-[#3B82F6] hover:text-[#1D4ED8] hover:underline">
              Cookie Policy
            </a>
            .
          </p>

          {/* Sign up CTA — Slack style */}
          <div className="mt-10 pt-6 border-t border-[#2A2D35] text-center max-w-sm mx-auto">
            <div className="flex flex-wrap items-center justify-center gap-2">
              <p className="text-[#94A3B8] text-[14px] font-semibold mb-0">
                Already have an account?
              </p>
              <Link
                to="/login"
                className="text-[#3B82F6] hover:text-[#1D4ED8] text-[15px] font-semibold hover:underline"
              >
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 px-4">
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[13px] text-[#475569]">
          <a href="/legal" className="hover:text-[#94A3B8] transition-colors">
            Privacy &amp; Terms
          </a>
          <a href="/help" className="hover:text-[#94A3B8] transition-colors">
            Contact Us
          </a>
          <a href="#" className="hover:text-[#94A3B8] transition-colors flex items-center gap-1">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            Change region
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </a>
        </div>
      </footer>
    </div>
  );
}