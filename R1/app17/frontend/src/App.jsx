import { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';
import axios from 'axios';

axios.defaults.baseURL = 'http://localhost:5593/api';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [workouts, setWorkouts] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [stats, setStats] = useState({});
  const [formData, setFormData] = useState({
    exercise_id: '',
    duration: '',
    calories: ''
  });

  useEffect(() => {
    axios.get('/exercises').then(res => setExercises(res.data));
    refreshWorkouts();
  }, []);

  const refreshWorkouts = () => {
    axios.get('/workouts').then(res => {
      setWorkouts(res.data);
      axios.get('/stats').then(statsRes => setStats(statsRes.data));
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/workouts', formData);
      refreshWorkouts();
      setFormData({ exercise_id: '', duration: '', calories: '' });
    } catch (err) {
      alert('Error logging workout');
    }
  };

  const getChartData = () => ({
    labels: workouts.map(w => new Date(w.date).toLocaleDateString()),
    datasets: [{
      label: 'Calories Burned',
      data: workouts.map(w => w.calories),
      borderColor: 'rgb(75, 192, 192)',
    }]
  });

  const renderPage = () => {
    switch(currentPage) {
      case 'dashboard':
        return (
          <div className="dashboard">
            <h2>Fitness Dashboard</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <h3>{stats.total_workouts}</h3>
                <p>Total Workouts</p>
              </div>
              <div className="stat-card">
                <h3>{stats.total_calories}</h3>
                <p>Calories Burned</p>
              </div>
            </div>
            <div className="chart-container">
              <Line data={getChartData()} />
            </div>
          </div>
        );
      
      case 'log':
        return (
          <div className="workout-form">
            <h2>Log New Workout</h2>
            <form onSubmit={handleSubmit}>
              <select 
                value={formData.exercise_id}
                onChange={e => setFormData({...formData, exercise_id: e.target.value})}
                required
              >
                <option value="">Select Exercise</option>
                {exercises.map(ex => (
                  <option key={ex.id} value={ex.id}>{ex.name}</option>
                ))}
              </select>
              <input
                type="number"
                placeholder="Duration (minutes)"
                value={formData.duration}
                onChange={e => setFormData({...formData, duration: e.target.value})}
                required
              />
              <input
                type="number"
                placeholder="Calories Burned"
                value={formData.calories}
                onChange={e => setFormData({...formData, calories: e.target.value})}
                required
              />
              <button type="submit">Log Workout</button>
            </form>
          </div>
        );

      case 'exercises':
        return (
          <div className="exercise-library">
            <h2>Exercise Library</h2>
            <div className="exercise-grid">
              {exercises.map(ex => (
                <div key={ex.id} className="exercise-card">
                  <h3>{ex.name}</h3>
                  <p>Category: {ex.category}</p>
                  <p>MET Value: {ex.met}</p>
                </div>
              ))}
            </div>
          </div>
        );
    }
  };

  return (
    <main>
      <nav className="navbar">
        <button onClick={() => setCurrentPage('dashboard')}>Dashboard</button>
        <button onClick={() => setCurrentPage('log')}>Log Workout</button>
        <button onClick={() => setCurrentPage('exercises')}>Exercises</button>
      </nav>
      
      {renderPage()}

      <div className="workout-history">
        <h3>Recent Workouts</h3>
        {workouts.map(workout => (
          <div key={workout.id} className="workout-card">
            <p>{exercises.find(ex => ex.id === workout.exercise_id)?.name}</p>
            <p>{workout.duration} minutes</p>
            <p>{workout.calories} kcal</p>
          </div>
        ))}
      </div>
    </main>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
