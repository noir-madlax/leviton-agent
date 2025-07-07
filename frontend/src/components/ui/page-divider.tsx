interface PageDividerProps {
  className?: string;
}

export function PageDivider({ className = "" }: PageDividerProps) {
  return <div className={`w-full h-px bg-gray-200 ${className}`} />;
} 