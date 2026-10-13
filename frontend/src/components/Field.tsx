import { useId } from "react";

interface FieldProps {
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  hint?: string;
}

export default function Field({ label, type = "text", value, onChange, autoComplete, hint }: FieldProps) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-ink">{label}</span>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        className="rounded-md border border-hairline bg-white px-3 py-2 text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
      />
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </label>
  );
}
