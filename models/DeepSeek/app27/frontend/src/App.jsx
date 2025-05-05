import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [currentPage, setCurrentPage] = useState('login');
  const [user, setUser] = useState(null);
  const [teams, setTeams] = useState([]);
  const [players, setPlayers] = useState([]);
  const [trainingSessions, setTrainingSessions] = useState([]);
  
  // Form states
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', password: '' });
  const [teamForm, setTeamForm] = useState({ name: '', sport: 'Football' });
  const [playerForm, setPlayerForm] = useState({
    name: '',
    position: '',
    dob: '',
    team_id: '',
    jersey_number: '',
    height: '',
    weight: ''
  });
  const [trainingForm, setTrainingForm] = useState({
    team_id: '',
    date: '',
    time: '',
    location: '',
    focus_area: 'General',
    notes: ''
  });
  
  // Selected states
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);

  // Stats modal
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [statsForm, setStatsForm] = useState({});

  // API Helper
  const apiRequest = async (endpoint, method = 'GET', data = null) => {
    try {
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      };
      
      if (data) {
        options.body = JSON.stringify(data);
      }
      
      const response = await fetch(`http://localhost:5213${endpoint}`, options);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Request failed');
      }
      
      return await response.json();
    } catch (error) {
      alert(error.message);
      throw error;
    }
  };

  // Fetch data functions
  const fetchTeams = async () => {
    try {
      const data = await apiRequest('/api/teams');
      setTeams(data);
    } catch (error) {
      console.error('Failed to fetch teams:', error);
    }
  };

  const fetchPlayers = async (teamId = null) => {
    try {
      const endpoint = teamId ? `/api/players?team_id=${teamId}` : '/api/players';
      const data = await apiRequest(endpoint);
      setPlayers(data);
    } catch (error) {
      console.error('Failed to fetch players:', error);
    }
  };

  const fetchTrainingSessions = async (teamId = null) => {
    try {
      const endpoint = teamId ? `/api/training-sessions?team_id=${teamId}` : '/api/training-sessions';
      const data = await apiRequest(endpoint);
      setTrainingSessions(data);
    } catch (error) {
      console.error('Failed to fetch training sessions:', error);
    }
  };

  // Auth functions
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await apiRequest('/api/login', 'POST', loginForm);
      setUser(data.user);
      setCurrentPage('dashboard');
      await fetchTeams();
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/register', 'POST', registerForm);
      alert('Registration successful! Please log in.');
      setCurrentPage('login');
      setRegisterForm({ username: '', password: '' });
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await apiRequest('/api/logout', 'POST');
      setUser(null);
      setCurrentPage('login');
      setTeams([]);
      setPlayers([]);
      setTrainingSessions([]);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Team functions
  const createTeam = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/teams', 'POST', teamForm);
      setTeamForm({ name: '', sport: 'Football' });
      await fetchTeams();
    } catch (error) {
      console.error('Team creation failed:', error);
    }
  };

  const deleteTeam = async (teamId) => {
    if (window.confirm('Are you sure you want to delete this team?')) {
      try {
        await apiRequest(`/api/teams/${teamId}`, 'DELETE');
        await fetchTeams();
        setSelectedTeam(null);
      } catch (error) {
        console.error('Team deletion failed:', error);
      }
    }
  };

  // Player functions
  const createPlayer = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/players', 'POST', playerForm);
      setPlayerForm({
        name: '',
        position: '',
        dob: '',
        team_id: '',
        jersey_number: '',
        height: '',
        weight: ''
      });
      await fetchPlayers(selectedTeam?.id);
    } catch (error) {
      console.error('Player creation failed:', error);
    }
  };

  const updatePlayer = async (e) => {
    e.preventDefault();
    try {
      await apiRequest(`/api/players/${selectedPlayer.id}`, 'PUT', playerForm);
      setSelectedPlayer(null);
      setPlayerForm({
        name: '',
        position: '',
        dob: '',
        team_id: '',
        jersey_number: '',
        height: '',
        weight: ''
      });
      await fetchPlayers(selectedTeam?.id);
    } catch (error) {
      console.error('Player update failed:', error);
    }
  };

  const deletePlayer = async (playerId) => {
    if (window.confirm('Are you sure you want to delete this player?')) {
      try {
        await apiRequest(`/api/players/${playerId}`, 'DELETE');
        await fetchPlayers(selectedTeam?.id);
        setSelectedPlayer(null);
      } catch (error) {
        console.error('Player deletion failed:', error);
      }
    }
  };

  const addPlayerStats = async (e) => {
    e.preventDefault();
    try {
      await apiRequest(`/api/players/${selectedPlayer.id}/stats`, 'POST', statsForm);
      setShowStatsModal(false);
      setStatsForm({});
      await fetchPlayers(selectedTeam?.id);
    } catch (error) {
      console.error('Failed to add stats:', error);
    }
  };

  // Training session functions
  const createTrainingSession = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/training-sessions', 'POST', trainingForm);
      setTrainingForm({
        team_id: '',
        date: '',
        time: '',
        location: '',
        focus_area: 'General',
        notes: ''
      });
      await fetchTrainingSessions(selectedTeam?.id);
    } catch (error) {
      console.error('Training session creation failed:', error);
    }
  };

  const deleteTrainingSession = async (sessionId) => {
    if (window.confirm('Are you sure you want to delete this training session?')) {
      try {
        await apiRequest(`/api/training-sessions/${sessionId}`, 'DELETE');
        await fetchTrainingSessions(selectedTeam?.id);
        setSelectedSession(null);
      } catch (error) {
        console.error('Training session deletion failed:', error);
      }
    }
  };

  // Form handlers
  const handleTeamSelect = (team) => {
    setSelectedTeam(team);
    setPlayerForm(prev => ({ ...prev, team_id: team.id }));
    setTrainingForm(prev => ({ ...prev, team_id: team.id }));
    fetchPlayers(team.id);
    fetchTrainingSessions(team.id);
  };

  const handlePlayerSelect = (player) => {
    setSelectedPlayer(player);
    setPlayerForm({
      name: player.name,
      position: player.position,
      dob: player.dob,
      team_id: player.team_id,
      jersey_number: player.jersey_number || '',
      height: player.height || '',
      weight: player.weight || ''
    });
  };

  const handleSessionSelect = (session) => {
    setSelectedSession(session);
    setTrainingForm({
      team_id: session.team_id,
      date: session.date,
      time: session.time,
      location: session.location,
      focus_area: session.focus_area,
      notes: session.notes
    });
  };

  // UseEffect for initial data
  useEffect(() => {
    if (currentPage === 'login' || currentPage === 'register') {
      // Check if user is already logged in
      apiRequest('/api/user').then(data => {
        if (data.user) {
          setUser(data.user);
          setCurrentPage('dashboard');
          fetchTeams();
        }
      }).catch(console.error);
    }
  }, [currentPage]);

  // Navigation
  const navigateTo = (page) => {
    setCurrentPage(page);
    
    // Reset forms when navigating away
    if (page !== 'players' && page !== 'training') {
      setSelectedTeam(null);
      setSelectedPlayer(null);
      setSelectedSession(null);
    }
  };

  // Render methods
  const renderLogin = () => (
    <div className="auth-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label>Username:</label>
          <input 
            type="text" 
            value={loginForm.username} 
            onChange={(e) => setLoginForm({...loginForm, username: e.target.value})} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            value={loginForm.password} 
            onChange={(e) => setLoginForm({...loginForm, password: e.target.value})} 
            required 
          />
        </div>
        <button type="submit">Login</button>
        <button type="button" className="link" onClick={() => setCurrentPage('register')}>
          Don't have an account? Register here
        </button>
      </form>
    </div>
  );

  const renderRegister = () => (
    <div className="auth-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label>Username:</label>
          <input 
            type="text" 
            value={registerForm.username} 
            onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})} 
            required 
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            value={registerForm.password} 
            onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})} 
            required 
          />
        </div>
        <button type="submit">Register</button>
        <button type="button" className="link" onClick={() => setCurrentPage('login')}>
          Already have an account? Login here
        </button>
      </form>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard">
      <h2>Welcome, {user?.username}!</h2>
      <div className="dashboard-cards">
        <div className="dashboard-card" onClick={() => navigateTo('teams')}>
          <h3>Teams</h3>
          <p>{teams.length} team{teams.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="dashboard-card" onClick={() => navigateTo('players')}>
          <h3>Players</h3>
          <p>{players.length} player{players.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="dashboard-card" onClick={() => navigateTo('training')}>
          <h3>Training Sessions</h3>
          <p>{trainingSessions.length} session{trainingSessions.length !== 1 ? 's' : ''}</p>
        </div>
      </div>
    </div>
  );

  const renderTeams = () => (
    <div className="teams-container">
      <div className="teams-sidebar">
        <h3>My Teams</h3>
        {teams.map(team => (
          <div 
            key={team.id} 
            className={`team-item ${selectedTeam?.id === team.id ? 'active' : ''}`}
            onClick={() => handleTeamSelect(team)}
          >
            {team.name} ({team.sport})
          </div>
        ))}
        <button 
          className="add-button" 
          onClick={() => {
            setSelectedTeam(null);
            setTeamForm({ name: '', sport: 'Football' });
          }}
        >
          + Add New Team
        </button>
      </div>
      
      <div className="team-details">
        {selectedTeam ? (
          <>
            <h2>{selectedTeam.name} Details</h2>
            <p>Sport: {selectedTeam.sport}</p>
            <p>Created: {new Date(selectedTeam.created_at).toLocaleDateString()}</p>
            
            <div className="action-buttons">
              <button className="edit-button">Edit Team</button>
              <button 
                className="delete-button"
                onClick={() => deleteTeam(selectedTeam.id)}
              >
                Delete Team
              </button>
            </div>
            
            <div className="sub-navigation">
              <button onClick={() => navigateTo('players')}>Players</button>
              <button onClick={() => navigateTo('training')}>Training</button>
            </div>
          </>
        ) : (
          <div className="team-form">
            <h2>Create New Team</h2>
            <form onSubmit={createTeam}>
              <div className="form-group">
                <label>Team Name:</label>
                <input 
                  type="text" 
                  value={teamForm.name} 
                  onChange={(e) => setTeamForm({...teamForm, name: e.target.value})} 
                  required 
                />
              </div>
              <div className="form-group">
                <label>Sport:</label>
                <select 
                  value={teamForm.sport} 
                  onChange={(e) => setTeamForm({...teamForm, sport: e.target.value})}
                >
                  <option value="Football">Football</option>
                  <option value="Basketball">Basketball</option>
                  <option value="Soccer">Soccer</option>
                  <option value="Baseball">Baseball</option>
                  <option value="Hockey">Hockey</option>
                  <option value="Volleyball">Volleyball</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <button type="submit">Create Team</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );

  const renderPlayers = () => {
    if (!selectedTeam) {
      return (
        <div className="notice-container">
          <p>Please select a team first to view or add players.</p>
          <button onClick={() => navigateTo('teams')}>Back to Teams</button>
        </div>
      );
    }

    return (
      <div className="players-container">
        <div className="players-list">
          <h3>Players for {selectedTeam.name}</h3>
          {players.length > 0 ? (
            <table className="players-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Name</th>
                  <th>Position</th>
                  <th>Age</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {players.map(player => (
                  <tr 
                    key={player.id} 
                    className={selectedPlayer?.id === player.id ? 'active' : ''}
                    onClick={() => handlePlayerSelect(player)}
                  >
                    <td>{player.jersey_number || '-'}</td>
                    <td>{player.name}</td>
                    <td>{player.position}</td>
                    <td>{player.age}</td>
                    <td>
                      <button 
                        className="small-button"
                        onClick={() => {
                          handlePlayerSelect(player);
                          setShowStatsModal(true);
                        }}
                      >
                        Stats
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No players found for this team.</p>
          )}
          
          <button 
            className="add-button"
            onClick={() => {
              setSelectedPlayer(null);
              setPlayerForm({
                name: '',
                position: '',
                dob: '',
                team_id: selectedTeam.id,
                jersey_number: '',
                height: '',
                weight: ''
              });
            }}
          >
            + Add New Player
          </button>
        </div>
        
        <div className="player-details">
          {selectedPlayer ? (
            <>
              <h2>{selectedPlayer.name}</h2>
              <div className="player-info">
                <div>
                  <strong>Position:</strong> {selectedPlayer.position}
                </div>
                <div>
                  <strong>Age:</strong> {selectedPlayer.age}
                </div>
                <div>
                  <strong>Jersey:</strong> {selectedPlayer.jersey_number || 'N/A'}
                </div>
                <div>
                  <strong>Height:</strong> {selectedPlayer.height || 'N/A'}
                </div>
                <div>
                  <strong>Weight:</strong> {selectedPlayer.weight || 'N/A'}
                </div>
              </div>
              
              {Object.keys(selectedPlayer.stats).length > 0 && (
                <div className="player-stats">
                  <h3>Statistics</h3>
                  <ul>
                    {Object.entries(selectedPlayer.stats).map(([stat, value]) => (
                      <li key={stat}>
                        <strong>{stat}:</strong> {value}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="action-buttons">
                <button className="edit-button">Edit Player</button>
                <button 
                  className="delete-button"
                  onClick={() => deletePlayer(selectedPlayer.id)}
                >
                  Delete Player
                </button>
              </div>
            </>
          ) : (
            <div className="player-form">
              <h2>Add New Player to {selectedTeam.name}</h2>
              <form onSubmit={createPlayer}>
                <div className="form-group">
                  <label>Full Name:</label>
                  <input 
                    type="text" 
                    value={playerForm.name} 
                    onChange={(e) => setPlayerForm({...playerForm, name: e.target.value})} 
                    required 
                  />
                </div>
                <div className="form-group">
                  <label>Position:</label>
                  <input 
                    type="text" 
                    value={playerForm.position} 
                    onChange={(e) => setPlayerForm({...playerForm, position: e.target.value})} 
                    required 
                  />
                </div>
                <div className="form-group">
                  <label>Date of Birth:</label>
                  <input 
                    type="date" 
                    value={playerForm.dob} 
                    onChange={(e) => setPlayerForm({...playerForm, dob: e.target.value})} 
                    required 
                  />
                </div>
                <div className="form-group">
                  <label>Jersey Number:</label>
                  <input 
                    type="number" 
                    value={playerForm.jersey_number} 
                    onChange={(e) => setPlayerForm({...playerForm, jersey_number: e.target.value})} 
                  />
                </div>
                <div className="form-group">
                  <label>Height (cm):</label>
                  <input 
                    type="number" 
                    value={playerForm.height} 
                    onChange={(e) => setPlayerForm({...playerForm, height: e.target.value})} 
                  />
                </div>
                <div className="form-group">
                  <label>Weight (kg):</label>
                  <input 
                    type="number" 
                    value={playerForm.weight} 
                    onChange={(e) => setPlayerForm({...playerForm, weight: e.target.value})} 
                  />
                </div>
                <button type="submit">Add Player</button>
              </form>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderTraining = () => {
    if (!selectedTeam) {
      return (
        <div className="notice-container">
          <p>Please select a team first to view or schedule training sessions.</p>
          <button onClick={() => navigateTo('teams')}>Back to Teams</button>
        </div>
      );
    }

    return (
      <div className="training-container">
        <div className="training-list">
          <h3>Upcoming Training for {selectedTeam.name}</h3>
          
          {trainingSessions.length > 0 ? (
            <div className="sessions-grid">
              {trainingSessions.map(session => (
                <div 
                  key={session.id} 
                  className={`session-card ${selectedSession?.id === session.id ? 'active' : ''}`}
                  onClick={() => handleSessionSelect(session)}
                >
                  <h4>{session.focus_area}</h4>
                  <p><strong>Date:</strong> {session.date}</p>
                  <p><strong>Time:</strong> {session.time}</p>
                  <p><strong>Location:</strong> {session.location}</p>
                </div>
              ))}
            </div>
          ) : (
            <p>No training sessions scheduled for this team.</p>
          )}
          
          <button 
            className="add-button"
            onClick={() => {
              setSelectedSession(null);
              setTrainingForm({
                team_id: selectedTeam.id,
                date: '',
                time: '',
                location: '',
                focus_area: 'General',
                notes: ''
              });
            }}
          >
            + Schedule New Session
          </button>
        </div>
        
        <div className="training-details">
          {selectedSession ? (
            <>
              <h2>{selectedSession.focus_area} Session</h2>
              <div className="session-info">
                <div>
                  <strong>Date:</strong> {selectedSession.date}
                </div>
                <div>
                  <strong>Time:</strong> {selectedSession.time}
                </div>
                <div>
                  <strong>Location:</strong> {selectedSession.location}
                </div>
                <div>
                  <strong>Focus Area:</strong> {selectedSession.focus_area}
                </div>
                <div>
                  <strong>Notes:</strong> {selectedSession.notes || 'None'}
                </div>
              </div>
              
              <div className="action-buttons">
                <button className="edit-button">Edit Session</button>
                <button 
                  className="delete-button"
                  onClick={() => deleteTrainingSession(selectedSession.id)}
                >
                  Cancel Session
                </button>
              </div>
            </>
          ) : (
            <div className="training-form">
              <h2>Schedule New Training Session</h2>
              <form onSubmit={createTrainingSession}>
                <div className="form-group">
                 
<label>Date:</label>
              <input 
                type="date" 
                value={trainingForm.date} 
                onChange={(e) => setTrainingForm({...trainingForm, date: e.target.value})} 
                required 
              />
            </div>
            <div className="form-group">
              <label>Time:</label>
              <input 
                type="time" 
                value={trainingForm.time} 
                onChange={(e) => setTrainingForm({...trainingForm, time: e.target.value})} 
                required 
              />
            </div>
            <div className="form-group">
              <label>Location:</label>
              <input 
                type="text" 
                value={trainingForm.location} 
                onChange={(e) => setTrainingForm({...trainingForm, location: e.target.value})} 
                required 
              />
            </div>
            <div className="form-group">
              <label>Focus Area:</label>
              <select 
                value={trainingForm.focus_area} 
                onChange={(e) => setTrainingForm({...trainingForm, focus_area: e.target.value})}
              >
                <option value="General">General</option>
                <option value="Offense">Offense</option>
                <option value="Defense">Defense</option>
                <option value="Fitness">Fitness</option>
                <option value="Skills">Skills</option>
                <option value="Strategy">Strategy</option>
              </select>
            </div>
            <div className="form-group">
              <label>Notes:</label>
              <textarea 
                value={trainingForm.notes} 
                onChange={(e) => setTrainingForm({...trainingForm, notes: e.target.value})}
              />
            </div>
            <button type="submit">Schedule Training</button>
          </form>
        </div>
      )}
    </div>
  </div>
);

};

const renderStatsModal = () => (

Add Player Statistics
Stat Name: <input type="text" value={statsForm.name || ''} onChange={(e) => setStatsForm({...statsForm, name: e.target.value})} required /> Value: <input type="text" value={statsForm.value || ''} onChange={(e) => setStatsForm({...statsForm, value: e.target.value})} required /> Save <button type="button" onClick={() => setShowStatsModal(false)}>Cancel );
// Main render
return (

{!user ? ( currentPage === 'login' ? renderLogin() : renderRegister() ) : (
Sports Team Manager
Hello, {user.username} Logout
      <nav className="main-nav">
        <button 
          className={currentPage === 'dashboard' ? 'active' : ''}
          onClick={() => navigateTo('dashboard')}
        >
          Dashboard
        </button>
        <button 
          className={currentPage === 'teams' ? 'active' : ''}
          onClick={() => navigateTo('teams')}
        >
          Teams
        </button>
        <button 
          className={currentPage === 'players' ? 'active' : ''}
          onClick={() => navigateTo('players')}
        >
          Players
        </button>
        <button 
          className={currentPage === 'training' ? 'active' : ''}
          onClick={() => navigateTo('training')}
        >
          Training
        </button>
      </nav>
      
      <main className="main-content">
        {currentPage === 'dashboard' && renderDashboard()}
        {currentPage === 'teams' && renderTeams()}
        {currentPage === 'players' && renderPlayers()}
        {currentPage === 'training' && renderTraining()}
      </main>
    </div>
  )}
  
  {showStatsModal && renderStatsModal()}
</div>

);
};

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render();
