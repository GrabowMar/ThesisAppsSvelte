import { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'

function App() {
  // State Management
  const [devices, setDevices] = useState([])
  const [newDevice, setNewDevice] = useState({ name: '', type: 'climate' })
  const [stats, setStats] = useState(null)
  const [currentView, setCurrentView] = useState('dashboard')

  // Lifecycle Functions
  useEffect(() => {
    fetchDevices()
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  // API Calls
  const fetchDevices = async () => {
    try {
      const response = await fetch('/api/devices')
      const data = await response.json()
      setDevices(data.devices)
    } catch (error) {
      console.error('Error fetching devices:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const sendCommand = async (deviceId, command) => {
    try {
      await fetch(`/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      })
      fetchDevices()
    } catch (error) {
      console.error('Command failed:', error)
    }
  }

  const addDevice = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/devices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newDevice)
      })
      if (response.ok) {
        setNewDevice({ name: '', type: 'climate' })
        fetchDevices()
      }
    } catch (error) {
      console.error('Add device failed:', error)
    }
  }

  // View Components
  const DashboardView = () => (
    <div className="dashboard">
      <h2>System Overview</h2>
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Devices</h3>
            <p>{stats.total_devices}</p>
          </div>
          <div className="stat-card">
            <h3>Online Devices</h3>
            <p>{stats.online_devices}</p>
          </div>
        </div>
      )}
      <div className="device-grid">
        {devices.map(device =>
          <DeviceCard key={device.id} device={device} sendCommand={sendCommand} />
        )}
      </div>
    </div>
  )

  const DeviceCard = ({ device }) => (
    <div className={`device-card ${device.status}`}>
      <div className="status-indicator"></div>
      <h3>{device.name}</h3>
      <p>Type: {device.type}</p>
      <p>Status: {device.status}</p>
      <div className="controls">
        <button onClick={() => sendCommand(device.id, 'toggle')}>
          Toggle Status
        </button>
        {device.type === 'security' &&
          <button onClick={() => sendCommand(device.id, 'record')}>
            {device.recording ? 'Stop Recording' : 'Start Recording'}
          </button>
        }
      </div>
    </div>
  )

  const AddDeviceView = () => (
    <div className="form-container">
      <h2>Add New Device</h2>
      <form onSubmit={addDevice}>
        <label>
          Device Name:
          <input
            type="text"
            value={newDevice.name}
            onChange={e => setNewDevice({...newDevice, name: e.target.value})}
            required
          />
        </label>
        <label>
          Device Type:
          <select
            value={newDevice.type}
            onChange={e => setNewDevice({...newDevice, type: e.target.value})}
          >
            <option value="climate">Climate</option>
            <option value="security">Security</option>
          </select>
        </label>
        <button type="submit">Add Device</button>
      </form>
    </div>
  )

  return (
    <main>
      <nav className="main-nav">
        <button onClick={() => setCurrentView('dashboard')}>Dashboard</button>
        <button onClick={() => setCurrentView('add-device')}>Add Device</button>
      </nav>

      {currentView === 'dashboard' && <DashboardView />}
      {currentView === 'add-device' && <AddDeviceView />}
    </main>
  )
}

// Mount React
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)
