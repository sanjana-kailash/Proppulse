// Settings.jsx — Agent profile and portfolio configuration panel
//
// Props:
//   settings: object — current settings loaded from localStorage or /api/settings
//     { agent_name, agency, suburbs: [], tone: "formal" | "conversational" }
//   onSave: function(newSettings) — called with updated settings object
//
// Renders:
//   - Agent Profile section:
//       - Text inputs: Agent Name, Agency Name
//   - Suburb Portfolio section:
//       - List of currently selected suburbs with remove (x) buttons
//       - Searchable dropdown/combobox to add new Melbourne suburbs
//       - Validation: max 8 suburbs, min 1
//   - Newsletter Tone section:
//       - Toggle/radio: "Formal" vs "Conversational"
//       - Preview blurb showing how each tone sounds
//   - Save button — calls onSave with updated state
//
// Notes:
//   - Suburb list sourced from GET /api/suburbs
//   - Settings persisted to localStorage for MVP (no backend auth)
