interface SkeletonProps {
  width?: string;
  height?: number;
  radius?: number;
}

export default function Skeleton({ width = "100%", height = 14, radius = 0 }: SkeletonProps) {
  return (
    <span
      className="skeleton"
      style={{ display: "block", width, height, borderRadius: radius }}
      aria-hidden="true"
    />
  );
}
