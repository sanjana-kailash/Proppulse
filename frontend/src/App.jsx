import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import DashboardPage from './pages/DashboardPage'
import BriefPage from './pages/BriefPage'
import SettingsPage from './pages/SettingsPage'
import SuburbPage from './pages/SuburbPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-6xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/brief" element={<BriefPage />} />
            <Route path="/suburb/:name" element={<SuburbPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
