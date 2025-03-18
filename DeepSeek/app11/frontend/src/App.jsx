import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [page, setPage] = useState('home');
  const [polls, setPolls] = useState([]);
  const [currentPoll, setCurrentPoll] = useState(null);
  const [voterId, setVoterId] = useState('');
  const [selectedOption, setSelectedOption] = useState('');
  const [pollResults, setPollResults] = useState({});

  useEffect(() => {
    fetch('http://localhost:5181/poll')
      .then((res) => res.json())
      .then((data) => setPolls(data))
      .catch((err) => console.error(err));
  }, []);

  const handleCreatePoll = (question, options, duration) => {
    fetch('http://localhost:5181/poll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, options, duration }),
    })
      .then((res) => res.json())
      .then((data) => {
        setPolls([...polls, data]);
        setPage('home');
      })
      .catch((err) => console.error(err));
  };

  const handleVote = (pollId) => {
    fetch(`http://localhost:5181/poll/${pollId}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ option: selectedOption, voter_id: voterId }),
    })
      .then((res) => res.json())
      .then(() => {
        setPage('results');
        fetchResults(pollId);
      })
      .catch((err) => console.error(err));
  };

  const fetchResults = (pollId) => {
    fetch(`http://localhost:5181/poll/${pollId}/results`)
      .then((res) => res.json())
      .then((data) => setPollResults(data))
      .catch((err) => console.error(err));
  };

  return (
    <div className="app">
      <nav>
        <button onClick={() => setPage('home')}>Home</button>
        <button onClick={() => setPage('create')}>Create Poll</button>
      </nav>
      {page === 'home' && (
        <div>
          <h1>Active Polls</h1>
          {polls.map((poll) => (
            <div key={poll.id} onClick={() => setCurrentPoll(poll)}>
              <h2>{poll.question}</h2>
              <p>Ends at: {poll.end_time}</p>
              <button onClick={() => setPage('vote')}>Vote</button>
              <button onClick={() => fetchResults(poll.id)}>Results</button>
            </div>
          ))}
        </div>
      )}
      {page === 'create' && (
        <CreatePollForm onCreatePoll={handleCreatePoll} />
      )}
      {page === 'vote' && currentPoll && (
        <div>
          <h2>{currentPoll.question}</h2>
          {currentPoll.options.map((option) => (
            <label key={option}>
              <input
                type="radio"
                name="option"
                value={option}
                onChange={(e) => setSelectedOption(e.target.value)}
              />
              {option}
            </label>
          ))}
          <input
            type="text"
            placeholder="Your Voter ID"
            value={voterId}
            onChange={(e) => setVoterId(e.target.value)}
          />
          <button onClick={() => handleVote(currentPoll.id)}>Submit Vote</button>
        </div>
      )}
      {page === 'results' && (
        <div>
          <h2>Results</h2>
          {Object.entries(pollResults).map(([option, count]) => (
            <p key={option}>
              {option}: {count} votes
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

const CreatePollForm = ({ onCreatePoll }) => {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState('');
  const [duration, setDuration] = useState(10);

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreatePoll(question, options.split(','), duration);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Poll Question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <input
        type="text"
        placeholder="Options (comma separated)"
        value={options}
        onChange={(e) => setOptions(e.target.value)}
      />
      <input
        type="number"
        placeholder="Duration (minutes)"
        value={duration}
        onChange={(e) => setDuration(e.target.value)}
      />
      <button type="submit">Create Poll</button>
    </form>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
