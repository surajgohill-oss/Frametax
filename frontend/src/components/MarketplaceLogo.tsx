import { cn } from "@/lib/utils";

interface Props {
  marketplace: "stubhub" | "gametime" | "tickpick" | "vividseats";
  size?: "sm" | "md" | "lg";
  variant?: "badge" | "icon" | "text";
}

const MARKETPLACE_INFO: Record<string, { name: string; color: string; icon: string; bg: string }> = {
  stubhub: {
    name: "StubHub",
    color: "text-red-500",
    icon: "S",
    bg: "bg-red-500/15 border-red-500/30",
  },
  gametime: {
    name: "Gametime",
    color: "text-blue-500",
    icon: "G",
    bg: "bg-blue-500/15 border-blue-500/30",
  },
  tickpick: {
    name: "TickPick",
    color: "text-purple-500",
    icon: "T",
    bg: "bg-purple-500/15 border-purple-500/30",
  },
  vividseats: {
    name: "Vivid Seats",
    color: "text-amber-500",
    icon: "V",
    bg: "bg-amber-500/15 border-amber-500/30",
  },
};

export function MarketplaceLogo({ marketplace, size = "md", variant = "badge" }: Props) {
  const info = MARKETPLACE_INFO[marketplace];
  if (!info) return null;

  if (variant === "text") {
    return <span className={cn("font-semibold", info.color)}>{info.name}</span>;
  }

  if (variant === "icon") {
    const sizeClasses = {
      sm: "w-6 h-6 text-[10px]",
      md: "w-8 h-8 text-xs",
      lg: "w-10 h-10 text-sm",
    };
    return (
      <div className={cn("rounded-lg flex items-center justify-center border font-bold", info.bg, sizeClasses[size], info.color)}>
        {info.icon}
      </div>
    );
  }

  const badgeSizeClasses = {
    sm: "text-[9px] px-1.5 py-0.5",
    md: "text-[10px] px-2 py-1",
    lg: "text-xs px-2.5 py-1.5",
  };

  return (
    <span className={cn("rounded-lg border font-medium", info.bg, info.color, badgeSizeClasses[size])}>
      {info.name}
    </span>
  );
}

export const MARKETPLACE_DISPLAY_NAMES: Record<string, string> = {
  stubhub: "StubHub",
  gametime: "Gametime",
  tickpick: "TickPick",
  vividseats: "Vivid Seats",
};
