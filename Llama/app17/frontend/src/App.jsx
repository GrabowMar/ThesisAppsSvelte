// 1. Imports
import { useState, useEffect } from 'react';
import { createBrowserRouter, RouterProvider, Link } from 'react-router-dom';

// 2. State Management
const [exercises, setExercises] = useState([]);
const [progress, setProgress] = useState([]);
const [statistics, setStatistics] = useState({});

// 3. Lifecycle Functions
useEffect(() => {
  fetch('/api/exercises')
    .then(response => response.json())
    .then(data => setExercises(data));

  fetch('/api/progress')
    .then(response => response.json())
    .then(data => setProgress(data));

  fetch('/api/statistics')
    .then(response => response.json())
    .then(data => setStatistics(data));
}, []);

// 4. Event Handlers
const handleCreateExercise = (event) => {
  event.preventDefault();
  const exercise = {
    name: event.target.name.value,
    sets: event.target.sets.value,
    reps: event.target.reps.value,
    weight: event.target.weight.value,
  };

  fetch('/api/exercises', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(exercise),
  })
    .then(response => response.json())
    .then(data => setExercises([...exercises, data]));
};

const handleCreateProgress = (event) => {
  event.preventDefault();
  const progressData = {
    exercise_id: event.target.exercise_id.value,
    date: event.target.date.value,
    weight_lifted: event.target.weight_lifted.value,
  };

  fetch('/api/progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(progressData),
  })
    .then(response => response.json())
    .then(data => setProgress([...progress, data]));
};

// 5. API Calls
const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <div>
        <h1>Exercises</h1>
        <ul>
          {exercises.map(exercise => (
            <li key={exercise.id}>{exercise.name}</li>
          ))}
        </ul>
        <form onSubmit={handleCreateExercise}>
          <input type="text" name="name" placeholder="Name" />
          <input type="number" name="sets" placeholder="Sets" />
          <input type="number" name="reps" placeholder="Reps" />
          <input type="number" name="weight" placeholder="Weight" />
          <button type="submit">Create Exercise</button>
        </form>
      </div>
    ),
  },
  {
    path: '/progress',
    element: (
      <div>
        <h1>Progress</h1>
        <ul>
          {progress.map(p => (
            <li key={p.id}>{p.date} - {p.weight_lifted} kg</li>
          ))}
        </ul>
        <form onSubmit={handleCreateProgress}>
          <input type="number" name="exercise_id" placeholder="Exercise ID" />
          <input type="date" name="date" placeholder="Date" />
          <input type="number" name="weight_lifted" placeholder="Weight Lifted" />
          <button type="submit">Create Progress</button>
        </form>
      </div>
    ),
  },
  {
    path: '/statistics',
    element: (
      <div>
        <h1>Statistics</h1>
        <p>Total weight lifted: {statistics.total_weight_lifted} kg</p>
      </div>
    ),
  },
]);

// 6. Render
const App = () => {
  return (
    <RouterProvider router={router} />
  );
};

export default App;
