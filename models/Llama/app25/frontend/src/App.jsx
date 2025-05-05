// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [mood, setMood] = useState('');
    const [stressLevel, setStressLevel] = useState('');
    const [journalEntry, setJournalEntry] = useState('');
    const [copingStrategies, setCopingStrategies] = useState([]);
    const [reminders, setReminders] = useState([]);
    const [newReminder, setNewReminder] = useState('');
    const [progress, setProgress] = useState({});

    useEffect(() => {
        fetchCopingStrategies();
        fetchReminders();
        fetchProgress();
    }, []);

    const trackMood = () => {
        fetch('/api/mood', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mood }),
        })
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.error('Error tracking mood:', error));
    };

    const trackStress = () => {
        fetch('/api/stress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stressLevel }),
        })
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.error('Error tracking stress:', error));
    };

    const addJournalEntry = () => {
        fetch('/api/journal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ journalEntry }),
        })
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.error('Error adding journal entry:', error));
    };

    const fetchCopingStrategies = () => {
        fetch('/api/coping_strategies')
            .then(response => response.json())
            .then(data => setCopingStrategies(data))
            .catch(error => console.error('Error fetching coping strategies:', error));
    };

    const fetchReminders = () => {
        fetch('/api/reminders')
            .then(response => response.json())
            .then(data => setReminders(data))
            .catch(error => console.error('Error fetching reminders:', error));
    };

    const addReminder = () => {
        fetch('/api/reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reminder: newReminder }),
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                fetchReminders();
                setNewReminder('');
            })
            .catch(error => console.error('Error adding reminder:', error));
    };

    const fetchProgress = () => {
        fetch('/api/progress')
            .then(response => response.json())
            .then(data => setProgress(data))
            .catch(error => console.error('Error fetching progress:', error));
    };

    return (
        <div className="app-container">
            <h1>Mental Wellness Tracking System</h1>
            <section>
                <h2>Track Mood</h2>
                <input type="text" value={mood} onChange={(e) => setMood(e.target.value)} placeholder="Enter your mood" />
                <button onClick={trackMood}>Track</button>
            </section>
            <section>
                <h2>Track Stress Level</h2>
                <input type="text" value={stressLevel} onChange={(e) => setStressLevel(e.target.value)} placeholder="Enter your stress level" />
                <button onClick={trackStress}>Track</button>
            </section>
            <section>
                <h2>Journal Entry</h2>
                <textarea value={journalEntry} onChange={(e) => setJournalEntry(e.target.value)} placeholder="Write your journal entry" />
                <button onClick={addJournalEntry}>Add Entry</button>
            </section>
            <section>
                <h2>Coping Strategies</h2>
                <ul>
                    {copingStrategies.map((strategy, index) => (
                        <li key={index}>{strategy}</li>
                    ))}
                </ul>
            </section>
            <section>
                <h2>Reminders</h2>
                <ul>
                    {reminders.map((reminder, index) => (
                        <li key={index}>{reminder.reminder}</li>
                    ))}
                </ul>
                <input type="text" value={newReminder} onChange={(e) => setNewReminder(e.target.value)} placeholder="Add a new reminder" />
                <button onClick={addReminder}>Add Reminder</button>
            </section>
            <section>
                <h2>Progress</h2>
                <p>Mood tracked: {progress.mood}</p>
                <p>Stress tracked: {progress.stress}</p>
                <p>Journal entries: {progress.journal_entries}</p>
            </section>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
