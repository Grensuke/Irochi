/**
 * exportPdf.ts — Vibhinetra Incident Report PDF Generator
 *
 * Generates a professional, sequential PDF report from the alert detail page data.
 * Uses jsPDF for client-side PDF generation.
 */

import { jsPDF } from 'jspdf';
import type { Alert, Incident, ThreatType } from '../types';
import { THREAT_TYPE_LABELS, DETECTOR_LABELS } from '../types';

// ─── Color Palette (RGB tuples) ──────────────────────
const COLORS = {
  black: [20, 20, 25] as [number, number, number],
  darkGray: [60, 60, 68] as [number, number, number],
  medGray: [120, 120, 130] as [number, number, number],
  lightGray: [200, 200, 205] as [number, number, number],
  bgLight: [245, 245, 248] as [number, number, number],
  accent: [99, 102, 241] as [number, number, number],      // Indigo
  critical: [239, 68, 68] as [number, number, number],
  high: [245, 158, 11] as [number, number, number],
  medium: [234, 179, 8] as [number, number, number],
  low: [34, 197, 94] as [number, number, number],
  info: [59, 130, 246] as [number, number, number],
  white: [255, 255, 255] as [number, number, number],
};

function getSeverityColor(severity: string): [number, number, number] {
  switch (severity?.toLowerCase()) {
    case 'critical': return COLORS.critical;
    case 'high': return COLORS.high;
    case 'medium': return COLORS.medium;
    case 'low': return COLORS.low;
    default: return COLORS.info;
  }
}

// ─── PDF Builder Class ───────────────────────────────
class VibhinetraPdfReport {
  private doc: jsPDF;
  private y: number = 0;
  private pageWidth: number;
  private pageHeight: number;
  private marginLeft: number = 25;
  private marginRight: number = 25;
  private contentWidth: number;
  private pageNumber: number = 1;

  constructor() {
    this.doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    this.pageWidth = this.doc.internal.pageSize.getWidth();
    this.pageHeight = this.doc.internal.pageSize.getHeight();
    this.contentWidth = this.pageWidth - this.marginLeft - this.marginRight;
    this.y = 20;
  }

  // ─── Utilities ─────────────────────────────────────

  private checkPageBreak(needed: number) {
    if (this.y + needed > this.pageHeight - 30) {
      this.addFooter();
      this.doc.addPage();
      this.pageNumber++;
      this.y = 20;
    }
  }

  private addFooter() {
    const footerY = this.pageHeight - 12;
    this.doc.setDrawColor(...COLORS.lightGray);
    this.doc.setLineWidth(0.3);
    this.doc.line(this.marginLeft, footerY - 4, this.pageWidth - this.marginRight, footerY - 4);

    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(7);
    this.doc.setTextColor(...COLORS.medGray);
    this.doc.text(`© 2026 Vibhinetra — All Rights Reserved. Passive Network Intelligence.`, this.marginLeft, footerY);
    this.doc.text(`Page ${this.pageNumber}`, this.pageWidth - this.marginRight, footerY, { align: 'right' });
    this.doc.text(`CONFIDENTIAL — FOR AUTHORIZED PERSONNEL ONLY`, this.pageWidth / 2, footerY, { align: 'center' });
  }

  private drawSectionHeader(title: string) {
    this.checkPageBreak(14);

    // Accent bar
    this.doc.setFillColor(...COLORS.accent);
    this.doc.rect(this.marginLeft, this.y, 3, 7, 'F');

    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(11);
    this.doc.setTextColor(...COLORS.black);
    this.doc.text(title.toUpperCase(), this.marginLeft + 7, this.y + 5.5);

    // Subtle underline
    this.doc.setDrawColor(...COLORS.lightGray);
    this.doc.setLineWidth(0.3);
    this.doc.line(this.marginLeft, this.y + 9, this.pageWidth - this.marginRight, this.y + 9);

    this.y += 14;
  }

  private drawKeyValue(key: string, value: string, keyWidth: number = 42) {
    this.checkPageBreak(7);
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(8);
    this.doc.setTextColor(...COLORS.medGray);
    this.doc.text(key.toUpperCase(), this.marginLeft + 4, this.y);

    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(9);
    this.doc.setTextColor(...COLORS.black);

    // Wrap long values
    const maxWidth = this.contentWidth - keyWidth - 4;
    const lines = this.doc.splitTextToSize(value || '—', maxWidth);
    this.doc.text(lines, this.marginLeft + keyWidth, this.y);
    this.y += Math.max(6, lines.length * 4.5);
  }

  private drawParagraph(text: string, fontSize: number = 9) {
    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(fontSize);
    this.doc.setTextColor(...COLORS.darkGray);
    const lines = this.doc.splitTextToSize(text, this.contentWidth - 8);
    
    // Check if we need multiple pages
    const lineHeight = fontSize * 0.45;
    const totalHeight = lines.length * lineHeight;
    this.checkPageBreak(Math.min(totalHeight + 4, 60));
    
    this.doc.text(lines, this.marginLeft + 4, this.y);
    this.y += totalHeight + 4;
  }

  private drawSubHeading(text: string) {
    this.checkPageBreak(8);
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(8.5);
    this.doc.setTextColor(...COLORS.darkGray);
    this.doc.text(text, this.marginLeft + 4, this.y);
    this.y += 5;
  }

  private drawBulletList(items: string[]) {
    items.forEach(item => {
      this.checkPageBreak(8);
      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(8.5);
      this.doc.setTextColor(...COLORS.darkGray);

      // Bullet circle
      this.doc.setFillColor(...COLORS.accent);
      this.doc.circle(this.marginLeft + 6, this.y - 1.2, 1, 'F');

      const lines = this.doc.splitTextToSize(item, this.contentWidth - 16);
      this.doc.text(lines, this.marginLeft + 11, this.y);
      this.y += lines.length * 4 + 2;
    });
  }

  private drawSpacer(h: number = 4) {
    this.y += h;
  }

  // ─── Report Sections ──────────────────────────────

  public buildCoverHeader(alert: Alert) {
    // Top accent banner
    this.doc.setFillColor(...COLORS.accent);
    this.doc.rect(0, 0, this.pageWidth, 38, 'F');

    // Logo / title
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(22);
    this.doc.setTextColor(...COLORS.white);
    this.doc.text('VIBHINETRA', this.marginLeft, 16);

    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(9);
    this.doc.setTextColor(200, 200, 255);
    this.doc.text('Passive Network Intelligence — Incident Report', this.marginLeft, 23);

    // Report timestamp
    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(8);
    this.doc.setTextColor(180, 180, 240);
    const now = new Date();
    this.doc.text(
      `Generated: ${now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} at ${now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })} UTC`,
      this.pageWidth - this.marginRight, 16,
      { align: 'right' }
    );
    this.doc.text(
      `Alert ID: ${alert.alert_id}`,
      this.pageWidth - this.marginRight, 23,
      { align: 'right' }
    );

    // Classification banner
    this.doc.setFillColor(30, 30, 40);
    this.doc.rect(0, 38, this.pageWidth, 7, 'F');
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(7);
    this.doc.setTextColor(...COLORS.white);
    this.doc.text('CLASSIFICATION: CONFIDENTIAL — FOR AUTHORIZED PERSONNEL ONLY', this.pageWidth / 2, 43, { align: 'center' });

    this.y = 52;
  }

  public buildIncidentOverview(alert: Alert) {
    this.drawSectionHeader('Incident Overview');

    // Severity badge
    const sevColor = getSeverityColor(alert.severity);
    this.doc.setFillColor(...sevColor);
    this.doc.roundedRect(this.marginLeft + 4, this.y - 3.5, 38, 7, 1.5, 1.5, 'F');
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(7.5);
    this.doc.setTextColor(...COLORS.white);
    this.doc.text(`SEVERITY: ${alert.severity.toUpperCase()}`, this.marginLeft + 6, this.y + 1);

    // Attack name badge
    const threatName = THREAT_TYPE_LABELS[alert.threat_type] ?? alert.threat_type;
    this.doc.setFillColor(...COLORS.bgLight);
    this.doc.roundedRect(this.marginLeft + 46, this.y - 3.5, this.doc.getTextWidth(threatName) + 10, 7, 1.5, 1.5, 'F');
    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(7.5);
    this.doc.setTextColor(...COLORS.black);
    this.doc.text(threatName.toUpperCase(), this.marginLeft + 51, this.y + 1);

    this.y += 10;

    this.drawKeyValue('Alert ID', alert.alert_id);
    this.drawKeyValue('Detector', DETECTOR_LABELS[alert.detector_id] ?? alert.detector_id);
    this.drawKeyValue('Confidence', `${((alert.confidence ?? 0) * 100).toFixed(0)}%`);
    this.drawKeyValue('Status', alert.status?.replace('_', ' ').toUpperCase() ?? '—');
    this.drawKeyValue('Timestamp', new Date(alert.timestamp).toISOString());
    this.drawSpacer();
  }

  public buildIncidentContext(incident: Incident) {
    this.drawSectionHeader('Incident Context');

    // KPI row
    this.checkPageBreak(22);
    const kpis = [
      { label: 'RISK SCORE', value: `${incident.risk_score}/100` },
      { label: 'CORRELATED ALERTS', value: `${incident.member_alert_ids.length}` },
      { label: 'CURRENT STAGE', value: THREAT_TYPE_LABELS[incident.current_stage as ThreatType] || incident.current_stage || 'None' },
      { label: 'STAGE STATE', value: incident.stage_state.replace('_', ' ').toUpperCase() },
    ];
    const kpiWidth = (this.contentWidth - 12) / kpis.length;
    kpis.forEach((kpi, i) => {
      const x = this.marginLeft + 4 + i * kpiWidth;
      // Box
      this.doc.setFillColor(...COLORS.bgLight);
      this.doc.roundedRect(x, this.y, kpiWidth - 4, 18, 2, 2, 'F');
      // Label
      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(6.5);
      this.doc.setTextColor(...COLORS.medGray);
      this.doc.text(kpi.label, x + 4, this.y + 5);
      // Value
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(11);
      this.doc.setTextColor(...COLORS.black);
      this.doc.text(kpi.value, x + 4, this.y + 13);
    });
    this.y += 24;

    // Threat types present
    this.drawSubHeading('Threat Types Present');
    const threats = incident.distinct_threat_types.map(tt => THREAT_TYPE_LABELS[tt] ?? tt);
    this.doc.setFont('helvetica', 'normal');
    this.doc.setFontSize(9);
    this.doc.setTextColor(...COLORS.darkGray);
    this.doc.text(threats.join('  •  '), this.marginLeft + 4, this.y);
    this.y += 6;

    // Forecast
    if (incident.forecast_next_stage) {
      this.drawSpacer(2);
      this.checkPageBreak(12);
      this.doc.setFillColor(255, 240, 240);
      this.doc.roundedRect(this.marginLeft + 4, this.y - 3, this.contentWidth - 8, 10, 2, 2, 'F');
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(8);
      this.doc.setTextColor(...COLORS.critical);
      this.doc.text(`⚠ RISK FORECAST: Next predicted stage → ${THREAT_TYPE_LABELS[incident.forecast_next_stage as ThreatType] ?? incident.forecast_next_stage}`, this.marginLeft + 8, this.y + 3);
      this.y += 12;
    }

    this.drawSpacer();
  }

  public buildKillChainProgression(incident: Incident) {
    const KILL_CHAIN = ['recon_portscan', 'dga_dns_tunnel', 'c2_beaconing', 'encrypted_malware', 'data_exfiltration'];

    this.drawSectionHeader('Kill-Chain Progression');
    this.checkPageBreak(30);

    const stageWidth = (this.contentWidth - 8) / KILL_CHAIN.length;
    const baseX = this.marginLeft + 4;
    const circleY = this.y + 8;

    // Connecting line
    this.doc.setDrawColor(...COLORS.lightGray);
    this.doc.setLineWidth(0.8);
    this.doc.line(baseX + stageWidth / 2, circleY, baseX + stageWidth * (KILL_CHAIN.length - 0.5), circleY);

    KILL_CHAIN.forEach((stage, i) => {
      const cx = baseX + stageWidth * i + stageWidth / 2;
      const isActive = incident.distinct_threat_types.includes(stage as any);
      const isCurrent = incident.current_stage === stage;

      // Circle
      if (isActive) {
        this.doc.setFillColor(...COLORS.accent);
        this.doc.circle(cx, circleY, 5, 'F');
        this.doc.setFont('helvetica', 'bold');
        this.doc.setFontSize(7);
        this.doc.setTextColor(...COLORS.white);
        this.doc.text('✓', cx - 1.5, circleY + 2);
      } else {
        this.doc.setDrawColor(...COLORS.lightGray);
        this.doc.setLineWidth(0.8);
        this.doc.setFillColor(...COLORS.white);
        this.doc.circle(cx, circleY, 5, 'FD');
      }

      // Label
      this.doc.setFont('helvetica', isActive ? 'bold' : 'normal');
      this.doc.setFontSize(6.5);
      this.doc.setTextColor(...(isActive ? COLORS.black : COLORS.medGray));
      const label = THREAT_TYPE_LABELS[stage as ThreatType] ?? stage;
      const labelLines = this.doc.splitTextToSize(label, stageWidth - 4);
      this.doc.text(labelLines, cx, circleY + 10, { align: 'center' });

      if (isCurrent) {
        this.doc.setFont('helvetica', 'bold');
        this.doc.setFontSize(5.5);
        this.doc.setTextColor(...COLORS.accent);
        this.doc.text('CURRENT', cx, circleY + 17, { align: 'center' });
      }
    });

    this.y += 36;
    this.drawSpacer();
  }

  public buildForensicTimeline(timelineEvents: { alert: Alert; reason: string }[]) {
    this.drawSectionHeader('Forensic Investigation Timeline');

    timelineEvents.forEach((ev, index) => {
      this.checkPageBreak(22);

      const a = ev.alert;
      const sevColor = getSeverityColor(a.severity);

      // Timeline dot
      this.doc.setFillColor(...sevColor);
      this.doc.circle(this.marginLeft + 6, this.y + 2, 2.5, 'F');

      // Vertical connector
      if (index < timelineEvents.length - 1) {
        this.doc.setDrawColor(...COLORS.lightGray);
        this.doc.setLineWidth(0.4);
        this.doc.line(this.marginLeft + 6, this.y + 5, this.marginLeft + 6, this.y + 20);
      }

      // Detector + Timestamp
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(8.5);
      this.doc.setTextColor(...COLORS.black);
      this.doc.text(DETECTOR_LABELS[a.detector_id] ?? a.detector_id, this.marginLeft + 14, this.y + 2);

      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(7.5);
      this.doc.setTextColor(...COLORS.medGray);
      const ts = new Date(a.timestamp);
      this.doc.text(ts.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }), this.pageWidth - this.marginRight, this.y + 2, { align: 'right' });

      // Severity + Threat type
      this.doc.setFillColor(...sevColor);
      this.doc.roundedRect(this.marginLeft + 14, this.y + 4, 30, 5, 1, 1, 'F');
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(6);
      this.doc.setTextColor(...COLORS.white);
      this.doc.text(`SEVERITY: ${a.severity.toUpperCase()}`, this.marginLeft + 15.5, this.y + 7.5);

      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(8);
      this.doc.setTextColor(...COLORS.darkGray);
      this.doc.text(THREAT_TYPE_LABELS[a.threat_type] ?? a.threat_type, this.marginLeft + 47, this.y + 7.5);

      // Details line
      this.doc.setFont('helvetica', 'normal');
      this.doc.setFontSize(7);
      this.doc.setTextColor(...COLORS.medGray);
      const details = `SRC: ${a.src_ip || 'N/A'}  →  DST: ${a.dst_ip || 'N/A'}${a.dst_port ? ':' + a.dst_port : ''}  |  CONFIDENCE: ${((a.confidence ?? 0) * 100).toFixed(0)}%`;
      this.doc.text(details, this.marginLeft + 14, this.y + 13);

      // Correlation reason
      if (ev.reason) {
        this.doc.setFont('helvetica', 'italic');
        this.doc.setFontSize(6.5);
        this.doc.setTextColor(...COLORS.accent);
        this.doc.text(`↳ ${ev.reason}`, this.marginLeft + 14, this.y + 17);
        this.y += 22;
      } else {
        this.y += 18;
      }
    });

    this.drawSpacer(4);
  }

  public buildAiAttackStory(narrative: { what_was_observed: string; why_it_matters: string; what_to_investigate: string } | null) {
    this.drawSectionHeader('AI Attack Story');

    if (!narrative) {
      this.drawParagraph('No AI-generated narrative available for this alert.');
      return;
    }

    // Subtle background box
    this.checkPageBreak(20);

    this.drawSubHeading('What Was Observed');
    this.drawParagraph(narrative.what_was_observed);

    this.drawSubHeading('Why It Matters');
    this.drawParagraph(narrative.why_it_matters);

    this.drawSubHeading('What To Investigate');
    this.drawParagraph(narrative.what_to_investigate);

    this.drawSpacer();
  }

  public buildEventSummary(alert: Alert) {
    this.drawSectionHeader('Event Summary');

    this.drawKeyValue('Source IP', alert.src_ip ?? '—');
    this.drawKeyValue('Destination IP', alert.dst_ip ?? '—');
    this.drawKeyValue('Destination Port', alert.dst_port?.toString() ?? '—');
    this.drawKeyValue('First Observed', alert.first_seen_at ? new Date(alert.first_seen_at).toISOString() : '—');
    this.drawKeyValue('Last Observed', alert.last_seen_at ? new Date(alert.last_seen_at).toISOString() : '—');
    this.drawSpacer();
  }

  public buildExplainableEvidence(alert: Alert, explanation: string) {
    this.drawSectionHeader('Explainable Evidence Panel');

    this.drawParagraph(explanation);

    // Evidence signals table
    if (alert.evidence?.signals && Array.isArray(alert.evidence.signals)) {
      this.checkPageBreak(12);
      this.drawSpacer(2);

      // Table header
      const colWidths = [40, 30, 30, 30];
      const headers = ['Signal', 'Observation', 'Threshold', 'Trigger State'];
      let tableX = this.marginLeft + 4;

      this.doc.setFillColor(...COLORS.bgLight);
      this.doc.rect(tableX, this.y - 3, this.contentWidth - 8, 7, 'F');
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(7);
      this.doc.setTextColor(...COLORS.medGray);
      headers.forEach((h, i) => {
        const offset = colWidths.slice(0, i).reduce((a, b) => a + b, 0);
        this.doc.text(h.toUpperCase(), tableX + offset + 2, this.y + 1);
      });
      this.y += 7;

      // Table rows
      (alert.evidence.signals as any[]).forEach((sig: any) => {
        this.checkPageBreak(8);
        this.doc.setFont('helvetica', 'normal');
        this.doc.setFontSize(7.5);
        this.doc.setTextColor(...COLORS.darkGray);

        const row = [
          sig.signal_name ?? '—',
          typeof sig.value === 'number' ? sig.value.toFixed(2) : String(sig.value ?? '—'),
          typeof sig.threshold === 'number' ? sig.threshold.toFixed(2) : String(sig.threshold ?? '—'),
          sig.triggered ? 'TRIGGERED' : 'NOT TRIGGERED',
        ];

        row.forEach((cell, i) => {
          const offset = colWidths.slice(0, i).reduce((a, b) => a + b, 0);
          if (i === 3) {
            this.doc.setTextColor(...(sig.triggered ? COLORS.critical : COLORS.medGray));
            this.doc.setFont('helvetica', 'bold');
          }
          this.doc.text(cell, tableX + offset + 2, this.y);
        });

        // Light separator
        this.doc.setDrawColor(...COLORS.lightGray);
        this.doc.setLineWidth(0.15);
        this.doc.line(tableX, this.y + 2, tableX + this.contentWidth - 8, this.y + 2);
        this.y += 6;
      });
    }

    // ML Probability
    if (alert.evidence?.probability !== undefined) {
      this.drawSpacer(3);
      this.drawKeyValue('ML Probability', `${((alert.evidence.probability as number) * 100).toFixed(2)}%`);
      if (alert.evidence.threshold !== undefined) {
        this.drawKeyValue('Threshold', `${((alert.evidence.threshold as number) * 100).toFixed(2)}%`);
      }
    }

    this.drawSpacer();
  }

  public buildRecommendations(immediate: string[], preventive: string[]) {
    this.drawSectionHeader('Recommended Immediate Response');
    this.drawBulletList(immediate);
    this.drawSpacer(4);

    this.drawSectionHeader('Preventive Recommendations');
    this.drawBulletList(preventive);
    this.drawSpacer();
  }

  // ─── Finalize & Save ──────────────────────────────

  public finalize(alertId: string) {
    // Add footer to last page
    this.addFooter();

    // Generate filename
    const dateStr = new Date().toISOString().split('T')[0];
    const shortId = alertId.substring(0, 8);
    this.doc.save(`Vibhinetra_Incident_Report_${shortId}_${dateStr}.pdf`);
  }
}

// ─── Public Export Function ──────────────────────────

export interface PdfExportData {
  alert: Alert;
  incident: Incident | null;
  timelineEvents: { alert: Alert; reason: string }[];
  narrative: { what_was_observed: string; why_it_matters: string; what_to_investigate: string } | null;
  explanation: string;
  recommendations: { immediate: string[]; preventive: string[] };
}

export function exportAlertToPdf(data: PdfExportData) {
  const report = new VibhinetraPdfReport();

  // 1. Cover Header
  report.buildCoverHeader(data.alert);

  // 2. Incident Overview (severity, attack name, confidence)
  report.buildIncidentOverview(data.alert);

  // 3. Incident Context (risk score, correlated alerts, stage state)
  if (data.incident) {
    report.buildIncidentContext(data.incident);
  }

  // 4. Kill-Chain Progression
  if (data.incident) {
    report.buildKillChainProgression(data.incident);
  }

  // 5. Forensic Investigation Timeline
  if (data.timelineEvents.length > 0) {
    report.buildForensicTimeline(data.timelineEvents);
  }

  // 6. AI Attack Story
  report.buildAiAttackStory(data.narrative);

  // 7. Event Summary
  report.buildEventSummary(data.alert);

  // 8. Explainable Evidence Panel
  report.buildExplainableEvidence(data.alert, data.explanation);

  // 9. Recommended Immediate Response + Preventive Recommendations
  report.buildRecommendations(data.recommendations.immediate, data.recommendations.preventive);

  // Finalize and download
  report.finalize(data.alert.alert_id);
}
