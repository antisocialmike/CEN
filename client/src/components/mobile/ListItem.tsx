import { ReactNode } from "react";
import { CaretRight } from "@phosphor-icons/react";

interface ListItemProps {
  title: string;
  subtitle?: string;
  badge?: {
    text: string;
    type: "success" | "info" | "warning" | "danger";
  };
  action?: () => void;
  actionLabel?: ReactNode;
  onClick?: () => void;
}

export function ListItem({
  title,
  subtitle,
  badge,
  action,
  actionLabel,
  onClick,
}: ListItemProps) {
  return (
    <div className="list-item" onClick={onClick}>
      <div className="list-item-content">
        <div className="list-item-title">{title}</div>
        {subtitle && <div className="list-item-subtitle">{subtitle}</div>}
      </div>
      {badge ? (
        <span className={`badge badge-${badge.type}`}>{badge.text}</span>
      ) : (
        <button
          className="list-item-action"
          onClick={(e) => {
            e.stopPropagation();
            action?.();
          }}
          type="button"
        >
          {actionLabel || <CaretRight size={20} weight="bold" />}
        </button>
      )}
    </div>
  );
}
