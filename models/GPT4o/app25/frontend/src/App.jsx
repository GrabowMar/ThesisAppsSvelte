import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [page, setPage] = useState("dashboard");
  const [mood, setMood] = useState("");
  const [stress, setStress] = useState("");
  const [journalEntry, setJournalEntry] = useState("");
  const [data, setData] = useState({ mood: [], stress: [], journal: [] });

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("/api/data");
      const result = await res.json();
      setData(result);
    };
    fetchData();
  }, [mood, stress, journalEntry]);

  // Navigation between pages
  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard />;
      case "logMood":
        return (
          <MoodTracker
            mood={mood}
            onMoodChange={setMood}
            onLogSubmit={logMood}
          />
        );
      case "logStress":
        return (
          <StressTracker
            stress={stress}
            onStressChange={setStress}
            onLogSubmit={logStress}
          />
        );
      case "journal":
        return (
          <Journal
            journalEntry={journalEntry}
            onJournalChange={setJournalEntry}
            onLogSubmit={saveJournal}
          />
        );
      default:
        return <Dashboard />;
    }
  };

  // API Operations
  const logMood = async () => {
    const date = new Date().toISOString().split("T")[0];
    await fetch("/api/mood", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mood, date }),
    });
    alert("Mood logged successfully!");
  };

  const logStress = async () => {
    const date = new Date().toISOString().split("T")[0];
    await fetch("/api/stress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stress, date }),
    });
    alert("Stress level logged successfully!");
  };

  const saveJournal = async () => {
    const date = new Date().toISOString().split("T")[0];
    await fetch("/api/journal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entry: journalEntry, date }),
    });
    alert("Journal entry saved!");
  };

  // Component Definitions
  const Dashboard = () => (
    <div className="dashboard">
      <h1>Dashboard</h1>
      <p>Welcome to the mental health app. Select a feature from the menu above.</p>
      <button onClick={() => setPage("logMood")}>Log Mood</button>
      <button onClick={() => setPage("logStress")}>Log Stress</button>
      <button onClick={() => setPage("journal")}>Journal</button>
    </div>
  );

  const MoodTracker = ({ mood, onMoodChange, onLogSubmit }) => (
    <div className="tracker">
      <h1>Log Your Mood</h1>
      <input
        type="text"
        placeholder="Enter mood (e.g., Happy)"
        value={mood}
        onChange={(e) => onMoodChange(e.target.value)}
      />
      <button onClick={onLogSubmit}>Submit</button>
    </div>
  );

  const StressTracker = ({ stress, onStressChange, onLogSubmit }) => (
    <div className="tracker">
      <h1>Log Stress</h1>
      <input
        type="text"
        placeholder="Enter stress level (e.g., 5/10)"
        value={stress}
        onChange={(e) => onStressChange(e.target.value)}
      />
      <button onClick={onLogSubmit}>Submit</button>
    </div>
  );

  const Journal = ({ journalEntry, onJournalChange, onLogSubmit }) => (
    <div className="tracker">
      <h1>Write a Journal Entry</h1>
      <textarea
        placeholder="Share your thoughts..."
        value={journalEntry}
        onChange={(e) => onJournalChange(e.target.value)}
      ></textarea>
      <button onClick={onLogSubmit}>Submit</button>
    </div>
  );

  return <main>{renderPage()}</main>;
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
