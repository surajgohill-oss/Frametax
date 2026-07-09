"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { NFL_THEME_AUDIO_URL } from "@/lib/audioConfig";

const LOCAL_FALLBACK = "/audio/nfl-theme.mp3";
const PREF_KEY = "awr_nfl_audio";

interface NflAudioPrefs {
  volume: number;
  muted: boolean;
}

function loadPrefs(): NflAudioPrefs {
  try {
    const raw = localStorage.getItem(PREF_KEY);
    if (raw) return { volume: 0.25, muted: false, ...JSON.parse(raw) };
  } catch {}
  return { volume: 0.25, muted: false };
}

function savePrefs(p: NflAudioPrefs) {
  try { localStorage.setItem(PREF_KEY, JSON.stringify(p)); } catch {}
}

export function useNflAudio() {
  const audioRef            = useRef<HTMLAudioElement | null>(null);
  const triedFallbackRef    = useRef(false);
  const [playing, setPlaying]     = useState(false);
  const [muted, setMutedState]    = useState(false);
  const [volume, setVolumeState]  = useState(0.25);
  const [blocked, setBlocked]     = useState(false);
  const [errorMsg, setErrorMsg]   = useState<string | null>(null);
  const [mounted, setMounted]     = useState(false);

  // Switch to local fallback src — called when primary URL fails.
  const tryFallback = useCallback((pendingPlay: boolean) => {
    const audio = audioRef.current;
    if (!audio || triedFallbackRef.current) {
      setErrorMsg("File missing — add nfl-theme.mp3 to public/audio/");
      return;
    }
    triedFallbackRef.current = true;
    audio.src = LOCAL_FALLBACK;
    audio.load();
    if (pendingPlay) {
      audio.play().then(() => {
        setBlocked(false);
        setErrorMsg(null);
      }).catch((e: Error) => {
        if (e.name === "NotAllowedError") {
          setBlocked(true);
          setErrorMsg(null);
        } else {
          setErrorMsg("File missing — add nfl-theme.mp3 to public/audio/");
        }
      });
    }
  }, []);

  useEffect(() => {
    const prefs = loadPrefs();
    setMutedState(prefs.muted);
    setVolumeState(prefs.volume);
    setMounted(true);

    const audio = new Audio(NFL_THEME_AUDIO_URL);
    audio.loop = true;
    audio.volume = prefs.muted ? 0 : prefs.volume;
    audioRef.current = audio;

    audio.addEventListener("play",  () => { setPlaying(true); setBlocked(false); setErrorMsg(null); });
    audio.addEventListener("pause", () => setPlaying(false));
    audio.addEventListener("ended", () => setPlaying(false));

    // Media load error — switch to local fallback automatically.
    const handleError = () => {
      if (!triedFallbackRef.current) {
        tryFallback(false);
      } else {
        setErrorMsg("File missing — add nfl-theme.mp3 to public/audio/");
      }
    };
    audio.addEventListener("error", handleError);

    return () => {
      audio.pause();
      audio.removeEventListener("error", handleError);
      audio.src = "";
    };
  }, [tryFallback]);

  const play = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setErrorMsg(null);
    audio.play().then(() => {
      setBlocked(false);
    }).catch((e: Error) => {
      if (e.name === "NotAllowedError") {
        // Browser blocked autoplay — show Tap to play.
        setBlocked(true);
      } else {
        // File error (403, 404, decode). Try local fallback with play intent.
        tryFallback(true);
      }
    });
  }, [tryFallback]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const stop = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
  }, []);

  const setMuted = useCallback((m: boolean) => {
    setMutedState(m);
    if (audioRef.current) audioRef.current.volume = m ? 0 : volume;
    savePrefs({ volume, muted: m });
  }, [volume]);

  const setVolume = useCallback((v: number) => {
    const clamped = Math.max(0, Math.min(1, v));
    setVolumeState(clamped);
    if (audioRef.current && !muted) audioRef.current.volume = clamped;
    savePrefs({ volume: clamped, muted });
  }, [muted]);

  /** Call from NFL card/row onClick — play() invoked synchronously inside user gesture. */
  const triggerFromUserAction = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) play();
  }, [play]);

  return {
    playing,
    muted,
    volume,
    blocked,
    errorMsg,
    mounted,
    play,
    pause,
    stop,
    setMuted,
    setVolume,
    triggerFromUserAction,
  };
}
