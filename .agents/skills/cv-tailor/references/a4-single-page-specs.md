# A4 Single-Page Print Layout Specification

- **Page Dimensions:** 210mm x 297mm (A4 Portrait)
- **Print Margins:** 8mm top/bottom, 11mm left/right
- **Base Typography:** 10.2pt, line-height 1.32, -apple-system / Arial
- **Main Title (Name):** 18pt bold, line-height 1.1
- **Section Titles (H2):** 11pt bold, uppercase, border-bottom 1.5px solid #0284c7, margin-top 6px, margin-bottom 3px
- **Role Titles (H3):** 10.2pt bold, margin-top 4px, margin-bottom 1px
- **Paragraphs & Bullets:** 9.6pt - 9.8pt, margin 2px 0, line-height 1.3
- **CSS Rules:**
  ```css
  @media print {
    @page { size: A4 portrait; margin: 0; }
    body { background-color: #ffffff; padding: 0; margin: 0; }
    .page-container { box-shadow: none; padding: 8mm 11mm; width: 100%; height: 100%; }
    .section-title { break-after: avoid; }
    .item-title, .cv-list li { break-inside: avoid; }
  }
  ```
