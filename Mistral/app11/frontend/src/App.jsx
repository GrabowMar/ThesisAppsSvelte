import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:5101';

function CreatePoll() {
    const [question, setQuestion] = useState('');
    const [options, setOptions] = useState(['', '']);
    const [duration, setDuration] = useState(10);

    const handleCreatePoll = async () => {
        const data = { question, options, duration };
        const response = await axios.post(`${API_BASE_URL}/create_poll`, data);
        alert('Poll created successfully! Poll ID: ' + response.data.poll_id);
    };

    return (
        <div>
            <h2>Create Poll</h2>
            <input
                type="text"
                placeholder="Question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
            />
            {options.map((option, index) => (
                <input
                    key={index}
                    type="text"
                    placeholder={`Option ${index + 1}`}
                    value={option}
                    onChange={(e) => {
                        const newOptions = [...options];
                        newOptions[index] = e.target.value;
                        setOptions(newOptions);
                    }}
                />
            ))}
            <input
                type="number"
                placeholder="Duration (minutes)"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
            />
            <button onClick={handleCreatePoll}>Create Poll</button>
        </div>
    );
}

function PollList() {
    const [polls, setPolls] = useState([]);

    useEffect(() => {
        const fetchPolls = async () => {
            const response = await axios.get(`${API_BASE_URL}/polls`);
            setPolls(response.data);
        };
        fetchPolls();
    }, []);

    return (
        <div>
            <h2>Polls</h2>
            {polls.map((poll, index) => (
                <div key={index}>
                    <h3>{poll.question}</h3>
                    <Link to={`/poll/${poll.id}`}>Vote</Link>
                    <Link to={`/results/${poll.id}`}>Results</Link>
                    <Link to={`/analytics/${poll.id}`}>Analytics</Link>
                </div>
            ))}
        </div>
    );
}

function Vote({ pollId }) {
    const [options, setOptions] = useState([]);
    const [selectedOption, setSelectedOption] = useState('');

    useEffect(() => {
        const fetchPoll = async () => {
            const response = await axios.get(`${API_BASE_URL}/polls`);
            const poll = response.data.find(p => p.id === pollId);
            setOptions(poll.options);
        };
        fetchPoll();
    }, [pollId]);

    const handleVote = async () => {
        const data = { option: selectedOption };
        await axios.post(`${API_BASE_URL}/vote/${pollId}`, data);
        alert('Vote cast successfully!');
    };

    return (
        <div>
            <h2>Vote</h2>
            {options.map((option, index) => (
                <div key={index}>
                    <input
                        type="radio"
                        name="option"
                        value={option}
                        onChange={(e) => setSelectedOption(e.target.value)}
                    />
                    {option}
                </div>
            ))}
            <button onClick={handleVote}>Vote</button>
        </div>
    );
}

function Results({ pollId }) {
    const [results, setResults] = useState({});

    useEffect(() => {
        const fetchResults = async () => {
            const response = await axios.get(`${API_BASE_URL}/results/${pollId}`);
            setResults(response.data);
        };
        fetchResults();
    }, [pollId]);

    return (
        <div>
            <h2>Results</h2>
            {Object.entries(results).map(([option, count], index) => (
                <div key={index}>
                    {option}: {count} votes
                </div>
            ))}
        </div>
    );
}

function Analytics({ pollId }) {
    const [analytics, setAnalytics] = useState({});

    useEffect(() => {
        const fetchAnalytics = async () => {
            const response = await axios.get(`${API_BASE_URL}/analytics/${pollId}`);
            setAnalytics(response.data);
        };
        fetchAnalytics();
    }, [pollId]);

    return (
        <div>
            <h2>Analytics</h2>
            <div>Total Votes: {analytics.total_votes}</div>
            {Object.entries(analytics.results).map(([option, percentage], index) => (
                <div key={index}>
                    {option}: {(percentage * 100).toFixed(2)}%
                </div>
            ))}
        </div>
    );
}

function App() {
    return (
        <Router>
            <div>
                <nav>
                    <Link to="/">Home</Link>
                    <Link to="/create_poll">Create Poll</Link>
                    <Link to="/polls">Polls</Link>
                </nav>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/create_poll" element={<CreatePoll />} />
                    <Route path="/polls" element={<PollList />} />
                    <Route path="/poll/:id" element={<Vote />} />
                    <Route path="/results/:id" element={<Results />} />
                    <Route path="/analytics/:id" element={<Analytics />} />
                </Routes>
            </div>
        </Router>
    );
}

function Home() {
    return <h1>Welcome to the Polling System</h1>;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
