import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

// API Configuration
const API_BASE_URL = 'http://localhost:5353/api';

// Utility Functions
const formatDate = (dateString) => {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const fetchAPI = async (endpoint, options = {}) => {
  const defaultOptions = {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, defaultOptions);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Something went wrong');
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Component: Login Form
const LoginForm = ({ onLogin, switchToRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const data = await fetchAPI('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      
      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form">
      <h2>Login to Your Account</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn primary" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p className="auth-switch">
        Don't have an account? <button onClick={switchToRegister}>Register</button>
      </p>
    </div>
  );
};

// Component: Register Form
const RegisterForm = ({ onRegisterSuccess, switchToLogin }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);

    try {
      await fetchAPI('/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      });
      
      onRegisterSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form">
      <h2>Create an Account</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength="6"
          />
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength="6"
          />
        </div>
        <button type="submit" className="btn primary" disabled={isLoading}>
          {isLoading ? 'Creating Account...' : 'Register'}
        </button>
      </form>
      <p className="auth-switch">
        Already have an account? <button onClick={switchToLogin}>Login</button>
      </p>
    </div>
  );
};

// Component: Navigation
const Navigation = ({ user, onLogout, setActivePage }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await fetchAPI('/logout', { method: 'POST' });
      onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <nav className="main-nav">
      <div className="nav-brand">
        <h1>FitnessTracker</h1>
        <button className="mobile-menu-btn" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          ☰
        </button>
      </div>
      
      <ul className={`nav-links ${isMenuOpen ? 'open' : ''}`}>
        <li>
          <button onClick={() => setActivePage('dashboard')}>Dashboard</button>
        </li>
        <li>
          <button onClick={() => setActivePage('workouts')}>Workouts</button>
        </li>
        <li>
          <button onClick={() => setActivePage('exercises')}>Exercises</button>
        </li>
        <li>
          <button onClick={() => setActivePage('progress')}>Progress</button>
        </li>
        <li>
          <button onClick={() => setActivePage('body-stats')}>Body Stats</button>
        </li>
      </ul>
      
      <div className="user-menu">
        <span>Hi, {user.username}</span>
                <button onClick={handleLogout} className="btn logout">
          Logout
        </button>
      </div>
    </nav>
  );
};

// Component: Dashboard
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const data = await fetchAPI('/dashboard');
        setDashboardData(data);
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      
      <div className="stats-overview">
        <div className="stat-card">
          <h3>Total Workouts</h3>
          <p className="stat-value">{dashboardData.stats.total_workouts}</p>
        </div>
        
        <div className="stat-card">
          <h3>Total Exercises</h3>
          <p className="stat-value">{dashboardData.stats.total_exercises}</p>
        </div>
        
        <div className="stat-card">
          <h3>Current Weight</h3>
          <p className="stat-value">{dashboardData.stats.current_weight ? `${dashboardData.stats.current_weight} kg` : 'Not recorded'}</p>
        </div>
        
        <div className="stat-card">
          <h3>Body Fat</h3>
          <p className="stat-value">{dashboardData.stats.current_body_fat ? `${dashboardData.stats.current_body_fat}%` : 'Not recorded'}</p>
        </div>
        
        <div className="stat-card">
          <h3>Favorite Exercise</h3>
          <p className="stat-value">{dashboardData.stats.favorite_exercise || 'None'}</p>
        </div>
      </div>
      
      <div className="recent-workouts">
        <h3>Recent Workouts</h3>
        
        {dashboardData.recent_workouts.length === 0 ? (
          <p>No workouts recorded yet. Start logging your first workout!</p>
        ) : (
          <ul className="workout-list">
            {dashboardData.recent_workouts.map(workout => (
              <li key={workout.id} className="workout-item">
                <div className="workout-header">
                  <h4>{workout.name}</h4>
                  <span className="workout-date">{formatDate(workout.date)}</span>
                </div>
                <p>{workout.duration ? `${workout.duration} minutes` : 'Duration not specified'}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

// Component: Exercises List
const ExerciseList = () => {
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    const fetchExercises = async () => {
      try {
        const data = await fetchAPI('/exercises');
        setExercises(data);
      } catch (err) {
        setError('Failed to load exercises');
      } finally {
        setLoading(false);
      }
    };

    fetchExercises();
  }, []);

  const categories = ['', ...new Set(exercises.map(ex => ex.category))];
  
  const filteredExercises = exercises.filter(exercise => {
    const matchesSearch = exercise.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || exercise.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return <div className="loading">Loading exercises...</div>;
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  return (
    <div className="exercises-container">
      <h2>Exercise Library</h2>
      
      <div className="filters">
        <div className="search-wrapper">
          <input
            type="text"
            placeholder="Search exercises..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="filter-wrapper">
          <select 
            value={selectedCategory} 
            onChange={e => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.filter(c => c).map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="exercise-grid">
        {filteredExercises.length === 0 ? (
          <p>No exercises match your search.</p>
        ) : (
          filteredExercises.map(exercise => (
            <div key={exercise.id} className="exercise-card">
              <h3>{exercise.name}</h3>
              <div className="exercise-details">
                <span className="exercise-category">{exercise.category}</span>
                <span className="exercise-muscle">{exercise.muscle_group}</span>
              </div>
              <p className="exercise-description">{exercise.description}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Component: Workouts Page
const WorkoutsPage = ({ setActivePage, setEditWorkoutId }) => {
  const [workouts, setWorkouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    const fetchWorkouts = async () => {
      try {
        const data = await fetchAPI('/workouts');
        setWorkouts(data);
      } catch (err) {
        setError('Failed to load workouts');
      } finally {
        setLoading(false);
      }
    };

    fetchWorkouts();
  }, []);

  const handleDeleteWorkout = async (id) => {
    if (!window.confirm('Are you sure you want to delete this workout?')) return;
    
    try {
      await fetchAPI(`/workouts/${id}`, { method: 'DELETE' });
      setWorkouts(workouts.filter(w => w.id !== id));
    } catch (error) {
      console.error('Failed to delete workout:', error);
      setError('Failed to delete workout');
    }
  };

  const handleViewWorkout = (id) => {
    setEditWorkoutId(id);
    setActivePage('workout-details');
  };

  if (loading) {
    return <div className="loading">Loading workouts...</div>;
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  return (
    <div className="workouts-container">
      <div className="page-header">
        <h2>My Workouts</h2>
        <button 
          className="btn primary" 
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancel' : 'Add New Workout'}
        </button>
      </div>
      
      {showCreateForm && <WorkoutForm 
        onSuccess={(newWorkout) => {
          setWorkouts([newWorkout, ...workouts]);
          setShowCreateForm(false);
        }} 
      />}
      
      {workouts.length === 0 ? (
        <p>No workouts recorded yet. Start by adding your first workout!</p>
      ) : (
        <div className="workouts-list">
          {workouts.map(workout => (
            <div key={workout.id} className="workout-card">
              <div className="workout-header">
                <h3>{workout.name}</h3>
                <span className="workout-date">{formatDate(workout.date)}</span>
              </div>
              
              <div className="workout-details">
                <p>
                  <strong>Duration:</strong> {workout.duration ? `${workout.duration} minutes` : 'Not specified'}
                </p>
                <p>
                  <strong>Exercises:</strong> {workout.entry_count}
                </p>
              </div>
              
              <div className="workout-actions">
                <button 
                  className="btn secondary" 
                  onClick={() => handleViewWorkout(workout.id)}
                >
                  View Details
                </button>
                <button 
                  className="btn danger"
                  onClick={() => handleDeleteWorkout(workout.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Component: Workout Form
const WorkoutForm = ({ onSuccess }) => {
  const [name, setName] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [duration, setDuration] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const data = await fetchAPI('/workouts', {
        method: 'POST',
        body: JSON.stringify({
          name,
          date,
          duration: duration ? parseInt(duration) : null,
          notes: notes || null
        }),
      });
      
      onSuccess(data.workout);
    } catch (err) {
      setError('Failed to create workout');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h3>Create New Workout</h3>
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Workout Name</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="date">Date</label>
          <input
            type="date"
            id="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="duration">Duration (minutes)</label>
          <input
            type="number"
            id="duration"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            min="1"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          ></textarea>
        </div>
        
        <button type="submit" className="btn primary" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create Workout'}
        </button>
      </form>
    </div>
  );
};

// Component: Workout Details
const WorkoutDetails = ({ workoutId, setActivePage }) => {
  const [workout, setWorkout] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [workoutData, exercisesData] = await Promise.all([
          fetchAPI(`/workouts/${workoutId}`),
          fetchAPI('/exercises')
        ]);
        
        setWorkout(workoutData);
        setExercises(exercisesData);
      } catch (err) {
        setError('Failed to load workout details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [workoutId]);

  const handleDeleteEntry = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this exercise entry?')) return;
    
    try {
      await fetchAPI(`/workouts/${workoutId}/entries/${entryId}`, { method: 'DELETE' });
      
      // Update the local state
      setWorkout({
        ...workout,
        entries: workout.entries.filter(entry => entry.id !== entryId)
      });
    } catch (error) {
      console.error('Failed to delete entry:', error);
      setError('Failed to delete entry');
    }
  };

  if (loading) {
    return <div className="loading">Loading workout details...</div>;
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  return (
    <div className="workout-details-container">
      <div className="page-header">
        <button className="btn back" onClick={() => setActivePage('workouts')}>
          ← Back to Workouts
        </button>
      </div>
      
      <div className="workout-header">
        <h2>{workout.name}</h2>
        <p className="workout-date">{formatDate(workout.date)}</p>
      </div>
      
      {workout.notes && (
        <div className="workout-notes">
          <h4>Notes</h4>
          <p>{workout.notes}</p>
        </div>
      )}
      
      <div className="entries-section">
        <div className="section-header">
          <h3>Exercises</h3>
          <button
            className="btn primary"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? 'Cancel' : 'Add Exercise'}
          </button>
        </div>
        
        {showAddForm && (
          <WorkoutEntryForm
            workoutId={workoutId}
            exercises={exercises}
            onSuccess={(newEntry) => {
              setWorkout({
                ...workout,
                entries: [...workout.entries, newEntry]
              });
              setShowAddForm(false);
            }}
          />
        )}
        
        {workout.entries.length === 0 ? (
          <p>No exercises added to this workout yet.</p>
        ) : (
          <div className="entries-list">
            {workout.entries.map(entry => (
              <div key={entry.id} className="entry-card">
                <h4>{entry.exercise_name}</h4>
                <div className="entry-details">
                  <div className="entry-stat">
                    <span className="stat-label">Sets</span>
                    <span className="stat-value">{entry.sets}</span>
                  </div>
                  
                  <div className="entry-stat">
                    <span className="stat-label">Reps</span>
                    <span className="stat-value">{entry.reps}</span>
                  </div>
                  
                  <div className="entry-stat">
                    <span className="stat-label">Weight</span>
                    <span className="stat-value">{entry.weight ? `${entry.weight} kg` : '-'}</span>
                  </div>
                </div>
                
                {entry.notes && <p className="entry-notes">{entry.notes}</p>}
                
                <button 
                  className="btn danger small" 
                  onClick={() => handleDeleteEntry(entry.id)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Component: Workout Entry Form
const WorkoutEntryForm = ({ workoutId, exercises, onSuccess }) => {
  const [exerciseId, setExerciseId] = useState('');
  const [sets, setSets] = useState('');
  const [reps, setReps] = useState('');
  const [weight, setWeight] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const data = await fetchAPI(`/workouts/${workoutId}/entries`, {
        method: 'POST',
        body: JSON.stringify({
          exercise_id: exerciseId,
          sets: parseInt(sets),
          reps: parseInt(reps),
          weight: weight ? parseFloat(weight) : null,
          notes: notes || null
        }),
      });
      
      onSuccess(data);
    } catch (err) {
      setError('Failed to add exercise');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h3>Add Exercise</h3>
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="exercise">Exercise</label>
          <select
            id="exercise"
            value={exerciseId}
            onChange={(e) => setExerciseId(e.target.value)}
            required
          >
            <option value="">Select an exercise</option>
            {exercises.map(exercise => (
              <option key={exercise.id} value={exercise.id}>
                {exercise.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="sets">Sets</label>
          <input
            type="number"
            id="sets"
            value={sets}
            onChange={(e) => setSets(e.target.value)}
            min="1"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="reps">Reps</label>
          <input
            type="number"
            id="reps"
            value={reps}
            onChange={(e) => setReps(e.target.value)}
            min="1"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="weight">Weight (kg)</label>
          <input
            type="number"
            id="weight"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            min="0"
            step="0.5"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          ></textarea>
        </div>
        
        <button type="submit" className="btn primary" disabled={isLoading}>
          {isLoading ? 'Adding...' : 'Add Exercise'}
        </button>
      </form>
    </div>
  );
};

// Component: Body Stats Page
const BodyStatsPage = () => {
  const [bodyStats, setBodyStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    const fetchBodyStats = async () => {
      try {
        const data = await fetchAPI('/body-stats');
        setBodyStats(data);
      } catch (err) {
        setError('Failed to load body stats');
      } finally {
        setLoading(false);
      }
    };

    fetchBodyStats();
  }, []);

  const handleAddSuccess = (newStat) => {
    // Check if we're updating an existing stat for the same date
    const existingIndex = bodyStats.findIndex(stat => stat.date === newStat.date);
    
    if (existingIndex >= 0) {
      // Update existing stat
      const updatedStats = [...bodyStats];
      updatedStats[existingIndex] = newStat;
      setBodyStats(updatedStats);
    } else {
      // Add new stat
      setBodyStats([newStat, ...bodyStats]);
    }
    
    setShowAddForm(false);
  };

  if (loading) {
    return <div className="loading">Loading body stats...</div>;
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  // Prepare data for the chart
  const chartData = [...bodyStats]
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .map(stat => ({
      date: formatDate(stat.date),
      weight: stat.weight,
      bodyFat: stat.body_fat
    }));

  return (
    <div className="body-stats-container">
      <div className="page-header">
        <h2>Body Stats</h2>
        <button 
          className="btn primary" 
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? 'Cancel' : 'Add New Measurement'}
        </button>
      </div>
      
      {showAddForm && <BodyStatForm onSuccess={handleAddSuccess} />}
      
      {bodyStats.length > 0 && (
        <div className="stats-chart">
          <h3>Weight Progress</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="weight" stroke="#8884d8" name="Weight (kg)" />
              {chartData.some(d => d.bodyFat) && (
                <Line type="monotone" dataKey="bodyFat" stroke="#82ca9d" name="Body Fat %" />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      
      {bodyStats.length === 0 ? (
        <p>No body measurements recorded yet. Start by adding your first measurement!</p>
      ) : (
        <div className="stats-table">
          <h3>Measurement History</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Weight (kg)</th>
                <th>Body Fat (%)</th>
                <th>Muscle Mass (kg)</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {bodyStats.map(stat => (
                <tr key={stat.id}>
                  <td>{formatDate(stat.date)}</td>
                  <td>{stat.weight || '-'}</td>
                  <td>{stat.body_fat || '-'}</td>
                  <td>{stat.muscle_mass || '-'}</td>
                  <td>{stat.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// Component: Body Stat Form
const BodyStatForm = ({ onSuccess }) => {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [weight, setWeight] = useState('');
  const [bodyFat, setBodyFat] = useState('');
  const [muscleMass, setMuscleMass] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!weight && !bodyFat && !muscleMass) {
      setError('At least one measurement must be provided');
      return;
    }
    
    setError('');
    setIsLoading(true);
    
    try {
      const data = await fetchAPI('/body-stats', {
        method: 'POST',
        body: JSON.stringify({
          date,
          weight: weight ? parseFloat(weight) : null,
          body_fat: bodyFat ? parseFloat(bodyFat) : null,
          muscle_mass: muscleMass ? parseFloat(muscleMass) : null,
          notes
        }),
      });
      
      onSuccess(data);
    } catch (err) {
      setError('Failed to save measurement');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h3>Add Body Measurement</h3>
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="date">Date</label>
          <input
            type="date"
            id="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="weight">Weight (kg)</label>
          <input
            type="number"
            id="weight"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            min="20"
            max="300"
            step="0.1"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="bodyFat">Body Fat (%)</label>
          <input
            type="number"
            id="bodyFat"
            value={bodyFat}
            onChange={(e) => setBodyFat(e.target.value)}
            min="1"
            max="60"
            step="0.1"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="muscleMass">Muscle Mass (kg)</label>
          <input
            type="number"
            id="muscleMass"
            value={muscleMass}
            onChange={(e) => setMuscleMass(e.target.value)}
            min="10"
            max="100"
            step="0.1"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          ></textarea>
        </div>
        
        <button type="submit" className="btn primary" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Measurement'}
        </button>
      </form>
    </div>
  );
};

// Component: Progress Page
const ProgressPage = () => {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const data = await fetchAPI('/progress');
        setProgressData(data);
      } catch (err) {
        setError('Failed to load progress data');
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, []);

  if (loading) {
    return <div className="loading">Loading progress data...</div>;
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  // Format data for charts
  const formatChartData = (data) => {
    if (!data || data.length === 0) return [];
    return data.map(item => ({
      date: item.date,
      weight: item.weight
    }));
  };

  const weightData = progressData.weight_data;
  const benchData = formatChartData(progressData.bench_press);
  const squatData = formatChartData(progressData.squat);
  const deadliftData = formatChartData(progressData.deadlift);

  return (
    <div className="progress-container">
      <h2>Progress Tracking</h2>
      
      {weightData && weightData.length > 0 ? (
        <div className="progress-chart">
          <h3>Body Weight Progress</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={weightData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="weight" stroke="#8884d8" name="Weight (kg)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="no-data-message">
          <p>No weight data recorded yet. Add body measurements to track your weight progress.</p>
        </div>
      )}
      
      <div className="strength-progress">
        <h3>Strength Progress</h3>
        
        {benchData.length === 0 && squatData.length === 0 && deadliftData.length === 0 ? (
          <p>No strength data recorded yet. Log your workouts to track your progress.</p>
        ) : (
          <div className="strength-charts">
            {benchData.length > 0 && (
              <div className="chart-container">
                <h4>Bench Press</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={benchData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="weight" stroke="#8884d8" name="Weight (kg)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            
            {squatData.length > 0 && (
              <div className="chart-container">
                <h4>Squat</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={squatData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="weight" stroke="#82ca9d" name="Weight (kg)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            
            {deadliftData.length > 0 && (
              <div className="chart-container">
                                <h4>Deadlift</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={deadliftData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="weight" stroke="#ff7300" name="Weight (kg)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authView, setAuthView] = useState('login');
  const [activePage, setActivePage] = useState('dashboard');
  const [editWorkoutId, setEditWorkoutId] = useState(null);
  
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await fetchAPI('/user');
        setUser(userData);
      } catch (error) {
        // Not authenticated, that's ok
        console.log('User not authenticated');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);
  
  const handleLogin = (userData) => {
    setUser(userData);
    setActivePage('dashboard');
  };
  
  const handleLogout = () => {
    setUser(null);
    setAuthView('login');
  };
  
  const handleRegisterSuccess = () => {
    setAuthView('login');
  };
  
  if (loading) {
    return (
      <div className="app-loading">
        <h2>Loading FitnessTracker...</h2>
      </div>
    );
  }
  
  // User not logged in
  if (!user) {
    return (
      <div className="auth-container">
        <div className="auth-header">
          <h1>FitnessTracker</h1>
          <p className="tagline">Track your fitness journey, celebrate your progress</p>
        </div>
        
        {authView === 'login' ? (
          <LoginForm 
            onLogin={handleLogin} 
            switchToRegister={() => setAuthView('register')} 
          />
        ) : (
          <RegisterForm 
            onRegisterSuccess={handleRegisterSuccess} 
            switchToLogin={() => setAuthView('login')} 
          />
        )}
      </div>
    );
  }
  
  // Render main application
  return (
    <div className="app-container">
      <Navigation 
        user={user} 
        onLogout={handleLogout}
        setActivePage={setActivePage}
      />
      
      <main className="content">
        {activePage === 'dashboard' && <Dashboard />}
        {activePage === 'exercises' && <ExerciseList />}
        {activePage === 'workouts' && (
          <WorkoutsPage 
            setActivePage={setActivePage} 
            setEditWorkoutId={setEditWorkoutId}
          />
        )}
        {activePage === 'workout-details' && (
          <WorkoutDetails 
            workoutId={editWorkoutId} 
            setActivePage={setActivePage}
          />
        )}
        {activePage === 'body-stats' && <BodyStatsPage />}
        {activePage === 'progress' && <ProgressPage />}
      </main>
      
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} FitnessTracker. Track your fitness journey.</p>
      </footer>
    </div>
  );
};

// Mounting logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);

export default App;



