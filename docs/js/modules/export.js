/**
 * export.js - Streamlined CSV/Excel Exporter
 * Generates RFC 4180 compliant CSV with UTF-8 BOM for seamless Hebrew display in Excel.
 * Implements security guards against CSV Formula Injection.
 */

import { store } from './store.js';

export function exportSavedToExcel() {
  const allPotentialSaved = store.getAllAvailableJobs();
  const savedJobs = allPotentialSaved.filter(job => store.getJobState(job.link) === 'saved');

  if (savedJobs.length === 0) {
    if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
      window.showToast('ph-warning', 'לא נמצאו משרות שמורות לייצוא');
    }
    return;
  }

  const BOM = '\uFEFF';
  const headers = [
    'חברה',
    'כותרת משרה',
    'ציון התאמה',
    'תחום',
    'מיקום',
    'טווח שכר צפוי',
    'ביסוס ומקור שכר',
    'דרישות החברה עבור המשרה',
    'תחום ומוצר החברה',
    'תקציר המשרה',
    'נקודות חוזק מהניסיון',
    'דגשים ומודל עבודה',
    'לינק למשרה',
    'תאריך איתור'
  ];

  const escapeCSV = (val) => {
    if (val === null || val === undefined) return '""';
    // Formula Injection Prevention: Prepend single quote if cell starts with formula characters
    const str = String(val).replace(/^[=+@\-\t\r]/, "'$&").replace(/"/g, '""');
    return `"${str}"`;
  };

  const rows = savedJobs.map(job => {
    const score = job.match_score || '';
    const reqs = job.company_requirements || '';
    const domain = job.company_domain_product || job.company_summary || '';
    const summary = job.job_summary || job.company_summary || '';
    const strengths = job.experience_strengths || job.reasoning || '';
    const highlights = job.key_highlights || (job.work_model ? `מודל: ${job.work_model}` : '');
    const date = job.date || '';
    let salaryStr = job.salary_range || 'לא צוין';
    if (job.salary_source_label) {
      salaryStr += ` (${job.salary_source_label})`;
    }
    const salaryEvidence = job.salary_evidence || '';

    return [
      escapeCSV(job.company || ''),
      escapeCSV(job.title || ''),
      escapeCSV(score),
      escapeCSV(job.sector || job.sector_key || ''),
      escapeCSV(job.location || 'ישראל'),
      escapeCSV(salaryStr),
      escapeCSV(salaryEvidence),
      escapeCSV(reqs),
      escapeCSV(domain),
      escapeCSV(summary),
      escapeCSV(strengths),
      escapeCSV(highlights),
      escapeCSV(job.link || ''),
      escapeCSV(date)
    ].join(',');
  });

  const csvContent = BOM + [headers.map(escapeCSV).join(','), ...rows].join(String.fromCharCode(13, 10));
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const dateStr = new Date().toISOString().slice(0, 10);
  a.href = url;
  a.download = `משרות_שמורות_עידו_גל_${dateStr}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
    window.showToast('ph-file-xls', `יוצאו ${savedJobs.length} משרות שמורות לאקסל בהצלחה!`);
  }
}

// Window export
if (typeof window !== 'undefined') {
  window.exportSavedToExcel = exportSavedToExcel;
}
