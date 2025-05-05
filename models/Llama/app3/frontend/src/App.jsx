import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [feedback, setFeedback] = useState([]);
  const [success, setSuccess] = useState(false);

  const handleFormSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/feedback', {
      name,
      email,
      message
    })
    .then((response) => {
      setSuccess(true);
      getName();
      setEmail('');
      setMessage('');
    })
    .catch((error) => {
      console.log(error);
    });
  };

  const getName = () => {
    axios.get('/api/feedback')
    .then((response) => {
      setFeedback(response.data.feedback);
    })
    .catch((error) => {
      console.log(error);
    });
  };

  return (
    <div>
      <h1>Feedback Form</h1>
      <form onSubmit={handleFormSubmit}>
        <label>Name:</label>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
        <br />
        <label>Email:</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <br />
        <label>Message:</label>
        <textarea value={message} onChange={(e) => setMessage(e.target.value)} />
        <br />
        <button type="submit">Submit</button>
      </form>
      {success && <p>Feedback submitted successfully!</p>}
      <h2>Feedback:</h2>
      <ul>
        {feedback.map((item) => (
          <li key={item.id}>{item.name} - {item.email} - {item.message}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
