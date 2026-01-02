import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import Members from './pages/Members'
import MemberDetail from './pages/MemberDetail'
import Chat from './pages/Chat'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/members" element={<Members />} />
        <Route path="/members/:bioguideId" element={<MemberDetail />} />
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </Layout>
  )
}

export default App
