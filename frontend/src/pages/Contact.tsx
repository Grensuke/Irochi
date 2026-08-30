import { useState } from 'react';
import './Contact.css';

export function Contact() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [org, setOrg] = useState('');
  const [message, setMessage] = useState('');

  return (
    <div className="contact-page">
      <div className="contact-container scroll-reveal">
        {/* Header */}
        <section className="contact-header">
          <div className="section-eyebrow">GET IN TOUCH</div>
          <h1 className="contact-title">Contact & Collaboration</h1>
          <p className="contact-subtitle">
            Have questions about SIH26145, unidirectional network telemetry, or project deployment? Use this form to review the UI layout.
          </p>
        </section>

        {/* Demo Notice Box */}
        <div className="contact-demo-notice">
          <span className="demo-notice-indicator" />
          <div>
            <h3 className="demo-notice-title">Demo Contact Interface</h3>
            <p className="demo-notice-text">
              In accordance with Irochi's passive architecture and project scope, there is no active outbound mail service or contact API endpoint connected. Form submission is disabled.
            </p>
          </div>
        </div>

        {/* Form */}
        <form className="contact-form" onSubmit={(e) => e.preventDefault()}>
          <div className="input-group">
            <label className="input-label" htmlFor="contact-name">FULL NAME</label>
            <input
              id="contact-name"
              type="text"
              className="input"
              placeholder="Analyst Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="contact-email">EMAIL ADDRESS</label>
            <input
              id="contact-email"
              type="email"
              className="input"
              placeholder="analyst@organization.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="contact-org">ORGANIZATION</label>
            <input
              id="contact-org"
              type="text"
              className="input"
              placeholder="Acme Security Ops"
              value={org}
              onChange={(e) => setOrg(e.target.value)}
              disabled
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="contact-message">MESSAGE</label>
            <textarea
              id="contact-message"
              className="input contact-textarea"
              placeholder="Your inquiry details..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={5}
              disabled
            />
          </div>

          <button type="submit" className="btn btn-primary btn-lg contact-submit" disabled>
            Submission Disabled (Demo Mode)
          </button>
        </form>
      </div>
    </div>
  );
}
