// App.jsx
import React, { useState, useEffect } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const [exercises, setExercises] = useState([]);
  const [workouts, setWorkouts] = useState([]);
  const [newWorkout, setNewWorkout] = useState({
    exercise_id: 1,
    reps: 0,
    weight: 0,
  });

  useEffect(() => {
    axios.get("http://localhost:5033/exercises")
      .then(response => {
        setExercises(response.data);
      })
      .catch(error => {
        console.error(error);
      });

    axios.get("http://localhost:5033/workouts")
      .then(response => {
        setWorkouts(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleAddWorkout = () => {
    axios.post("http://localhost:5033/workouts", newWorkout)
      .then(response => {
        setWorkouts([...workouts, response.data]);
        setNewWorkout({
          exercise_id: 1,
          reps: 0,
          weight: 0,
        });
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleExerciseChange = (event) => {
    setNewWorkout({ ...newWorkout, exercise_id: parseInt(event.target.value) });
  };

  const handleRepsChange = (event) => {
    setNewWorkout({ ...newWorkout, reps: parseInt(event.target.value) });
  };

  const handleWeightChange = (event) => {
    setNewWorkout({ ...newWorkout, weight: parseInt(event.target.value) });
  };

  return (
    <div className="container">
      <h1>Fitness Logger</h1>
      <h2>Exercises:</h2>
      <ul>
        {exercises.map((exercise) => (
          <li key={exercise.id}>{exercise.name}</li>
        ))}
      </ul>
      <h2>Workouts:</h2>
      <ul>
        {workouts.map((workout, index) => (
          <li key={index}>{workout.exercise_id} - {workout.reps} reps - {workout.weight} weight</li>
        ))}
      </ul>
      <h2>Add new workout:</h2>
      <select value={newWorkout.exercise_id} onChange={handleExerciseChange}>
        {exercises.map((exercise) => (
          <option key={exercise.id} value={exercise.id}>{exercise.name}</option>
        ))}
      </select>
      <input type="number" value={newWorkout.reps} onChange={handleRepsChange} placeholder="Reps" />
      <input type="number" value={newWorkout.weight} onChange={handleWeightChange} placeholder="Weight" />
      <button onClick={handleAddWorkout}>Add workout</button>
    </div>
  );
}

export default App;
