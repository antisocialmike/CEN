interface IconProps {
  className?: string;
}

export function LogoMark({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="1" y="1" width="30" height="30" fill="var(--rosa)" />
      <path
        d="M20.5 11.5C19.4 10.2 17.8 9.5 16 9.5C12.7 9.5 10 12.2 10 15.5C10 18.8 12.7 21.5 16 21.5C17.8 21.5 19.4 20.8 20.5 19.5"
        stroke="#fff"
        strokeWidth="2.5"
      />
      <path d="M9.5 14H17.5" stroke="#fff" strokeWidth="2.5" />
      <path d="M9.5 17H17.5" stroke="#fff" strokeWidth="2.5" />
    </svg>
  );
}
