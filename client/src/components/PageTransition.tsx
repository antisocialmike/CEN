import { ReactNode } from "react";
import { motion } from "motion/react";
import { routeVariants, useStill } from "../motion/variants";

interface PageTransitionProps {
  children: ReactNode;
}

export default function PageTransition({ children }: PageTransitionProps) {
  const variants = useStill(routeVariants);

  return (
    <motion.div
      variants={variants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {children}
    </motion.div>
  );
}
