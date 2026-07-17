import type { ReactNode } from "react";

export function GlassCard({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`glass rounded-2xl ${hover ? "card-hover" : ""} ${className}`}
    >
      {children}
    </div>
  );
}
