import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DailyReportPage from './pages/DailyReportPage'
import AllNewsPage from './pages/AllNewsPage'
import SourcesPage from './pages/SourcesPage'
import BookmarksPage from './pages/BookmarksPage'
import { ToastProvider } from './components/Toast'

function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DailyReportPage />} />
          <Route path="/all" element={<AllNewsPage />} />
          <Route path="/bookmarks" element={<BookmarksPage />} />
          <Route path="/sources" element={<SourcesPage />} />
        </Route>
      </Routes>
    </ToastProvider>
  )
}

export default App
