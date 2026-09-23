import './ToggleSwitch.css';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  label?: string;
}

export default function ToggleSwitch({ checked, onChange, label }: ToggleSwitchProps) {
  return (
    <div
      className={`toggle-switch ${checked ? 'toggle-switch--on' : 'toggle-switch--off'}`}
      onClick={() => onChange(!checked)}
      role="switch"
      aria-checked={checked}
      aria-label={label}
    >
      <div className="toggle-switch__thumb" />
    </div>
  );
}
