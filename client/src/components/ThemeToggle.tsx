import { useEffect, useState } from "react";
import { Moon, Sun } from "@phosphor-icons/react";

export type Theme = "light" | "dark";

const KEY = "cen_theme";

export function resolveTheme(): Theme {
  try {
    const stored = localStorage.getItem(KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(resolveTheme);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function onSystemChange(event: MediaQueryListEvent) {
      let hasChoice = false;
      try {
        hasChoice = localStorage.getItem(KEY) !== null;
      } catch {
        hasChoice = false;
      }
      if (!hasChoice) {
        const next: Theme = event.matches ? "dark" : "light";
        setTheme(next);
        document.documentElement.dataset.theme = next;
      }
    }

    media.addEventListener("change", onSystemChange);
    return () => media.removeEventListener("change", onSystemChange);
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    const root = document.documentElement;

    root.setAttribute("data-theme-switching", "");
    root.dataset.theme = next;
    setTheme(next);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => root.removeAttribute("data-theme-switching"));
    });

    try {
      localStorage.setItem(KEY, next);
    } catch {
    }
  }

  const goingTo = theme === "dark" ? "claro" : "oscuro";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={`Cambiar al tema ${goingTo}`}
      title={`Cambiar al tema ${goingTo}`}
    >
      {theme === "dark" ? <Sun weight="bold" /> : <Moon weight="bold" />}
    </button>
  );
}
