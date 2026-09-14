import { motion } from "motion/react";
import { ReactNode } from "react";
import { listItemVariants, listItemActionVariants } from "./animations";
import { ListItem } from "./ListItem";

interface AnimatedListItemProps {
  title: string;
  subtitle?: string;
  badge?: {
    text: string;
    type: "success" | "info" | "warning" | "danger";
  };
  action?: () => void;
  actionLabel?: ReactNode;
  onClick?: () => void;
  delay?: number;
}

export function AnimatedListItem({
  title,
  subtitle,
  badge,
  action,
  actionLabel,
  onClick,
  delay = 0,
}: AnimatedListItemProps) {
  return (
    <motion.div
      variants={listItemVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      whileTap="tap"
      transition={{
        delay,
      }}
    >
      <motion.div whileHover={{ x: 4 }}>
        <ListItem
          title={title}
          subtitle={subtitle}
          badge={badge}
          action={action}
          actionLabel={actionLabel}
          onClick={onClick}
        />
      </motion.div>

            {!badge && (
        <motion.div
          variants={listItemActionVariants}
          className="list-item-action-wrapper"
        />
      )}
    </motion.div>
  );
}
