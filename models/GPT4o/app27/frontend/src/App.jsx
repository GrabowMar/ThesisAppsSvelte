import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [view, setView] = useState('dashboard'); // Available views: 'dashboard', 'schedule', 'addPlayer'
  const [players, setPlayers] = useState([]);
  const [schedule, setSchedule] = useState([]);

  useEffect(() => {
    fetch('/api/players')
      .then(res => res.json())
      .then(data => setPlayers(data));

    fetch('/api/schedule')
      .then(res => res.json())
      .then(data => setSchedule(data));
  }, []);

  const handleAddPlayer = async (player) => {
    const response = await fetch('/api/players', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(player),
    });
    if (response.ok) {
      const newPlayer = await response.json();
      setPlayers([...players, newPlayer]);
      setView('dashboard');
    }
  };

  return (
    <div>
      <header>
        <h1>Sports Team Manager</h1>
        <nav>
          <button onClick={() => setView('dashboard')}>Dashboard</button>
          <button onClick={() => setView('schedule')}>Schedule</button>
          <button onClick={() => setView('addPlayer')}>Add Player</button>
        </nav>
      </header>

      <main>
        {view === 'dashboard' && (
          <div>
            <h2>Player Roster</h2>
            <ul>
              {players.map(player => (
                <li key={player.id}>
                  {player.name} ({player.position}) - Games: {player.stats.games}, Goals: {player.stats.goals}
                </li>
              ))}
            </ul>
          </div>
        )}

        {view === 'schedule' && (
          <div>
            <h2>Schedule</h2>
            <ul>
              {schedule.map(event => (
                <li key={event.id}>
                  {event.date} - {event.type} vs {event.opponent}
                </li>
              ))}
            </ul>
          </div>
        )}

        {view === 'addPlayer' && (
          <div>
            <h2>Add Player</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const newPlayer = {
                  name: e.target.name.value,
                  position: e.target.position.value,
                };
                handleAddPlayer(newPlayer);
              }}
            >
              <input type="text" name="name" placeholder="Player Name" required />
              <input type="text" name="position" placeholder="Player Position" required />
              <button type="submit">Add Player</button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
