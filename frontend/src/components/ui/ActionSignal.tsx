"use client";

import type { ActionWord } from "@/lib/utils";
import { actionColors } from "@/lib/utils";

interface Props {
  action: ActionWord;
  size?: "sm" | "md" | "lg" | "xl";
  description?: string;
}

const SIZE_CLASSES = {
  sm:  { word: "text-xl font-black tracking-widest", wrap: "px-4 py-2 rounded-xl" },
  md:  { word: "text-2xl font-black tracking-widest", wrap: "px-5 py-3 rounded-xl" },
  lg:  { word: "text-4xl font-black tracking-[0.2em]", wrap: "px-8 py-5 rounded-2xl" },
  xl:  { word: "text-5xl font-black tracking-[0.25em]", wrap: "px-10 py-6 rounded-2xl" },
};

export default function ActionSignal({ action, size = "lg", description }: Props) {
  const colors = actionColors(action);
  const cls = SIZE_CLASSES[size];

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`${cls.wrap} border flex items-center justify-center`}
        style={{
          background: colors.bg,
          borderColor: colors.border,
          boxShadow: `0 0 32px ${colors.glow}, inset 0 1px 0 rgba(255,255,255,0.05)`,
        }}
      >
        <span className={cls.word} style={{ color: colors.text }}>
          {action}
        </span>
      </div>
      {description && (
        <p className="text-xs text-slate-400 text-center max-w-[200px] leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
}
