import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [workouts, setWorkouts] = useState([]);
  const [statistics, setStatistics] = useState([]);
  const [exercise, setExercise] = useState('');
  const [sets, setSets] = useState(0);
  const [reps, setReps] = useState(0);
  const [weight, setWeight] = useState(0);
  const [date, setDate] = useState('');

  useEffect(() => {
    fetchWorkouts();
    fetchStatistics();
  }, []);

  const fetchWorkouts = async () => {
    const response = await fetch('http://localhost:5193/api/workouts');
    const data = await response.json();
    setWorkouts(data);
  };

  const fetchStatistics = async () => {
    const response = await fetch('http://localhost:5193/api/statistics');
    const data = await response.json();
    setStatistics(data);
  };

  const addWorkout = async () => {
    const response = await fetch('http://localhost:5193/api/workouts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ exercise, sets, reps, weight, date }),
    });
    if (response.ok) {
      fetchWorkouts();
      fetchStatistics();
    }
  };

  return (
    <div className="App">
      <h1>Fitness Logger</h1>
      <div className="workout-form">
        <input type="text" placeholder="Exercise" value={exercise} onChange={(e) => setExercise(e.target.value)} />
        <input type="number" placeholder="Sets" value={sets} onChange={(e) => setSets(e.target.value)} />
        <input type="number" placeholder="Reps" value={reps} onChange={(e) => setReps(e.target.value)} />
        <input type="number" placeholder="Weight" value={weight} onChange={(e) => setWeight(e.target.value)} />
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <button onClick={addWorkout}>Add Workout</button>
      </div>
      <div className="workouts-list">
        <h2>Workouts</h2>
        {workouts.map((workout) => (
          <div key={workout[0]} className="workout-item">
            <p>{workout[1]} - {workout[2]} sets of {workout[3]} reps at {workout[4]} kg on {workout[5]}</p>
          </div>
        ))}
      </div>
      <div className="statistics">
        <h2>Statistics</h2>
        {statistics.map((stat) => (
          <div key={stat[0]} className="statistic-item">
            <p>{stat[0]} - Total Volume: {stat[1]} kg</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
