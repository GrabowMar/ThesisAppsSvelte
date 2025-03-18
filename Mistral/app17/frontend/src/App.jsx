import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loggedIn, setLoggedIn] = useState(false);
    const [exercises, setExercises] = useState([]);
    const [workouts, setWorkouts] = useState([]);
    const [statistics, setStatistics] = useState({});

    useEffect(() => {
        if (loggedIn) {
            axios.get('http://localhost:5113/exercises')
                .then(response => setExercises(response.data))
                .catch(error => console.error('Error fetching exercises:', error));

            axios.get(`http://localhost:5113/workouts/${username}`)
                .then(response => setWorkouts(response.data))
                .catch(error => console.error('Error fetching workouts:', error));

            axios.get(`http://localhost:5113/statistics/${username}`)
                .then(response => setStatistics(response.data))
                .catch(error => console.error('Error fetching statistics:', error));
        }
    }, [loggedIn, username]);

    const handleLogin = () => {
        axios.post('http://localhost:5113/login', { username, password })
            .then(response => {
                setLoggedIn(true);
            })
            .catch(error => console.error('Error logging in:', error));
    };

    const handleRegister = () => {
        axios.post('http://localhost:5113/register', { username, password })
            .then(response => {
                alert('Registration successful! Please login.');
            })
            .catch(error => console.error('Error registering:', error));
    };

    const handleLogout = () => {
        setLoggedIn(false);
        setUsername('');
        setPassword('');
    };

    const handleLogWorkout = (exerciseId, details) => {
        axios.post('http://localhost:5113/workouts', { username, exercise_id: exerciseId, details })
            .then(response => {
                setWorkouts([...workouts, response.data]);
            })
            .catch(error => console.error('Error logging workout:', error));
    };

    return (
        <Router>
            <div className="app">
                <nav>
                    <Link to="/">Home</Link>
                    {loggedIn && (
                        <>
                            <Link to="/exercises">Exercises</Link>
                            <Link to="/workouts">Workouts</Link>
                            <Link to="/statistics">Statistics</Link>
                            <button onClick={handleLogout}>Logout</button>
                        </>
                    )}
                </nav>
                <Routes>
                    <Route path="/" element={
                        loggedIn ? (
                            <div>Welcome, {username}!</div>
                        ) : (
                            <div>
                                <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                                <button onClick={handleLogin}>Login</button>
                                <button onClick={handleRegister}>Register</button>
                            </div>
                        )
                    } />
                    <Route path="/exercises" element={
                        <div>
                            <h2>Exercise Library</h2>
                            <ul>
                                {exercises.map(exercise => (
                                    <li key={exercise.id}>{exercise.name} - {exercise.description}</li>
                                ))}
                            </ul>
                        </div>
                    } />
                    <Route path="/workouts" element={
                        <div>
                            <h2>Log Workout</h2>
                            <input type="number" placeholder="Exercise ID" />
                            <input type="text" placeholder="Details" />
                            <button onClick={() => handleLogWorkout(1, 'Details')}>Log Workout</button>
                            <h2>Workout History</h2>
                            <ul>
                                {workouts.map(workout => (
                                    <li key={workout.id}>{workout.date} - Exercise ID: {workout.exercise_id}, Details: {workout.details}</li>
                                ))}
                            </ul>
                        </div>
                    } />
                    <Route path="/statistics" element={
                        <div>
                            <h2>Statistics</h2>
                            <p>Total Workouts: {statistics.total_workouts}</p>
                            <p>Exercise Counts: {JSON.stringify(statistics.exercise_counts)}</p>
                        </div>
                    } />
                </Routes>
            </div>
        </Router>
    );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
