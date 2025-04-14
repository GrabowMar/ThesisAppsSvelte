import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [players, setPlayers] = useState([]);
  const [performances, setPerformances] = useState([]);
  const [trainingSchedules, setTrainingSchedules] = useState([]);
  const [matches, setMatches] = useState([]);
  const [injuries, setInjuries] = useState([]);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [newPlayerPosition, setNewPlayerPosition] = useState('');
  const [activeTab, setActiveTab] = useState('players');

  useEffect(() => {
    fetch('/api/players')
      .then(response => response.json())
      .then(data => setPlayers(data));

    fetch('/api/performances')
      .then(response => response.json())
      .then(data => setPerformances(data));

    fetch('/api/training-schedules')
      .then(response => response.json())
      .then(data => setTrainingSchedules(data));

    fetch('/api/matches')
      .then(response => response.json())
      .then(data => setMatches(data));

    fetch('/api/injuries')
      .then(response => response.json())
      .then(data => setInjuries(data));
  }, []);

  const handleCreatePlayer = () => {
    fetch('/api/players', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newPlayerName, position: newPlayerPosition }),
    })
      .then(response => response.json())
      .then(newPlayer => {
        setPlayers([...players, newPlayer]);
        setNewPlayerName('');
        setNewPlayerPosition('');
      });
  };

  return (
    <div className="app-container">
      <h1>Sports Team Management</h1>
      <div className="tab-navigation">
        <button onClick={() => setActiveTab('players')}>Players</button>
        <button onClick={() => setActiveTab('performances')}>Performances</button>
        <button onClick={() => setActiveTab('training-schedules')}>Training Schedules</button>
        <button onClick={() => setActiveTab('matches')}>Matches</button>
        <button onClick={() => setActiveTab('injuries')}>Injuries</button>
      </div>
      {activeTab === 'players' && (
        <div>
          <h2>Players</h2>
          <ul>
            {players.map(player => (
              <li key={player.id}>{player.name} - {player.position}</li>
            ))}
          </ul>
          <input type="text" value={newPlayerName} onChange={(e) => setNewPlayerName(e.target.value)} placeholder="Name" />
          <input type="text" value={newPlayerPosition} onChange={(e) => setNewPlayerPosition(e.target.value)} placeholder="Position" />
          <button onClick={handleCreatePlayer}>Add Player</button>
        </div>
      )}
      {activeTab === 'performances' && (
        <div>
          <h2>Performances</h2>
          <ul>
            {performances.map(performance => (
              <li key={performance.id}>Player ID: {performance.player_id}, Match ID: {performance.match_id}, Goals: {performance.goals}, Assists: {performance.assists}</li>
            ))}
          </ul>
        </div>
      )}
      {activeTab === 'training-schedules' && (
        <div>
          <h2>Training Schedules</h2>
          <ul>
            {trainingSchedules.map(schedule => (
              <li key={schedule.id}>Date: {schedule.date}, Activity: {schedule.activity}</li>
            ))}
          </ul>
        </div>
      )}
      {activeTab === 'matches' && (
        <div>
          <h2>Matches</h2>
          <ul>
            {matches.map(match => (
              <li key={match.id}>Date: {match.date}, Opponent: {match.opponent}</li>
            ))}
          </ul>
        </div>
      )}
      {activeTab === 'injuries' && (
        <div>
          <h2>Injuries</h2>
          <ul>
            {injuries.map(injury => (
              <li key={injury.id}>Player: {injury.player_name}, Injury: {injury.injury}, Recovery Date: {injury.recovery_date}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
