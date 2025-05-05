import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import axios from 'axios';

const App = () => {
  const [mood, setMood] = useState('');
  const [stress, setStress] = useState('');
  const [journalEntry, setJournalEntry] = useState('');
  const [copingStrategies, setCopingStrategies] = useState([]);
  const [progress, setProgress] = useState({});
  const [reminders, setReminders] = useState([]);

  useEffect(() => {
    axios.get('/api/coping_strategies')
      .then(response => setCopingStrategies(response.data))
      .catch(error => console.error('Error fetching coping strategies:', error));

    axios.get('/api/progress')
      .then(response => setProgress(response.data))
      .catch(error => console.error('Error fetching progress:', error));

    axios.get('/api/reminders')
      .then(response => setReminders(response.data))
      .catch(error => console.error('Error fetching reminders:', error));
  }, []);

  const handleMoodSubmit = () => {
    axios.post('/api/log_mood', { mood })
      .then(response => console.log(response.data.message))
      .catch(error => console.error('Error logging mood:', error));
  };

  const handleStressSubmit = () => {
    axios.post('/api/log_stress', { stress })
      .then(response => console.log(response.data.message))
      .catch(error => console.error('Error logging stress:', error));
  };

  const handleJournalSubmit = () => {
    axios.post('/api/journal', { entry: journalEntry })
      .then(response => console.log(response.data.message))
      .catch(error => console.error('Error logging journal entry:', error));
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home
          copingStrategies={copingStrategies}
          progress={progress}
          reminders={reminders}
        />} />
        <Route path="/mood" element={<MoodForm handleSubmit={handleMoodSubmit} mood={mood} setMood={setMood} />} />
        <Route path="/stress" element={<StressForm handleSubmit={handleStressSubmit} stress={stress} setStress={setStress} />} />
        <Route path="/journal" element={<JournalForm handleSubmit={handleJournalSubmit} journalEntry={journalEntry} setJournalEntry={setJournalEntry} />} />
      </Routes>
    </Router>
  );
};

const Home = ({ copingStrategies, progress, reminders }) => (
  <div>
    <h1>Mental Wellness Tracking System</h1>
    <div>
      <h2>Coping Strategies</h2>
      <ul>
        {copingStrategies.map((strategy, index) => (
          <li key={index}>{strategy}</li>
        ))}
      </ul>
    </div>
    <div>
      <h2>Progress</h2>
      <pre>{JSON.stringify(progress, null, 2)}</pre>
    </div>
    <div>
      <h2>Reminders</h2>
      <ul>
        {reminders.map((reminder, index) => (
          <li key={index}>{reminder}</li>
        ))}
      </ul>
    </div>
  </div>
);

const MoodForm = ({ handleSubmit, mood, setMood }) => (
  <div>
    <h1>Log Mood</h1>
    <input type="text" value={mood} onChange={(e) => setMood(e.target.value)} />
    <button onClick={handleSubmit}>Submit</button>
  </div>
);

const StressForm = ({ handleSubmit, stress, setStress }) => (
  <div>
    <h1>Log Stress</h1>
    <input type="text" value={stress} onChange={(e) => setStress(e.target.value)} />
    <button onClick={handleSubmit}>Submit</button>
  </div>
);

const JournalForm = ({ handleSubmit, journalEntry, setJournalEntry }) => (
  <div>
    <h1>Journal Entry</h1>
    <textarea value={journalEntry} onChange={(e) => setJournalEntry(e.target.value)} />
    <button onClick={handleSubmit}>Submit</button>
  </div>
);

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
