import { useState } from 'react';
import type { CanonicalEvent } from '@/types';
import { addToast } from '@/components/Toast/Toast';
import './RawEventViewer.css';

interface RawEventViewerProps { event?: CanonicalEvent; }

function syntaxHighlight(json: string): string {
  return json.replace(
    /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number';
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? 'json-key' : 'json-string';
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean';
      } else if (/null/.test(match)) {
        cls = 'json-null';
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

export default function RawEventViewer({ event }: RawEventViewerProps) {
  const [expanded, setExpanded] = useState(false);

  if (!event) return null;

  const jsonStr = JSON.stringify(event, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonStr);
    addToast({ type: 'success', title: 'JSON copied to clipboard' });
  };

  return (
    <div className="raw-event">
      <div className="raw-event__header" onClick={() => setExpanded(!expanded)}>
        <span className="raw-event__title">CANONICAL EVENT</span>
        <span className="raw-event__toggle">{expanded ? '▼ COLLAPSE' : '▶ EXPAND'}</span>
      </div>
      {expanded && (
        <div className="raw-event__body">
          <button className="raw-event__copy" onClick={handleCopy}>COPY JSON</button>
          <div className="raw-event__code" dangerouslySetInnerHTML={{ __html: syntaxHighlight(jsonStr) }} />
        </div>
      )}
    </div>
  );
}
