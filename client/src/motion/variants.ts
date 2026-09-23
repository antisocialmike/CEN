import { useMemo } from "react";
import { useReducedMotion, type Variants } from "motion/react";

export const EASE_OUT = [0.23, 1, 0.32, 1] as const;
export const EASE_IN_OUT = [0.77, 0, 0.175, 1] as const;
// Arranque lento y final brusco: el logo parece atravesar la camara.
export const EASE_TUNEL = [0.7, 0, 0.84, 0] as const;

export const DUR = {
  fast: 0.12,
  base: 0.18,
  slow: 0.26
} as const;

export const STAGGER = 0.04;

export const routeVariants: Variants = {
  initial: { opacity: 0, transform: "translateY(10px)" },
  animate: {
    opacity: 1,
    transform: "translateY(0px)",
    transition: { duration: DUR.slow, ease: EASE_OUT }
  },
  exit: {
    opacity: 0,
    transform: "translateY(0px)",
    transition: { duration: DUR.fast, ease: EASE_OUT }
  }
};

export const stackVariants: Variants = {
  initial: {},
  animate: {
    transition: { staggerChildren: STAGGER, delayChildren: 0.04 }
  }
};

export const rowVariants: Variants = {
  initial: { opacity: 0, transform: "translateX(-8px)" },
  animate: {
    opacity: 1,
    transform: "translateX(0px)",
    transition: { duration: DUR.base, ease: EASE_OUT }
  }
};

export const blockVariants: Variants = {
  initial: { opacity: 0, transform: "translateY(12px)" },
  animate: {
    opacity: 1,
    transform: "translateY(0px)",
    transition: { duration: DUR.base, ease: EASE_OUT }
  }
};

export const revealVariants: Variants = {
  initial: { opacity: 0, transform: "translateY(20px)" },
  animate: {
    opacity: 1,
    transform: "translateY(0px)",
    transition: { duration: DUR.slow, ease: EASE_OUT }
  }
};

export function useStill(variants: Variants): Variants {
  const reduce = useReducedMotion();

  return useMemo(() => {
    if (!reduce) return variants;

    return Object.fromEntries(
      Object.entries(variants).map(([state, definition]) => {
        if (typeof definition !== "object" || definition === null) {
          return [state, definition];
        }
        const { transform: _travel, ...rest } = definition as Record<
          string,
          unknown
        >;
        return [state, rest];
      })
    ) as Variants;
  }, [variants, reduce]);
}
