import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const ExerciseList = () => {
  const [exercises, setExercises] = useState([]);

  useEffect(() => {
    axios.get('/api/exercises').then(response => setExercises(response.data));
  }, []);

  return (
    <div>
      <h2>Exercises</h2>
      <ul>
        {exercises.map(exercise => (
          <li key={exercise.id}>{exercise.name}</li>
        ))}
      </ul>
    </div>
  );
};

const LogWorkout = () => {
  const [exerciseId, setExerciseId] = useState('');
  const [duration, setDuration] = useState('');
  const [date, setDate] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/logs', { exercise_id: exerciseId, duration, date }).then(() => {
      alert('Log added successfully');
    });
  };

  return (
    <div>
      <h2>Log Workout</h2>
      <form onSubmit={handleSubmit}>
        <input type="number" placeholder="Exercise ID" value={exerciseId} onChange={e => setExerciseId(e.target.value)} required />
        <input type="number" placeholder="Duration (minutes)" value={duration} onChange={e => setDuration(e.target.value)} required />
        <input type="date" value={date} onChange={e => setDate(e.target.value)} required />
        <button type="submit">Log Workout</button>
      </form>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <nav>
        <Link to="/">Exercises</Link>
        <Link to="/log">Log Workout</Link>
      </nav>
      <Switch>
        <Route path="/log" component={LogWorkout} />
        <Route path="/" component={ExerciseList} />
      </Switch>
    </Router>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
