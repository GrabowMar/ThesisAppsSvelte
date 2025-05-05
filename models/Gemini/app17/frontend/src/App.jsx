import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [currentView, setCurrentView] = useState('workoutLog');
    const [workouts, setWorkouts] = useState([]);
    const [exercises, setExercises] = useState([]);
    const [selectedExercises, setSelectedExercises] = useState([]);
    const [stats, setStats] = useState({});

    useEffect(() => {
        fetchExercises();
        fetchWorkouts();
        fetchStats();
    }, []);

    const fetchExercises = async () => {
        try {
            const response = await fetch('/api/exercises');
            const data = await response.json();
            setExercises(data);
        } catch (error) {
            console.error("Error fetching exercises:", error);
        }
    };

    const fetchWorkouts = async () => {
        try {
            const response = await fetch('/api/workouts');
            const data = await response.json();
            setWorkouts(data);
        } catch (error) {
            console.error("Error fetching workouts:", error);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error("Error fetching stats:", error);
        }
    };


    const handleExerciseSelect = (exercise) => {
        setSelectedExercises([...selectedExercises, exercise]);
    };

    const handleRemoveExercise = (exerciseToRemove) => {
        setSelectedExercises(selectedExercises.filter(exercise => exercise.id !== exerciseToRemove.id));
    };



    const handleSubmitWorkout = async () => {
        if (selectedExercises.length === 0) {
            alert("Please select at least one exercise.");
            return;
        }

        try {
            const response = await fetch('/api/workouts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ exercises: selectedExercises }),
            });

            if (response.ok) {
                const newWorkout = await response.json();
                setWorkouts([...workouts, newWorkout]);
                setSelectedExercises([]); // Clear selected exercises after submission
                fetchStats(); // Refresh stats
                setCurrentView('workoutLog');  // Go back to workout log
            } else {
                const errorData = await response.json();
                alert(`Error submitting workout: ${errorData.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error("Error submitting workout:", error);
            alert("Failed to submit workout.  Please try again.");
        }
    };


    const renderView = () => {
        switch (currentView) {
            case 'workoutLog':
                return (
                    <div>
                        <h2>Workout Log</h2>
                        <ul>
                            {workouts.map(workout => (
                                <li key={workout.id}>
                                    {new Date(workout.date).toLocaleDateString()} -
                                    {workout.exercises.map(exercise => exercise.name).join(', ')}
                                </li>
                            ))}
                        </ul>
                        <button onClick={() => setCurrentView('addWorkout')}>Add Workout</button>
                        <button onClick={() => setCurrentView('progressTracking')}>View Progress</button>
                    </div>
                );
            case 'addWorkout':
                return (
                    <div>
                        <h2>Add Workout</h2>
                        <div className="exercise-list">
                            <h3>Exercises</h3>
                            <ul>
                                {exercises.map(exercise => (
                                    <li key={exercise.id}>
                                        {exercise.name} ({exercise.type})
                                        <button onClick={() => handleExerciseSelect(exercise)}>Add</button>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="selected-exercises">
                            <h3>Selected Exercises</h3>
                            <ul>
                                {selectedExercises.map(exercise => (
                                    <li key={exercise.id}>
                                        {exercise.name}
                                        <button onClick={() => handleRemoveExercise(exercise)}>Remove</button>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <button onClick={handleSubmitWorkout}>Submit Workout</button>
                        <button onClick={() => setCurrentView('workoutLog')}>Cancel</button>
                    </div>
                );
            case 'progressTracking':
                return (
                    <div>
                        <h2>Progress Tracking</h2>
                        <p>Total Workouts: {stats.total_workouts || 0}</p>
                        {stats.most_frequent_exercises && Object.keys(stats.most_frequent_exercises).length > 0 ? (
                            <div>
                                <p>Most Frequent Exercises:</p>
                                <ul>
                                    {Object.entries(stats.most_frequent_exercises).map(([exercise, count]) => (
                                        <li key={exercise}>{exercise}: {count}</li>
                                    ))}
                                </ul>
                            </div>
                        ) : (
                            <p>No exercise data available yet.</p>
                        )}
                        <button onClick={() => setCurrentView('workoutLog')}>Back to Workout Log</button>
                    </div>
                );
            default:
                return <div>Unknown view</div>;
        }
    };

    return (
        <div className="App">
            <h1>Fitness Logger</h1>
            {renderView()}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
