import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [workouts, setWorkouts] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [currentView, setCurrentView] = useState('dashboard');

  useEffect(() => {
    fetch('/api/workouts')
      .then((res) => res.json())
      .then((data) => setWorkouts(data))
      .catch((err) => console.error(err));

    fetch('/api/statistics')
      .then((res) => res.json())
      .then((data) => setStatistics(data))
      .catch((err) => console.error(err));

    fetch('/api/exercises')
      .then((res) => res.json())
      .then((data) => setExercises(data))
      .catch((err) => console.error(err));
  }, []);

  const addWorkout = (workout) => {
    fetch('/api/workouts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workout),
    })
      .then((res) => res.json())
      .then((data) => {
        setWorkouts([...workouts, data.workout]);
        fetch('/api/statistics')
          .then((res) => res.json())
          .then((data) => setStatistics(data))
          .catch((err) => console.error(err));
      })
      .catch((err) => console.error(err));
  };

  const renderDashboard = () => (
    <div>
      <h1>Dashboard</h1>
      {statistics && (
        <div>
          <p>Total Workouts: {statistics.total_workouts}</p>
          <p>Total Duration: {statistics.total_duration} minutes</p>
          <p>Total Calories Burned: {statistics.total_calories}</p>
        </div>
      )}
    </div>
  );

  const renderWorkouts = () => (
    <div>
      <h1>Workouts</h1>
      <ul>
        {workouts.map((workout) => (
          <li key={workout.id}>
            {workout.date} - {workout.exercise} - {workout.duration} minutes - {workout.calories_burned} calories
          </li>
        ))}
      </ul>
      <button onClick={() => setCurrentView('addWorkout')}>Add Workout</button>
    </div>
  );

  const renderAddWorkout = () => (
    <div>
      <h1>Add Workout</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const workout = {
            exercise: e.target.exercise.value,
            duration: parseInt(e.target.duration.value),
            calories_burned: parseInt(e.target.calories.value),
          };
          addWorkout(workout);
          setCurrentView('workouts');
        }}
      >
        <label>
          Exercise:
          <select name="exercise">
            {exercises.map((exercise) => (
              <option key={exercise.id} value={exercise.name}>
                {exercise.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Duration (minutes):
          <input type="number" name="duration" required />
        </label>
        <label>
          Calories Burned:
          <input type="number" name="calories" required />
        </label>
        <button type="submit">Add</button>
      </form>
    </div>
  );

  const renderExercises = () => (
    <div>
      <h1>Exercises</h1>
      <ul>
        {exercises.map((exercise) => (
          <li key={exercise.id}>
            {exercise.name} ({exercise.muscle_group})
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <main>
      <nav>
        <button onClick={() => setCurrentView('dashboard')}>Dashboard</button>
        <button onClick={() => setCurrentView('workouts')}>Workouts</button>
        <button onClick={() => setCurrentView('exercises')}>Exercises</button>
      </nav>
      {currentView === 'dashboard' && renderDashboard()}
      {currentView === 'workouts' && renderWorkouts()}
      {currentView === 'addWorkout' && renderAddWorkout()}
      {currentView === 'exercises' && renderExercises()}
    </main>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
