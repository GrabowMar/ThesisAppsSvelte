import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

const App = () => {
  const [polls, setPolls] = useState([]);
  const [selectedPoll, setSelectedPoll] = useState(null);
  const [voteOption, setVoteOption] = useState('');
  const [analytics, setAnalytics] = useState(null);

  // Fetch all polls
  useEffect(() => {
    fetch('/api/polls')
      .then((response) => response.json())
      .then((data) => setPolls(data))
      .catch((error) => console.error("Error fetching polls:", error));
  }, []);

  // Fetch poll details
  const fetchPoll = (pollId) => {
    fetch(`/api/polls/${pollId}`)
      .then((response) => response.json())
      .then((data) => setSelectedPoll(data))
      .catch((error) => console.error("Error fetching poll:", error));
  };

  // Cast vote
  const castVote = (pollId) => {
    fetch(`/api/polls/${pollId}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ option: voteOption }),
    })
      .then((response) => response.json())
      .then((data) => {
        alert(data.message);
        fetchPollDetails(pollId);
      })
      .catch((error) => console.error("Error casting vote:", error));
  };

  // Fetch poll analytics
  const fetchPollDetails = (pollId) => {
    fetch(`/api/polls/${pollId}/results`)
      .then((response) => response.json())
      .then((data) => setAnalytics(data))
      .catch((error) => console.error("Error fetching analytics:", error));
  };

  return (
    <main>
      <h1>Polling Application</h1>
      <div>
        <h2>Polls:</h2>
        <ul>
          {polls.map((poll) => (
            <li key={poll.id}>
              <button onClick={() => fetchPoll(poll.id)}>{poll.question}</button>
            </li>
          ))}
        </ul>
      </div>
      {selectedPoll && (
        <div>
          <h2>{selectedPoll.question}</h2>
          <select onChange={(e) => setVoteOption(e.target.value)}>
            <option value="">Select an option</option>
            {selectedPoll.options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <button onClick={() => castVote(selectedPoll.id)}>Vote</button>
        </div>
      )}
      {analytics && (
        <div>
          <h2>Analytics</h2>
          <p>Total Votes: {analytics.total_votes}</p>
          <ul>
            {Object.entries(analytics.options).map(([option, count]) => (
              <li key={option}>
                {option}: {count} votes
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
};

// Mounting Logic
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
