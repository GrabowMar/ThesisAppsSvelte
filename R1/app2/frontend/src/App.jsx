import { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import io from 'socket.io-client'
import { FiSend, FiUsers, FiMessageSquare } from 'react-icons/fi'
import './App.css'

const App = () => {
  const [view, setView] = useState('login')
  const [username, setUsername] = useState('')
  const [currentRoom, setCurrentRoom] = useState('')
  const [messageInput, setMessageInput] = useState('')
  const [messages, setMessages] = useState([])
  const [onlineUsers, setOnlineUsers] = useState([])
  const [socket, setSocket] = useState(null)
  const [availableRooms] = useState(['general', 'random'])

  useEffect(() => {
    const newSocket = io('http://localhost:5563')
    setSocket(newSocket)

    newSocket.on('connect_error', (err) => {
      console.error('Connection error:', err)
      alert('Failed to connect to server')
    })

    newSocket.on('new_message', (message) => {
      setMessages(prev => [...prev, message])
    })

    newSocket.on('user_joined', (data) => {
      setOnlineUsers(data.users)
      setMessages(prev => [...prev, {
        content: `${data.username} joined the room`,
        timestamp: data.timestamp,
        system: true
      }])
    })

    newSocket.on('user_left', (data) => {
      setOnlineUsers(prev => prev.filter(u => u.username !== data.username))
      setMessages(prev => [...prev, {
        content: `${data.username} left the room`,
        system: true
      }])
    })

    return () => newSocket.disconnect()
  }, [])

  const handleLogin = (e) => {
    e.preventDefault()
    if (username.trim()) {
      setView('room-select')
    }
  }

  const joinRoom = (room) => {
    socket.emit('join_room', {
      username: username,
      room: room
    }, (response) => {
      setCurrentRoom(room)
      setView('chat')
      setMessages(response.messages)
      setOnlineUsers(response.users)
    })
  }

  const sendMessage = (e) => {
    e.preventDefault()
    if (messageInput.trim()) {
      socket.emit('send_message', {
        content: messageInput,
        room: currentRoom
      })
      setMessageInput('')
    }
  }

  return (
    <div className="app-container">
      {view === 'login' && (
        <div className="auth-form">
          <h1>Chat Login</h1>
          <form onSubmit={handleLogin}>
            <input
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <button type="submit">Join Chat</button>
          </form>
        </div>
      )}

      {view === 'room-select' && (
        <div className="room-select">
          <h2>Choose a Room</h2>
          <div className="room-list">
            {availableRooms.map(room => (
              <div key={room} className="room-card" onClick={() => joinRoom(room)}>
                <FiMessageSquare />
                <h3>{room.charAt(0).toUpperCase() + room.slice(1)}</h3>
              </div>
            ))}
          </div>
        </div>
      )}

      {view === 'chat' && (
        <div className="chat-container">
          <div className="chat-header">
            <h2>{currentRoom}</h2>
            <div className="online-count">
              <FiUsers /> {onlineUsers.length} online
            </div>
          </div>
          
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.system ? 'system' : ''}`}>
                {!msg.system && (
                  <div className="message-header">
                    <span className="username">{msg.username}</span>
                    <span className="timestamp">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                )}
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
          </div>

          <form className="message-input" onSubmit={sendMessage}>
            <input
              type="text"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder="Type a message..."
            />
            <button type="submit">
              <FiSend />
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

// Mounting Logic
const root = createRoot(document.getElementById('root'))
root.render(<App />)
