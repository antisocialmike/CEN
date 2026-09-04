interface IconProps {
  className?: string;
}

export function MailIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M3 5.5C3 4.67157 3.67157 4 4.5 4H15.5C16.3284 4 17 4.67157 17 5.5V14.5C17 15.3284 16.3284 16 15.5 16H4.5C3.67157 16 3 15.3284 3 14.5V5.5Z"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <path d="M4 5.5L10 10.5L16 5.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function LockIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="4.5" y="9" width="11" height="7.5" rx="1.5" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M6.5 9V6.5C6.5 4.567 8.067 3 10 3C11.933 3 13.5 4.567 13.5 6.5V9"
        stroke="currentColor"
        strokeWidth="1.4"
      />
    </svg>
  );
}

export function EyeIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M1.5 10C1.5 10 4.5 4.5 10 4.5C15.5 4.5 18.5 10 18.5 10C18.5 10 15.5 15.5 10 15.5C4.5 15.5 1.5 10 1.5 10Z"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

export function EyeOffIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M1.5 10C1.5 10 4.5 4.5 10 4.5C15.5 4.5 18.5 10 18.5 10C18.5 10 15.5 15.5 10 15.5C4.5 15.5 1.5 10 1.5 10Z"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M3 17L17 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function UsersIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7.5" cy="6.5" r="2.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M2.5 16C2.5 12.9624 4.79 10.5 7.5 10.5C10.21 10.5 12.5 12.9624 12.5 16" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <circle cx="14" cy="7" r="2" stroke="currentColor" strokeWidth="1.4" />
      <path d="M13 10.6C15.3 10.9 17.5 13 17.5 16" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
