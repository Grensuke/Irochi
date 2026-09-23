import { useRef, useEffect } from 'react';
import './ContextMenu.css';

export interface ContextMenuItem {
  label: string;
  onClick: () => void;
  danger?: boolean;
  divider?: boolean;
}

interface ContextMenuProps {
  items: ContextMenuItem[];
  x: number;
  y: number;
  onClose: () => void;
}

export default function ContextMenu({ items, x, y, onClose }: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Adjust position if menu would go off-screen
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      if (rect.right > window.innerWidth) {
        ref.current.style.left = `${x - rect.width}px`;
      }
      if (rect.bottom > window.innerHeight) {
        ref.current.style.top = `${y - rect.height}px`;
      }
    }
  }, [x, y]);

  return (
    <>
      <div className="ctx-menu__backdrop" onClick={onClose} />
      <div className="ctx-menu" ref={ref} style={{ left: x, top: y }}>
        {items.map((item, i) => (
          item.divider ? (
            <div key={i} className="ctx-menu__divider" />
          ) : (
            <div
              key={i}
              className={`ctx-menu__item ${item.danger ? 'ctx-menu__item--danger' : ''}`}
              onClick={() => { item.onClick(); onClose(); }}
            >
              {item.label}
            </div>
          )
        ))}
      </div>
    </>
  );
}
