import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { WeeklyLog } from '@/pages/WeeklyLog'
import { ModelChangelog } from '@/pages/ModelChangelog'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<WeeklyLog />} />
          <Route path="model/:modelName" element={<ModelChangelog />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
