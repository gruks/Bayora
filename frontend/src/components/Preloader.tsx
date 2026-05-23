import { useEffect, useRef, useState } from "react";
import gsap from "gsap";

export function Preloader({ children }: { children: React.ReactNode }) {
  const [done, setDone] = useState(() => {
    if (typeof window === "undefined") return true;
    return sessionStorage.getItem("centinela_loaded") === "1";
  });
  const overlayRef = useRef<HTMLDivElement>(null);
  const wordRef = useRef<HTMLDivElement>(null);
  const barRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (done) return;
    const tl = gsap.timeline({
      onComplete: () => {
        sessionStorage.setItem("centinela_loaded", "1");
        setDone(true);
      },
    });
    gsap.set(contentRef.current, { clipPath: "inset(100% 0 0 0)" });
    tl.fromTo(
      wordRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" },
    )
      .fromTo(
        barRef.current,
        { width: "0%" },
        { width: "100%", duration: 2, ease: "power1.inOut" },
        "+=0.2",
      )
      .fromTo(
        textRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.5 },
        "<-1.6",
      )
      .to(overlayRef.current, { opacity: 0, duration: 0.6, ease: "power2.in" })
      .to(
        contentRef.current,
        { clipPath: "inset(0% 0 0 0)", duration: 0.8, ease: "power3.out" },
        "<",
      );
  }, [done]);

  if (done) return <>{children}</>;

  return (
    <>
      <div ref={contentRef} style={{ clipPath: "inset(100% 0 0 0)" }}>
        {children}
      </div>
      <div
        ref={overlayRef}
        className="fixed inset-0 z-[100] bg-[#0A0B0D] flex flex-col items-center justify-center"
      >
        <div
          ref={wordRef}
          className="text-white text-[48px] font-bold tracking-tight"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}
        >
          CENTINELA
        </div>
        <div className="mt-8 w-[240px] h-[2px] bg-[#1f2937] overflow-hidden">
          <div ref={barRef} className="h-full bg-[#3B82F6]" style={{ width: 0 }} />
        </div>
        <div ref={textRef} className="mt-4 text-[13px] text-[#475569]">
          Initializing secure environment...
        </div>
      </div>
    </>
  );
}