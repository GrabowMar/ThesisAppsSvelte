// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [polls, setPolls] = useState({});
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['Option 1', 'Option 2']);
  const [timeLimit, setTimeLimit] = useState(null);
  const [selectedPoll, setSelectedPoll] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5021/get_polls')
      .then(response => response.json())
      .then(data => setPolls(data.polls));
  }, []);

  const handleCreatePoll = () => {
    const pollData = {
      question,
      options,
      time_limit: timeLimit ? new Date(timeLimit) : null
    };
    fetch('http://localhost:5021/create_poll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pollData)
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleCastVote = () => {
    const voteData = {
      poll_id: selectedPoll,
      option: selectedOption
    };
    fetch('http://localhost:5021/cast_vote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(voteData)
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleGetResults = () => {
    const resultsData = {
      poll_id: selectedPoll
    };
    fetch('http://localhost:5021/get_results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(resultsData)
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  return (
    <div>
      <h1>Polling System</h1>
      <h2>Create Poll</h2>
      <input type="text" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Question" />
      <ul>
        {options.map((option, index) => (
          <li key={index}>
            <input type="text" value={option} onChange={e => setOptions(options.map((o, i) => i === index ? e.target.value : o))} />
          </li>
        ))}
      </ul>
      <input type="datetime-local" value={timeLimit} onChange={e => setTimeLimit(e.target.value)} />
      <button onClick={handleCreatePoll}>Create Poll</button>
      <h2>Cast Vote</h2>
      <select value={selectedPoll} onChange={e => setSelectedPoll(e.target.value)}>
        <option value="">Select Poll</option>
        {Object.keys(polls).map(pollId => (
          <option key={pollId} value={pollId}>{polls[pollId].question}</option>
        ))}
      </select>
      <select value={selectedOption} onChange={e => setSelectedOption(e.target.value)}>
        <option value="">Select Option</option>
        {selectedPoll && polls[selectedPoll].options.map(option => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
      <button onClick={handleCastVote}>Cast Vote</button>
      <h2>Get Results</h2>
      <select value={selectedPoll} onChange={e => setSelectedPoll(e.target.value)}>
        <option value="">Select Poll</option>
        {Object.keys(polls).map(pollId => (
          <option key={pollId} value={pollId}>{polls[pollId].question}</option>
        ))}
      </select>
      <button onClick={handleGetResults}>Get Results</button>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
