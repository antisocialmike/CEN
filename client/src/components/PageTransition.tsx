import { ReactNode } from "react";
import { motion } from "motion/react";

interface PageTransitionProps {
  children: ReactNode;
}

const variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -16 }
};

export default function PageTransition({ children }: PageTransitionProps) {
  return (
    <motion.div
      variants={variants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
