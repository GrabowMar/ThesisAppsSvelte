import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Set the base URL for axios
axios.defaults.baseURL = 'http://localhost:6013';

// Components
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/login', { username, password });
      localStorage.setItem('user', JSON.stringify(response.data));
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">Login</button>
      </form>
      {error && <p className="error">{error}</p>}
      <p>Don't have an account? <a href="/register">Register</a></p>
    </div>
  );
};

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    try {
      await axios.post('/register', { username, password });
      window.location.href = '/login';
    } catch (err) {
      setError(err.response.data.error);
    }
  };

  return (
    <div className="register-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <input type="password" placeholder="Confirm Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        <button type="submit">Register</button>
      </form>
      {error && <p className="error">{error}</p>}
      <p>Already have an account? <a href="/login">Login</a></p>
    </div>
  );
};

const Dashboard = () => {
  const [workouts, setWorkouts] = useState([]);
  const [progress, setProgress] = useState({});
  const [exercises, setExercises] = useState([]);
  const [newWorkout, setNewWorkout] = useState({ date: new Date().toISOString().split('T')[0], exercises: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchWorkouts();
    fetchProgress();
    fetchExercises();
  }, []);

  const fetchWorkouts = async () => {
    try {
      const response = await axios.get('/workouts');
      setWorkouts(response.data);
    } catch (err) {
      setError('Failed to fetch workouts');
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await axios.get('/progress');
      setProgress(response.data);
    } catch (err) {
      setError('Failed to fetch progress');
    }
  };

  const fetchExercises = async () => {
    try {
      const response = await axios.get('/exercises');
      setExercises(response.data);
    } catch (err) {
      setError('Failed to fetch exercises');
    }
  };

  const addExercise = () => {
    setNewWorkout({
      ...newWorkout,
      exercises: [...newWorkout.exercises, { name: '', sets: 0, reps: 0, weight: 0 }]
    });
  };

  const updateExercise = (index, field, value) => {
    const updatedExercises = [...newWorkout.exercises];
    updatedExercises[index][field] = value;
    setNewWorkout({ ...newWorkout, exercises: updatedExercises });
  };

  const submitWorkout = async () => {
    try {
      await axios.post('/workouts', newWorkout);
      fetchWorkouts();
      setNewWorkout({ date: new Date().toISOString().split('T')[0], exercises: [] });
    } catch (err) {
      setError('Failed to submit workout');
    }
  };

  return (
    <div className="dashboard-container">
      <h2>Dashboard</h2>
      {error && <p className="error">{error}</p>}
      <div className="workout-log">
        <h3>Log New Workout</h3>
        <input type="date" value={newWorkout.date} onChange={(e) => setNewWorkout({ ...newWorkout, date: e.target.value })} />
        {newWorkout.exercises.map((exercise, index) => (
          <div key={index} className="exercise-input">
            <select value={exercise.name} onChange={(e) => updateExercise(index, 'name', e.target.value)}>
              <option value="">Select Exercise</option>
              {exercises.map((ex) => (
                <option key={ex.name} value={ex.name}>{ex.name}</option>
              ))}
            </select>
            <input type="number" placeholder="Sets" value={exercise.sets} onChange={(e) => updateExercise(index, 'sets', parseInt(e.target.value))} />
            <input type="number" placeholder="Reps" value={exercise.reps} onChange={(e) => updateExercise(index, 'reps', parseInt(e.target.value))} />
            <input type="number" placeholder="Weight (kg)" value={exercise.weight} onChange={(e) => updateExercise(index, 'weight', parseFloat(e.target.value))} />
          </div>
        ))}
        <button onClick={addExercise}>Add Exercise</button>
        <button onClick={submitWorkout}>Submit Workout</button>
      </div>
      <div className="workout-history">
        <h3>Workout History</h3>
        {workouts.map((workout) => (
          <div key={workout.id} className="workout-item">
            <h4>{new Date(workout.date).toLocaleDateString()}</h4>
            <ul>
              {workout.exercises.map((exercise, index) => (
                <li key={index}>
                  {exercise.name}: {exercise.sets} sets x {exercise.reps} reps {exercise.weight ? `x ${exercise.weight} kg` : ''}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="progress-stats">
        <h3>Progress</h3>
        {Object.keys(progress).length === 0 ? (
          <p>No progress data available yet.</p>
        ) : (
          <ul>
            {Object.entries(progress).map(([exercise, stats]) => (
              <li key={exercise}>
                {exercise}: Volume increase: {stats.volume_increase.toFixed(2)} kg, Percentage increase: {stats.percentage_increase.toFixed(2)}%
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    window.location.href = '/login';
  };

  return (
    <Router>
      <div className="app-container">
        <nav className="navbar">
          <h1>Fitness Logger</h1>
          {isAuthenticated && <button onClick={handleLogout}>Logout</button>}
        </nav>
        <Routes>
          <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
          <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
          <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
