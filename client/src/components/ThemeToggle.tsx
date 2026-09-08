import { useEffect, useState } from "react";
import { Moon, Sun } from "@phosphor-icons/react";

export type Theme = "light" | "dark";

const KEY = "cen_theme";

function readStoredTheme(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function storeTheme(theme: Theme): boolean {
  try {
    localStorage.setItem(KEY, theme);
    return true;
  } catch {
    return false;
  }
}

function resolveTheme(): Theme {
  const stored = readStoredTheme();
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(resolveTheme);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function onSystemChange(event: MediaQueryListEvent) {
      if (readStoredTheme() !== null) return;

      const next: Theme = event.matches ? "dark" : "light";
      setTheme(next);
      document.documentElement.dataset.theme = next;
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

    storeTheme(next);
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
