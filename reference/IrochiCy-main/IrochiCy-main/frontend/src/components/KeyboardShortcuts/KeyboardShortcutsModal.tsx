import { useState } from 'react';
import Modal from '@/components/Modal/Modal';
import './KeyboardShortcutsModal.css';

const SHORTCUTS = [
  { keys: ['G', 'D'], desc: 'Go to Dashboard' },
  { keys: ['G', 'A'], desc: 'Go to Alerts' },
  { keys: ['G', 'N'], desc: 'Go to Network' },
  { keys: ['G', 'T'], desc: 'Go to Threats' },
  { keys: ['/'], desc: 'Focus search bar' },
  { keys: ['T'], desc: 'Toggle theme' },
  { keys: ['Esc'], desc: 'Close modal/menu' },
  { keys: ['?'], desc: 'Show this help' },
];

export default function KeyboardShortcutsModal() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button id="kb-shortcuts-trigger" className="kb-trigger" onClick={() => setOpen(true)} aria-label="Keyboard shortcuts">?</button>
      {open && (
        <Modal title="Keyboard Shortcuts" onClose={() => setOpen(false)}>
          <div className="kb-modal">
            {SHORTCUTS.map((s, i) => (
              <div key={i} className="kb-item">
                <span className="kb-item__desc">{s.desc}</span>
                <span className="kb-item__keys">
                  {s.keys.map((k, j) => (
                    <span key={j}>
                      <span className="kb-key">{k}</span>
                      {j < s.keys.length - 1 && <span style={{ color: 'var(--text-tertiary)', margin: '0 2px' }}>+</span>}
                    </span>
                  ))}
                </span>
              </div>
            ))}
          </div>
        </Modal>
      )}
    </>
  );
}
