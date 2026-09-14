import { motion } from "motion/react";
import {
  screenVariants,
  containerVariants,
  itemVariants,
  metricsContainerVariants,
  metricCardVariants,
  badgeVariants,
} from "./animations";
import { AnimatedBalanceCard } from "./AnimatedBalanceCard";
import { AnimatedListItem } from "./AnimatedListItem";
import { MetricCard } from "./MetricCard";

interface Receipt {
  period: string;
  dateRange: string;
  amount: number;
}

interface EmployeeDashboardAnimatedProps {
  balance: number;
  gross: number;
  taxes: number;
  period: string;
  receipts: Receipt[];
  onDownloadReceipt?: (period: string) => void;
}

export function EmployeeDashboardAnimated({
  balance,
  gross,
  taxes,
  period,
  receipts,
  onDownloadReceipt,
}: EmployeeDashboardAnimatedProps) {
  return (
    <motion.div
      className="mobile-screen"
      variants={screenVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
            <div className="mobile-header">
        <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
          Mi nómina
        </motion.h1>
        <motion.p
          className="mobile-header-subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
        >
          Período actual: {period}
        </motion.p>
      </div>

            <motion.div className="mobile-content">
                <AnimatedBalanceCard
          label="Saldo neto"
          amount={balance}
          status="paid"
          period={period}
        />

                <motion.div
          className="metrics-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "16px",
            marginBottom: "24px",
          }}
          variants={metricsContainerVariants}
          initial="initial"
          animate="animate"
        >
          <motion.div variants={metricCardVariants}>
            <MetricCard label="Bruto" value={`$${gross.toLocaleString("es-MX")}`} />
          </motion.div>

          <motion.div variants={metricCardVariants}>
            <MetricCard
              label="Impuestos"
              value={`$${taxes.toLocaleString("es-MX")}`}
              trend="down"
            />
          </motion.div>
        </motion.div>

                <motion.div variants={containerVariants} initial="initial" animate="animate">
          <motion.h3
            variants={itemVariants}
            style={{
              fontSize: "13px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.3px",
              marginBottom: "12px",
              color: "var(--text-secondary)",
              padding: "0 4px",
            }}
          >
            Últimos recibos
          </motion.h3>

          {receipts.map((receipt, index) => (
            <AnimatedListItem
              key={receipt.period}
              title={receipt.period}
              subtitle={`${receipt.dateRange} • $${receipt.amount.toLocaleString("es-MX")}`}
              action={() => onDownloadReceipt?.(receipt.period)}
              actionLabel="📥"
              delay={0.1 * (index + 1)}
            />
          ))}
        </motion.div>

                {receipts.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            style={{
              textAlign: "center",
              padding: "24px 16px",
              color: "var(--text-muted)",
            }}
          >
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>📄</div>
            <p>No hay recibos disponibles aún</p>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
}
