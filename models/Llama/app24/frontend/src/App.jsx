import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('register');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userId, setUserId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [connections, setConnections] = useState([]);
  const [jobPostings, setJobPostings] = useState([]);
  const [messages, setMessages] = useState([]);
  const [endorsements, setEndorsements] = useState([]);
  const [achievements, setAchievements] = useState([]);

  useEffect(() => {
    // Initialize user data if available
  }, []);

  const handleRegister = async () => {
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setCurrentPage('login');
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error registering user:', error);
    }
  };

  const handleCreateProfile = async () => {
    try {
      const response = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, name: 'John Doe', headline: 'Software Engineer', bio: 'Experienced software engineer' }),
      });
      const data = await response.json();
      if (response.ok) {
        setProfile({ name: 'John Doe', headline: 'Software Engineer', bio: 'Experienced software engineer' });
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error creating profile:', error);
    }
  };

  const handleCreateConnection = async () => {
    try {
      const response = await fetch('/api/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user1_id: userId, user2_id: 2 }),
      });
      const data = await response.json();
      if (response.ok) {
        setConnections([...connections, { user_id: 2, name: 'Jane Doe' }]);
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error creating connection:', error);
    }
  };

  const handleCreateJobPosting = async () => {
    try {
      const response = await fetch('/api/job_postings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, title: 'Software Engineer', description: 'Job description' }),
      });
      const data = await response.json();
      if (response.ok) {
        setJobPostings([...jobPostings, { title: 'Software Engineer', description: 'Job description' }]);
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error creating job posting:', error);
    }
  };

  const handleSendMessage = async () => {
    try {
      const response = await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender_id: userId, receiver_id: 2, content: 'Hello!' }),
      });
      const data = await response.json();
      if (response.ok) {
        setMessages([...messages, { sender_id: userId, receiver_id: 2, content: 'Hello!' }]);
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleCreateEndorsement = async () => {
    try {
      const response = await fetch('/api/endorsements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endorser_id: userId, endorsee_id: 2, skill: 'Programming' }),
      });
      const data = await response.json();
      if (response.ok) {
        setEndorsements([...endorsements, { endorser_id: userId, endorsee_id: 2, skill: 'Programming' }]);
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error creating endorsement:', error);
    }
  };

  const handleCreateAchievement = async () => {
    try {
      const response = await fetch('/api/achievements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, title: 'Achievement', description: 'Description' }),
      });
      const data = await response.json();
      if (response.ok) {
        setAchievements([...achievements, { title: 'Achievement', description: 'Description' }]);
      } else {
        console.error(data.message);
      }
    } catch (error) {
      console.error('Error creating achievement:', error);
    }
  };

  return (
    <div className="app">
      {currentPage === 'register' && (
        <div>
          <h1>Register</h1>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <button onClick={handleRegister}>Register</button>
        </div>
      )}
      {currentPage === 'profile' && (
        <div>
          <h1>Profile</h1>
          {profile && (
            <div>
              <p>Name: {profile.name}</p>
              <p>Headline: {profile.headline}</p>
              <p>Bio: {profile.bio}</p>
            </div>
          )}
          <button onClick={handleCreateProfile}>Create Profile</button>
        </div>
      )}
      {currentPage === 'connections' && (
        <div>
          <h1>Connections</h1>
          <ul>
            {connections.map((connection) => (
              <li key={connection.user_id}>{connection.name}</li>
            ))}
          </ul>
          <button onClick={handleCreateConnection}>Create Connection</button>
        </div>
      )}
      {currentPage === 'job_postings' && (
        <div>
          <h1>Job Postings</h1>
          <ul>
            {jobPostings.map((jobPosting) => (
              <li key={jobPosting.title}>{jobPosting.title}</li>
            ))}
          </ul>
          <button onClick={handleCreateJobPosting}>Create Job Posting</button>
        </div>
      )}
      {currentPage === 'messages' && (
        <div>
          <h1>Messages</h1>
          <ul>
            {messages.map((message) => (
              <li key={message.content}>{message.content}</li>
            ))}
          </ul>
          <button onClick={handleSendMessage}>Send Message</button>
        </div>
      )}
      {currentPage === 'endorsements' && (
        <div>
          <h1>Endorsements</h1>
          <ul>
            {endorsements.map((endorsement) => (
              <li key={endorsement.skill}>{endorsement.skill}</li>
            ))}
          </ul>
          <button onClick={handleCreateEndorsement}>Create Endorsement</button>
        </div>
      )}
      {currentPage === 'achievements' && (
        <div>
          <h1>Achievements</h1>
          <ul>
            {achievements.map((achievement) => (
              <li key={achievement.title}>{achievement.title}</li>
            ))}
          </ul>
          <button onClick={handleCreateAchievement}>Create Achievement</button>
        </div>
      )}
      <nav>
        <button onClick={() => setCurrentPage('register')}>Register</button>
        <button onClick={() => setCurrentPage('profile')}>Profile</button>
        <button onClick={() => setCurrentPage('connections')}>Connections</button>
        <button onClick={() => setCurrentPage('job_postings')}>Job Postings</button>
        <button onClick={() => setCurrentPage('messages')}>Messages</button>
        <button onClick={() => setCurrentPage('endorsements')}>Endorsements</button>
        <button onClick={() => setCurrentPage('achievements')}>Achievements</button>
      </nav>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
