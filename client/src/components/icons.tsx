interface IconProps {
  className?: string;
}

export function LogoMark({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" fill="var(--rosa)" />
      <path d="M4.5 4H27.5V7.6H8.1V24.4H27.5V28H4.5Z" fill="#fff" />
      <rect x="12" y="11.7" width="15.5" height="3.4" fill="#fff" />
      <rect x="12" y="18.1" width="15.5" height="3.4" fill="#fff" />
    </svg>
  );
}
