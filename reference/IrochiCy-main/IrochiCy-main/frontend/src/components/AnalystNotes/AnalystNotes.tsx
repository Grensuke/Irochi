import { useState } from 'react';
import type { AnalystNote } from '@/types';
import { addToast } from '@/components/Toast/Toast';
import './AnalystNotes.css';

interface AnalystNotesProps { notes: AnalystNote[]; }

export default function AnalystNotes({ notes }: AnalystNotesProps) {
  const [text, setText] = useState('');
  const [localNotes, setLocalNotes] = useState<AnalystNote[]>(notes);

  const handleSave = () => {
    if (!text.trim()) return;
    const note: AnalystNote = {
      id: crypto.randomUUID?.() || String(Date.now()),
      author: 'Current Analyst',
      content: text.trim(),
      created_at: new Date().toISOString(),
    };
    setLocalNotes(prev => [note, ...prev]);
    setText('');
    addToast({ type: 'success', title: 'Note saved' });
  };

  return (
    <div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-tertiary)', marginBottom: 'var(--space-3)' }}>
        ANALYST NOTES
      </div>
      <textarea
        className="analyst-notes__textarea"
        placeholder="Add investigation notes..."
        value={text}
        onChange={e => setText(e.target.value)}
        rows={5}
      />
      <button className="analyst-notes__save" onClick={handleSave}>SAVE NOTE</button>
      {localNotes.length > 0 && (
        <div className="analyst-notes__history">
          {localNotes.map(n => (
            <div key={n.id} className="analyst-notes__note">
              <div className="analyst-notes__note-meta">{n.author} · {new Date(n.created_at).toLocaleString()}</div>
              <div className="analyst-notes__note-content">{n.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
