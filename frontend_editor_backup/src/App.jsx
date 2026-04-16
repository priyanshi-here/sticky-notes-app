import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'

function App() {
  const [docId, setDocId] = useState(1)
  const [content, setContent] = useState('')
  const [users, setUsers] = useState([])
  const wsRef = useRef(null)

  useEffect(() => {
    // Create document if not exists
    fetch('http://127.0.0.1:8000/documents/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
    }).then(() => fetchContent())

    // WebSocket connection
    wsRef.current = new WebSocket(`ws://127.0.0.1:8000/ws/${docId}`)
    
    wsRef.current.onopen = () => console.log('Connected to collab editor')
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'delta') {
        setContent(prev => prev + data.delta.content)
      } else if (data.type === 'init') {
        setContent(data.content)
      }
    }

    return () => wsRef.current?.close()
  }, [docId])

  const fetchContent = async () => {
    const res = await fetch(`http://127.0.0.1:8000/documents/${docId}/content`)
    const data = await res.json()
    setContent(data.content)
  }

  const handleChange = (value) => {
    setContent(value)
    // Send delta to server
    const delta = {
      op_id: Date.now(),
      content: value.slice(-1), // Last char as simple delta
      cursor: 5,
      user_id: 'user1'
    }
    fetch(`http://127.0.0.1:8000/documents/${docId}/delta`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(delta)
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Collaborative Text Editor
        </h1>
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="flex gap-4 mb-6">
            <select 
              value={docId}
              onChange={(e) => setDocId(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Document 1</option>
              <option value={2}>Document 2</option>
            </select>
            <button 
              onClick={fetchContent}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
          
          <div className="h-[70vh] border-2 border-gray-200 rounded-xl overflow-hidden shadow-inner">
            <Editor
              height="100%"
              language="markdown"
              value={content}
              onChange={handleChange}
              theme="vs-light"
              options={{
                minimap: { enabled: false },
                fontSize: 16,
                wordWrap: 'on',
                cursorBlinking: 'smooth'
              }}
            />
          </div>
          
          <div className="mt-6 p-4 bg-gray-50 rounded-xl">
            <h3 className="font-semibold text-gray-900 mb-2">Active Users: {users.length}</h3>
            <p className="text-sm text-gray-600">Real-time collaboration enabled via WebSocket</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

