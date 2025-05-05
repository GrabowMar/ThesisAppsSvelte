import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import './App.css';
const App = () => {
  const [players, setPlayers] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [matches, setMatches] = useState([]);
  const [newPlayer, setNewPlayer] = useState({ name: '', position: '', performance: '', health_status: '' });
  const [newTraining, setNewTraining] = useState({ schedule: '' });
  const [newMatch, setNewMatch] = useState({ date: '', opponent: '', result: '' });
useEffect(() => {
  axios.get('/api/players')
    .then(response => setPlayers(response.data))
    .catch(error => console.error('Error fetching players:', error));

  axios.get('/api/trainings')
    .then(response => setTrainings(response.data))
    .catch(error => console.error('Error fetching trainings:', error));

  axios.get('/api/matches')
    .then(response => setMatches(response.data))
    .catch(error => console.error('Error fetching matches:', error));
}, []);
const addPlayer = () => {
  axios.post('/api/players', newPlayer)
    .then(response => {
      setPlayers([...players, response.data.player]);
      setNewPlayer({ name: '', position: '', performance: '', health_status: '' });
    })
    .catch(error => console.error('Error adding player:', error));
};

const addTraining = () => {
  axios.post('/api/trainings', newTraining)
    .then(response => {
      setTrainings([...trainings, response.data.training]);
      setNewTraining({ schedule: '' });
    })
    .catch(error => console.error('Error adding training:', error));
};

const addMatch = () => {
  axios.post('/api/matches', newMatch)
    .then(response => {
      setMatches([...matches, response.data.match]);
      setNewMatch({ date: '', opponent: '', result: '' });
    })
    .catch(error => console.error('Error adding match:', error));
};
// API calls are managed using axios within useEffect and event handlers
const App = () => {
  // State and functions defined above

  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/players">Players</Link>
        <Link to="/trainings">Trainings</Link>
        <Link to="/matches">Matches</Link>
      </nav>
      <Switch>
        <Route path="/players">
          <PlayersList players={players} />
          <AddPlayerForm newPlayer={newPlayer} setNewPlayer={setNewPlayer} addPlayer={addPlayer} />
        </Route>
        <Route path="/trainings">
          <TrainingsList trainings={trainings} />
          <AddTrainingForm newTraining={newTraining} setNewTraining={setNewTraining} addTraining={addTraining} />
        </Route>
        <Route path="/matches">
          <MatchesList matches={matches} />
          <AddMatchForm newMatch={newMatch} setNewMatch={setNewMatch} addMatch={addMatch} />
        </Route>
        <Route path="/">
          <Home />
        </Route>
      </Switch>
    </Router>
  );
};

const PlayersList = ({ players }) => (
  <div>
    <h2>Players</h2>
    <ul>
      {players.map(player => (
        <li key={player.id}>{player.name} - {player.position}</li>
      ))}
    </ul>
  </div>
);

const AddPlayerForm = ({ newPlayer, setNewPlayer, addPlayer }) => (
  <div>
    <h2>Add Player</h2>
    <input
      type="text"
      placeholder="Name"
      value={newPlayer.name}
      onChange={e => setNewPlayer({ ...newPlayer, name: e.target.value })}
    />
    <input
      type="text"
      placeholder="Position"
      value={newPlayer.position}
      onChange={e => setNewPlayer({ ...newPlayer, position: e.target.value })}
    />
    <input
      type="text"
      placeholder="Performance"
      value={newPlayer.performance}
      onChange={e => setNewPlayer({ ...newPlayer, performance: e.target.value })}
    />
    <input
      type="text"
      placeholder="Health Status"
      value={newPlayer.health_status}
      onChange={e => setNewPlayer({ ...newPlayer, health_status: e.target.value })}
    />
    <button onClick={addPlayer}>Add Player</button>
  </div>
);

const TrainingsList = ({ trainings }) => (
  <div>
    <h2>Trainings</h2>
    <ul>
      {trainings.map(training => (
        <li key={training.id}>{training.schedule}</li>
      ))}
    </ul>
  </div>
);

const AddTrainingForm = ({ newTraining, setNewTraining, addTraining }) => (
  <div>
    <h2>Add Training</h2>
    <input
      type="text"
      placeholder="Schedule"
      value={newTraining.schedule}
      onChange={e => setNewTraining({ ...newTraining, schedule: e.target.value })}
    />
    <button onClick={addTraining}>Add Training</button>
  </div>
);

const MatchesList = ({ matches }) => (
  <div>
    <h2>Matches</h2>
    <ul>
      {matches.map(match => (
      <li key={match.id}>{match.date} - {match.opponent} ({match.result})</li>
      ))}
    </ul>
  </div>
);

const AddMatchForm = ({ newMatch, setNewMatch, addMatch }) => (
  <div>
    <h2>Add Match</h2>
    <input
      type="text"
      placeholder="Date"
      value={newMatch.date}
      onChange={e => setNewMatch({ ...newMatch, date: e.target.value })}
    />
    <input
      type="text"
      placeholder="Opponent"
      value={newMatch.opponent}
      onChange={e => setNewMatch({ ...newMatch, opponent: e.target.value })}
    />
    <input
      type="text"
      placeholder="Result"
      value={newMatch.result}
      onChange={e => setNewMatch({ ...newMatch, result: e.target.value })}
    />
    <button onClick={addMatch}>Add Match</button>
  </div>
);

const Home = () => (
  <div>
    <h1>Welcome to the Sports Team Management System</h1>
    <p>Manage your team's roster, training schedules, match planning, and more!</p>
  </div>
);

// Mounting the App component
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);

