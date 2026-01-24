import { Routes, Route } from 'react-router-dom'
import DashboardLayout from './components/layout/DashboardLayout'
import DashboardPage from './pages/Dashboard'
import BusinessSearchPage from './pages/BusinessSearch'
import BusinessDetailPage from './pages/BusinessDetail'
import TransactionsPage from './pages/Transactions'
import GraphExplorerPage from './pages/GraphExplorer'
import RiskAnalysisPage from './pages/RiskAnalysis'
import FraudAlertsPage from './pages/FraudAlerts'
import WorkflowsPage from './pages/Workflows'
import AuditLogsPage from './pages/AuditLogs'
import SettingsPage from './pages/Settings'
import AdminPage from './pages/Admin'
import LoginPage from './pages/Login'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <DashboardLayout>
            <Routes>
              <Route index element={<DashboardPage />} />
              <Route path="businesses" element={<BusinessSearchPage />} />
              <Route path="businesses/:id" element={<BusinessDetailPage />} />
              <Route path="transactions" element={<TransactionsPage />} />
              <Route path="graph" element={<GraphExplorerPage />} />
              <Route path="risk" element={<RiskAnalysisPage />} />
              <Route path="fraud" element={<FraudAlertsPage />} />
              <Route path="workflows" element={<WorkflowsPage />} />
              <Route path="audit" element={<AuditLogsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="admin" element={<AdminPage />} />
            </Routes>
          </DashboardLayout>
        }
      />
    </Routes>
  )
}

export default App
