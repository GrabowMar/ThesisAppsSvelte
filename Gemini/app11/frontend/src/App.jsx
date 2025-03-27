import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [polls, setPolls] = useState([]);
  const [newPollTitle, setNewPollTitle] = useState('');
  const [newPollOptions, setNewPollOptions] = useState('');
  const [selectedPoll, setSelectedPoll] = useState(null);
  const [voteOption, setVoteOption] = useState('');
  const [results, setResults] = useState({});
  const [view, setView] = useState('list'); // 'list', 'create', 'vote', 'results'
  const [duration, setDuration] = useState(60); // Poll duration in minutes
  const [error, setError] = useState('');


  useEffect(() => {
    fetchPolls();
  }, []);

  const fetchPolls = async () => {
    try {
      const response = await fetch('/api/polls');
      if (!response.ok) {
        throw new Error('Failed to fetch polls');
      }
      const data = await response.json();
      setPolls(data.polls);
    } catch (error) {
      console.error('Error fetching polls:', error);
      setError('Failed to load polls. Please try again.');
    }
  };

  const createPoll = async () => {
    if (!newPollTitle || !newPollOptions) {
      alert('Title and options are required');
      return;
    }

    const optionsArray = newPollOptions.split(',').map(option => option.trim()).filter(option => option !== '');

    if (optionsArray.length < 2) {
      alert('At least two options are required');
      return;
    }

    try {
      const response = await fetch('/api/polls', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newPollTitle, options: optionsArray, duration: parseInt(duration) }),
      });

      if (!response.ok) {
        throw new Error('Failed to create poll');
      }

      setNewPollTitle('');
      setNewPollOptions('');
      setDuration(60);
      fetchPolls(); // Refresh poll list
      setView('list');

    } catch (error) {
      console.error('Error creating poll:', error);
      setError('Failed to create poll. Please try again.');
    }
  };


  const handleVote = async () => {
    if (!voteOption) {
      alert('Please select an option to vote for.');
      return;
    }

    try {
      const response = await fetch(`/api/polls/${selectedPoll.id}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ option: voteOption }),
      });

      if (!response.ok) {
        throw new Error('Failed to cast vote');
      }

      fetchPolls(); // Refresh polls
      fetchResults(selectedPoll.id); //Refresh results
      setView('results');

    } catch (error) {
      console.error('Error casting vote:', error);
      setError('Failed to cast vote. Please try again.');
    }
  };

  const fetchResults = async (pollId) => {
    try {
      const response = await fetch(`/api/polls/${pollId}/results`);
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error fetching results:', error);
      setError('Failed to fetch results. Please try again.');
    }
  };

  const showVoteView = (poll) => {
    setSelectedPoll(poll);
    setVoteOption('');
    setView('vote');
  };

  const showResultsView = async (pollId) => {
    setSelectedPoll(polls.find(poll => poll.id === pollId));
    await fetchResults(pollId);
    setView('results');
  };

  const handleBackToList = () => {
    setSelectedPoll(null);
    setResults({});
    setView('list');
  };


  let content;

  if (view === 'list') {
    content = (
      <div>
        <h2>Current Polls</h2>
        {error && <div className="error">{error}</div>}
        <ul>
          {polls.map((poll) => (
            <li key={poll.id}>
              {poll.title} - Options: {poll.options.join(', ')}
              {poll.is_active ? (
                <>
                  <button onClick={() => showVoteView(poll)}>Vote</button>
                  <button onClick={() => showResultsView(poll.id)}>Results</button>
                </>
              ) : (
                <span> (Closed) - <button onClick={() => showResultsView(poll.id)}>Results</button></span>
              )}
            </li>
          ))}
        </ul>
        <button onClick={() => setView('create')}>Create New Poll</button>
      </div>
    );
  } else if (view === 'create') {
    content = (
      <div>
        <h2>Create a New Poll</h2>
        <label>
          Title:
          <input type="text" value={newPollTitle} onChange={(e) => setNewPollTitle(e.target.value)} />
        </label>
        <br />
        <label>
          Options (comma-separated):
          <input type="text" value={newPollOptions} onChange={(e) => setNewPollOptions(e.target.value)} />
        </label>
        <br />
        <label>
          Duration (minutes, optional):
          <input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} />
        </label>
        <br />
        <button onClick={createPoll}>Create Poll</button>
        <button onClick={() => setView('list')}>Back to List</button>
      </div>
    );
  } else if (view === 'vote') {
    content = (
      <div>
        <h2>Vote: {selectedPoll.title}</h2>
        {error && <div className="error">{error}</div>}
        <form>
          {selectedPoll.options.map((option) => (
            <div key={option}>
              <label>
                <input
                  type="radio"
                  value={option}
                  checked={voteOption === option}
                  onChange={() => setVoteOption(option)}
                />
                {option}
              </label>
            </div>
          ))}
          <button type="button" onClick={handleVote}>
            Vote
          </button>
          <button type="button" onClick={handleBackToList}>Back to List</button>
        </form>
      </div>
    );
  } else if (view === 'results') {
    content = (
      <div>
        <h2>Results: {selectedPoll ? selectedPoll.title : 'Poll Results'}</h2>
        {error && <div className="error">{error}</div>}
        {Object.keys(results).length > 0 ? (
          <ul>
            {Object.entries(results).map(([option, data]) => (
              <li key={option}>
                {option}: {data.votes} votes ({data.percentage.toFixed(2)}%)
              </li>
            ))}
          </ul>
        ) : (
          <p>No votes yet.</p>
        )}
        <button onClick={handleBackToList}>Back to List</button>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Polling Application</h1>
      </header>
      <main>
        {content}
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
