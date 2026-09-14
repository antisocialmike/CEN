import { motion } from "motion/react";
import { balanceCardVariants, balanceAmountVariants, badgeVariants } from "./animations";
import { BalanceCard } from "./BalanceCard";

interface AnimatedBalanceCardProps {
  label: string;
  amount: number;
  currency?: string;
  status: "paid" | "pending" | "failed";
  period: string;
}

export function AnimatedBalanceCard({
  label,
  amount,
  currency,
  status,
  period,
}: AnimatedBalanceCardProps) {
  return (
    <motion.div
      variants={balanceCardVariants}
      initial="initial"
      animate="animate"
      className="balance-card-container"
    >
      <BalanceCard
        label={label}
        amount={amount}
        currency={currency}
        status={status}
        period={period}
      />

            <motion.div
        className="balance-card-glow"
        animate={{
          opacity: [0.5, 0.8, 0.5],
        }}
        transition={{
          repeat: Infinity,
          duration: 3,
          ease: "easeInOut",
        }}
      />
    </motion.div>
  );
}
