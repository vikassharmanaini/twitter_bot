import { useReducedMotion } from "framer-motion";

/** Decorative blurred gradients; pointer-events none; respects reduced motion (static). */
export function BackgroundOrbs() {
  const reduce = useReducedMotion();

  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden
    >
      <div
        className={`absolute -left-[20%] top-[10%] h-[min(520px,50vw)] w-[min(520px,50vw)] rounded-full bg-accent/25 blur-[100px] ${
          reduce ? "" : "animate-float"
        }`}
      />
      <div
        className={`absolute -right-[15%] top-[35%] h-[min(480px,45vw)] w-[min(480px,45vw)] rounded-full bg-accent-secondary/20 blur-[90px] ${
          reduce ? "" : "animate-float-slow"
        }`}
      />
      <div
        className={`absolute bottom-[5%] left-[30%] h-[min(360px,40vw)] w-[min(360px,40vw)] rounded-full bg-accent-tertiary/18 blur-[80px] ${
          reduce ? "" : "animate-float"
        }`}
        style={{ animationDelay: "-6s" }}
      />
    </div>
  );
}
