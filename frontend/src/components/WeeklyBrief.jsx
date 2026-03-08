// WeeklyBrief.jsx — Renders the full AI-generated weekly market brief
//
// Props:
//   brief: object with shape:
//     {
//       week: string (e.g. "Week ending 7 March 2026"),
//       suburbs: [
//         {
//           name, median_price, clearance_rate, days_on_market,
//           narrative, top_themes: [string x3], outlook, sources: [string]
//         }
//       ]
//     }
//   onExportPDF: function — triggers PDF export (uses window.print() or react-to-pdf)
//
// Renders:
//   - PropPulse branded header with week label and agent name
//   - For each suburb: a formatted section with:
//       - Suburb name + divider
//       - Market Snapshot (3 metric badges)
//       - Weekly Narrative (AI-generated paragraph)
//       - Top 3 Themes (tag pills)
//       - Outlook (italicised forward-looking sentence)
//       - Sources cited (small grey text)
//   - "Export to PDF" button (top right)
//
// Style: Clean, print-friendly layout — white background, clear typography hierarchy
// Note: Wrap in a ref for PDF export targeting
