"use client";
import { Volume2, VolumeX, Square, Play, Pause, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { NFL_THEME_LABEL } from "@/lib/audioConfig";

interface Props {
  playing: boolean;
  muted: boolean;
  blocked: boolean;
  errorMsg?: string | null;
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
  onToggleMute: () => void;
}

export default function NflAudioControl({
  playing, muted, blocked, errorMsg, onPlay, onPause, onStop, onToggleMute,
}: Props) {
  return (
    <div className={cn(
      "fixed bottom-5 left-1/2 -translate-x-1/2 z-50",
      "flex items-center gap-2 px-3 py-2 rounded-full",
      "border bg-[#0e1117]/95 backdrop-blur-sm shadow-2xl",
      playing
        ? "border-amber-500/40 shadow-amber-500/10"
        : errorMsg
          ? "border-red-500/30"
          : "border-white/10",
    )}>
      {/* NFL indicator dot */}
      <span className={cn(
        "w-2 h-2 rounded-full flex-shrink-0",
        playing ? "bg-amber-400 animate-pulse" : errorMsg ? "bg-red-400" : "bg-white/20",
      )} />

      <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest pr-1">
        {NFL_THEME_LABEL}
      </span>

      {errorMsg && (
        <span className="flex items-center gap-1 text-[10px] text-red-400 font-medium max-w-[180px] truncate">
          <AlertCircle size={10} className="flex-shrink-0" />
          {errorMsg}
        </span>
      )}

      {blocked && !playing && !errorMsg && (
        <button
          onClick={onPlay}
          className="text-[10px] text-amber-400 hover:text-amber-300 font-medium px-2 py-0.5 rounded border border-amber-500/30 bg-amber-500/8 transition-colors"
        >
          Tap to play
        </button>
      )}

      {playing && (
        <span className="text-[10px] text-amber-400 font-medium">Playing</span>
      )}

      {/* Play / Pause */}
      <button
        onClick={playing ? onPause : onPlay}
        className="p-1 rounded-full hover:bg-white/10 transition-colors text-white/70 hover:text-white"
        title={playing ? "Pause" : "Play"}
      >
        {playing ? <Pause size={13} /> : <Play size={13} />}
      </button>

      {/* Mute */}
      <button
        onClick={onToggleMute}
        className="p-1 rounded-full hover:bg-white/10 transition-colors text-white/70 hover:text-white"
        title={muted ? "Unmute" : "Mute"}
      >
        {muted ? <VolumeX size={13} /> : <Volume2 size={13} />}
      </button>

      {/* Stop */}
      <button
        onClick={onStop}
        className="p-1 rounded-full hover:bg-white/10 transition-colors text-white/50 hover:text-white"
        title="Stop"
      >
        <Square size={11} />
      </button>
    </div>
  );
}
