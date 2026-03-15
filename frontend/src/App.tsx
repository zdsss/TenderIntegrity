import { BrowserRouter, Routes, Route } from 'react-router-dom'
import PageLayout from './components/PageLayout'
import UploadPage from './pages/UploadPage'
import TaskHistoryPage from './pages/TaskHistoryPage'
import ReportPage from './pages/ReportPage'
import { UploadSessionProvider } from './context/UploadSessionContext'

export default function App() {
  return (
    <BrowserRouter>
      <UploadSessionProvider>
        <Routes>
          <Route element={<PageLayout />}>
            <Route index element={<UploadPage />} />
            <Route path="tasks" element={<TaskHistoryPage />} />
            <Route path="tasks/:taskId/report" element={<ReportPage />} />
          </Route>
        </Routes>
      </UploadSessionProvider>
    </BrowserRouter>
  )
}
