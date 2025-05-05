import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useParams } from 'react-router-dom';
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip);

const HomePage = () => {
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/polls')
      .then(res => setPolls(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="container">
      <h1>Latest Polls</h1>
      <Link to="/create" className="btn">Create New Poll</Link>
      
      {loading ? <p>Loading...</p> : (
        <div className="poll-grid">
          {polls.map(poll => (
            <div key={poll.id} className="poll-card">
              <h3>{poll.question}</h3>
              <div className="poll-meta">
                <span className={`status ${poll.is_active ? 'active' : 'ended'}`}>
                  {poll.is_active ? 'Active' : 'Ended'}
                </span>
                <span>{Math.floor(poll.time_left / 3600)}h remaining</span>
              </div>
              <Link to={`/poll/${poll.id}`} className="btn">View Poll</Link>
              <Link to={`/results/${poll.id}`} className="btn">Results</Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const CreatePoll = () => {
  const [options, setOptions] = useState(['', '']);
  const [formData, setFormData] = useState({
    question: '',
    creator: '',
    duration: '24'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/polls', {
      ...formData,
      options: options.filter(opt => opt.trim())
    })
      .then(() => window.location = '/')
      .catch(console.error);
  };

  return (
    <div className="container">
      <h1>Create New Poll</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Question:
          <input 
            type="text" 
            value={formData.question}
            onChange={e => setFormData({...formData, question: e.target.value})}
            required 
          />
        </label>
        
        <label>
          Creator Name:
          <input 
            type="text" 
            value={formData.creator}
            onChange={e => setFormData({...formData, creator: e.target.value})}
            required 
          />
        </label>
        
        <label>
          Duration (hours):
          <input
            type="number"
            value={formData.duration}
            onChange={e => setFormData({...formData, duration: e.target.value})}
            min="1"
          />
        </label>

        <div className="options">
          <h3>Options</h3>
          {options.map((opt, i) => (
            <input
              key={i}
              type="text"
              value={opt}
              onChange={e => {
                const newOptions = [...options];
                newOptions[i] = e.target.value;
                setOptions(newOptions);
              }}
              placeholder={`Option ${i + 1}`}
            />
          ))}
        </div>
        <button type="button" onClick={() => setOptions([...options, ''])}>
          Add Option
        </button>
        
        <button type="submit">Create Poll</button>
      </form>
    </div>
  );
};

const PollPage = () => {
  const { id } = useParams();
  const [poll, setPoll] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    axios.get(`/api/polls/${id}`).then(res => setPoll(res.data));
  }, [id]);

  const handleVote = () => {
    if (!poll.is_active) return;
    axios.post(`/api/polls/${id}/vote`, { option: selectedOption })
      .then(() => setSubmitted(true))
      .catch(alert);
  };

  if (!poll) return <div>Loading...</div>;

  return (
    <div className="container poll-view">
      <h1>{poll.question}</h1>
      <div className={`status ${poll.is_active ? 'active' : 'ended'}`}>
        {poll.is_active ? `Closes in ${Math.floor(poll.time_left / 3600)}h` : 'Poll Ended'}
      </div>
      
      {poll.is_active && !submitted ? (
        <div className="options">
          {poll.options.map((opt, i) => (
            <button
              key={i}
              className={selectedOption === i ? 'selected' : ''}
              onClick={() => setSelectedOption(i)}
            >
              {opt.text}
            </button>
          ))}
          <button onClick={handleVote} disabled={selectedOption === null}>
            Submit Vote
          </button>
        </div>
      ) : (
        <p>Thanks for voting! <Link to={`/results/${id}`}>View results</Link></p>
      )}
    </div>
  );
};

const ResultsPage = () => {
  const { id } = useParams();
  const [poll, setPoll] = useState(null);

  useEffect(() => {
    axios.get(`/api/polls/${id}`).then(res => setPoll(res.data));
  }, [id]);

  if (!poll) return <div>Loading...</div>;

  const chartData = {
    labels: poll.options.map(opt => opt.text),
    datasets: [{
      label: 'Votes',
      data: poll.options.map(opt => opt.votes),
      backgroundColor: 'rgba(54, 162, 235, 0.5)'
    }]
  };

  return (
    <div className="container">
      <h1>{poll.question}</h1>
      <div className="analytics">
        <div className="chart-container">
          <Bar data={chartData} options={{ responsive: true }} />
        </div>
        <div className="stats">
          <p>Total votes: {poll.options.reduce((sum, opt) => sum + opt.votes, 0)}</p>
          <p>Created by: {poll.creator}</p>
          <p>{poll.is_active ? 'Active' : 'Ended'}</p>
        </div>
      </div>
      <Link to="/" className="btn">Back to Home</Link>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/" className="brand">Voting App</Link>
        <div>
          <Link to="/create">Create Poll</Link>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/create" element={<CreatePoll />} />
        <Route path="/poll/:id" element={<PollPage />} />
        <Route path="/results/:id" element={<ResultsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
