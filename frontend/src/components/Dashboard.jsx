// Dashboard.jsx — Main dashboard component (agent's portfolio overview)
//
// Props:
//   suburbs: array of suburb data objects from GET /api/dashboard
//   onGenerateBrief: function — called when "Generate This Week's Brief" is clicked
//   isGenerating: bool — shows loading state on the button while API call is in progress
//
// Renders:
//   - A header section: "Good morning, [Agent Name]. Here's your market snapshot."
//   - A responsive grid of SuburbCard components (one per suburb in portfolio)
//   - A prominent "Generate This Week's Brief" CTA button
//   - Last updated timestamp (from suburb data)
//
// Data flow:
//   DashboardPage fetches data from /api/dashboard and passes it as props here.
//   onGenerateBrief triggers POST /api/generate-brief in DashboardPage.
