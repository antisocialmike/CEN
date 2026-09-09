import { ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";

const ENTER = [0.16, 1, 0.3, 1] as const;

interface PageTransitionProps {
  children: ReactNode;
}

export default function PageTransition({ children }: PageTransitionProps) {
  const reduceMotion = useReducedMotion();
  const shift = reduceMotion ? 0 : 10;

  return (
    <motion.div
      initial={{ opacity: 0, y: shift }}
      animate={{
        opacity: 1,
        y: 0,
        transition: { duration: 0.24, ease: ENTER }
      }}
      exit={{
        opacity: 0,
        y: -shift,
        transition: { duration: 0.14, ease: "easeIn" }
      }}
    >
      {children}
    </motion.div>
  );
}
