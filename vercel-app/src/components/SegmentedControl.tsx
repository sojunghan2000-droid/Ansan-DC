"use client";

interface Props<T extends string> {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  label?: string;
  ariaLabel?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  label,
  ariaLabel,
}: Props<T>) {
  return (
    <div>
      {label && <div className="sect-label">{label}</div>}
      <div className="segctl" role="radiogroup" aria-label={ariaLabel ?? label ?? ""}>
        {options.map((opt) => (
          <button
            key={opt}
            type="button"
            role="radio"
            aria-checked={opt === value}
            data-active={opt === value}
            onClick={() => onChange(opt)}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
