import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import "./App.css";

const App = () => {
  const [page, setPage] = useState("login");
  const [user, setUser] = useState(null);
  const [loginData, setLoginData] = useState({ username: "", password: "" });
  const [registerData, setRegisterData] = useState({ username: "", password: "" });
  const [workout, setWorkout] = useState([]);
  const [exerciseLibrary, setExerciseLibrary] = useState([]);
  const [progressData, setProgressData] = useState([]);

  const fetchExerciseLibrary = async () => {
    const res = await axios.get("/api/exercise_library");
    setExerciseLibrary(res.data.exercises || []);
  };

  const fetchProgress = async () => {
    if (user) {
      const res = await axios.get(`/api/progress?username=${user}`);
      setProgressData(res.data.workouts || []);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/api/register", registerData);
      setPage("login");
    } catch (err) {
      alert(err.response.data.error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("/api/login", loginData);
      setUser(res.data.username);
      setPage("dashboard");
    } catch (err) {
      alert(err.response.data.error);
    }
  };

  const handleWorkoutSubmission = async (e) => {
    e.preventDefault();
    const date = new Date().toISOString().slice(0, 10); // Format 5273-MM-DD
    try {
      await axios.post("/api/log_workout", {
        username: user,
        exercises: workout,
        date,
      });
      alert("Workout logged!");
      setWorkout([]);
      fetchProgress();
    } catch (err) {
      alert(err.response.data.error);
    }
  };

  useEffect(() => {
    fetchExerciseLibrary();
    if (user) fetchProgress();
  }, [user]);

  if (page === "login") {
    return (
      <div className="auth-container">
        <h2>Login</h2>
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Username"
            value={loginData.username}
            onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
          />
          <input
            type="password"
            placeholder="Password"
            value={loginData.password}
            onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
          />
          <button type="submit">Login</button>
        </form>
        <p onClick={() => setPage("register")}>Create an account</p>
      </div>
    );
  }

  if (page === "register") {
    return (
      <div className="auth-container">
        <h2>Register</h2>
        <form onSubmit={handleRegister}>
          <input
            type="text"
            placeholder="Username"
            value={registerData.username}
            onChange={(e) => setRegisterData({ ...registerData, username: e.target.value })}
          />
          <input
            type="password"
            placeholder="Password"
            value={registerData.password}
            onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
          />
          <button type="submit">Register</button>
        </form>
        <p onClick={() => setPage("login")}>Back to Login</p>
      </div>
    );
  }

  if (page === "dashboard") {
    return (
      <div className="dashboard">
        <h2>Welcome, {user}!</h2>
        <h3>Log a Workout</h3>
        <form onSubmit={handleWorkoutSubmission}>
          <select
            multiple
            value={workout}
            onChange={(e) =>
              setWorkout(Array.from(e.target.selectedOptions, (option) => option.value))
            }
          >
            {exerciseLibrary.map((exercise) => (
              <option key={exercise} value={exercise}>
                {exercise}
              </option>
            ))}
          </select>
          <button type="submit">Log Workout</button>
        </form>
        <h3>Progress</h3>
        <ul>
          {Object.entries(progressData).map(([date, exercises]) => (
            <li key={date}>
              {date}: {exercises.join(", ")}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return null;
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
