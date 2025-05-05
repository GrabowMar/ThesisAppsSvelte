import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';
const App = () => {
  const [polls, setPolls] = useState([]);
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState('');
  const [endsAt, setEndsAt] = useState('');

  useEffect(() => {
    fetch('/api/polls')
      .then(response => response.json())
      .then(data => setPolls(data.polls));
  }, []);

  const createPoll = () => {
    fetch('/api/polls', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question,
        options: options.split(','),
        ends_at: endsAt
      })
    })
    .then(response => response.json())
    .then(data => {
      setPolls({ ...polls, [data.poll_id]: data });
      setQuestion('');
      setOptions('');
      setEndsAt('');
    });
  };

  const vote = (pollId, option) => {
    fetch(`/api/polls/${pollId}/vote`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ option })
    })
    .then(response => response.json())
    .then(data => console.log(data));
  };

  const getResults = (pollId) => {
    fetch(`/api/polls/${pollId}/results`)
      .then(response => response.json())
      .then(data => console.log(data));
  };

  return (
    <Router>
      <div>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/create">Create Poll</Link>
        </nav>
        <Routes>
          <Route path="/" element={
            <div>
              <h1>Polls</h1>
              {Object.keys(polls).map(id => (
                <div key={id}>
                  <h2>{polls[id].question}</h2>
                  <button onClick={() => vote(id, polls[id].options[0])}>Vote</button>
                  <button onClick={() => getResults(id)}>Results</button>
                </div>
              ))}
            </div>
          } />
          <Route path="/create" element={
            <div>
              <h1>Create Poll</h1>
              <input type="text" placeholder="Question" value={question} onChange={e => setQuestion(e.target.value)} />
              <input type="text" placeholder="Options (comma separated)" value={options} onChange={e => setOptions(e.target.value)} />
              <input type="datetime-local" value={endsAt} onChange={e => setEndsAt(e.target.value)} />
              <button onClick={createPoll}>Create</button>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
};
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
