import { useState } from 'react';
import './Documentation.css';

const DOCS_SECTIONS = [
  {
    id: 'overview',
    title: 'Overview',
    content: (
      <div>
        <p>Irochi is a real-time network threat-detection and security-intelligence system. It is designed to passively observe traffic segments, analyze behaviors, and deliver evidence-rich alerts to security analysts. Crucially, the platform operates in a read-only telemetry mode, guaranteeing that no write-back or inline packet modification is attempted.</p>
        <div className="status-label-doc mock">DUMMY SCAFFOLD STAGE</div>
      </div>
    )
  },
  {
    id: 'getting-started',
    title: 'Getting Started',
    content: (
      <div>
        <p>To run the developer environment, check out the source code and use docker compose to spin up the local development stack:</p>
        <pre className="mono code-snippet">
{`# Clone and start environment
git clone https://github.com/Grensuke/Irochi.git
cd Irochi
docker-compose up --build`}
        </pre>
        <p>The mock FastAPI server runs at <code className="mono">http://localhost:8000</code> and the React Vite server at <code className="mono">http://localhost:5173</code>.</p>
        <div className="status-label-doc available">AVAILABLE IN DEV</div>
      </div>
    )
  },
  {
    id: 'frontend-arch',
    title: 'Frontend Architecture',
    content: (
      <div>
        <p>The frontend is written in React, TypeScript, and Vite. Routing is managed by React Router v7. Components are organized into pages and shared UI primitives in <code className="mono">src/components</code>. The data layout communicates strictly with the backend API service wrapper.</p>
        <pre className="mono code-snippet">
{`// src/services/api.ts
export const api = {
  getAlerts: async (): Promise<AlertListResponse> => { ... },
  getDashboardSummary: async (): Promise<DashboardSummary> => { ... }
};`}
        </pre>
        <div className="status-label-doc available">LOCKED IMPLEMENTATION</div>
      </div>
    )
  },
  {
    id: 'api-integration',
    title: 'API Integration Overview',
    content: (
      <div>
        <p>All client communications route through the backend gateway. REST endpoints supply summaries, historical lists, and profile configs:</p>
        <table className="docs-api-table">
          <thead>
            <tr>
              <th>ENDPOINT</th>
              <th>METHOD</th>
              <th>CONTRACT STATE</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">/api/v1/health</td>
              <td className="mono">GET</td>
              <td><span className="badge-doc success">Mock Endpoint Active</span></td>
            </tr>
            <tr>
              <td className="mono">/api/v1/alerts</td>
              <td className="mono">GET</td>
              <td><span className="badge-doc success">Mock Endpoint Active</span></td>
            </tr>
            <tr>
              <td className="mono">/api/v1/dashboard/summary</td>
              <td className="mono">GET</td>
              <td><span className="badge-doc success">Mock Endpoint Active</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    )
  },
  {
    id: 'websocket-lifecycle',
    title: 'WebSocket Lifecycle',
    content: (
      <div>
        <p>The live alerts are delivered over a WebSocket boundary at <code className="mono">/api/v1/ws/alerts</code>. The lifecycle states proceed as follows:</p>
        <ol className="docs-ordered-list">
          <li><strong>Client Connecting:</strong> Handshake initializing.</li>
          <li><strong>Backfilling Phase:</strong> Server pushes existing alert history to populate the analyst view.</li>
          <li><strong>Backfill Complete:</strong> Server sends a complete payload delimiter: <code className="mono">{"{ type: 'backfill_complete', alert: null }"}</code>.</li>
          <li><strong>Live Phase:</strong> Server pushes new threats in real-time as detectors flag traffic indicators.</li>
        </ol>
        <div className="status-label-doc available">WS DUMMY STREAM ACTIVE</div>
      </div>
    )
  },
  {
    id: 'alert-model',
    title: 'Alert Presentation Model',
    content: (
      <div>
        <p>Alerts in the frontend are formatted for security analyst triage. We explicitly distinguish "closed" states from mitigation claims. An alert contains:</p>
        <pre className="mono code-snippet">
{`interface Alert {
  alert_id: string;
  timestamp: string;
  threat_type: ThreatType;
  detector_id: DetectorId;
  severity: Severity;
  confidence: number;
  src_ip: string | null;
  dst_ip: string | null;
  evidence_summary: string;
  status: AlertStatus; // 'new' | 'investigating' | 'closed' | 'false_positive'
}`}
        </pre>
        <div className="status-label-doc available">LOCKED DATA MODEL</div>
      </div>
    )
  },
  {
    id: 'detector-overview',
    title: 'Detector Overview',
    content: (
      <div>
        <p>Threat detection is logically split into five threat intelligence modules. They evaluate normalized streams rather than standalone packets:</p>
        <ul className="docs-list">
          <li><strong>DDoS Detector:</strong> Flags volumetric anomalies and protocol floods.</li>
          <li><strong>Recon Detector:</strong> Detects sequential scans and network maps.</li>
          <li><strong>DNS/DGA Detector:</strong> Analyzes algorithmically generated query domains.</li>
          <li><strong>TLS/C2 Detector:</strong> Identifies TLS handshake beacons.</li>
          <li><strong>Exfiltration Detector:</strong> Flags excessive payload transfers.</li>
        </ul>
        <div className="status-label-doc planned">MODELS IN DEVELOPMENT</div>
      </div>
    )
  },
  {
    id: 'deployment-notes',
    title: 'Deployment Notes',
    content: (
      <div>
        <p>For production deployment, Nginx is placed in front of the Vite assets and FastAPI gateway to proxy traffic securely. Read the root repository <code className="mono">README.md</code> for production compose configs.</p>
        <div className="status-label-doc planned">PLANNED INFRASTRUCTURE</div>
      </div>
    )
  },
  {
    id: 'faq',
    title: 'FAQ',
    content: (
      <div>
        <h4 style={{ marginBottom: 4 }}>Can Irochi automatically block an attacker?</h4>
        <p style={{ marginBottom: 16 }}>No. Irochi is purely passive and read-only. It does not block IP addresses, alter routing paths, or write to any network interfaces.</p>
        <h4 style={{ marginBottom: 4 }}>Does Irochi decrypt TLS traffic?</h4>
        <p>No. Threats inside SSL/TLS are identified using metadata parameters like client JA3/JA4 fingerprints, server certificate validity, SNI labels, and packet intervals.</p>
      </div>
    )
  }
];

export function Documentation() {
  const [activeSection, setActiveSection] = useState('overview');

  const activeDoc = DOCS_SECTIONS.find((s) => s.id === activeSection) || DOCS_SECTIONS[0];

  return (
    <div className="docs-page">
      <div className="docs-container scroll-reveal">
        {/* Left Nav */}
        <aside className="docs-sidebar">
          {/* Mock Search Bar */}
          <div className="docs-search-mock">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="7" cy="7" r="5" />
              <line x1="11" y1="11" x2="15" y2="15" />
            </svg>
            <input type="text" placeholder="Search docs (Demo)..." disabled />
          </div>

          <nav className="docs-nav">
            {DOCS_SECTIONS.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`docs-nav-item ${activeSection === section.id ? 'active' : ''}`}
              >
                {section.title}
              </button>
            ))}
          </nav>
        </aside>

        {/* Right Content */}
        <article className="docs-content">
          <h1 className="docs-content-title">{activeDoc.title}</h1>
          <div className="docs-content-body">{activeDoc.content}</div>
        </article>
      </div>
    </div>
  );
}
