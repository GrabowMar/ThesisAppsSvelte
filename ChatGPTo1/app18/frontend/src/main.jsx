import React, { useState, useEffect } from 'react';
import './App.css'; // Import external CSS for styling

const App = () => {
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        const response = await fetch('http://localhost:{backend_port}/');
        const data = await response.json();
        setMessage(data.message);
      } catch (error) {
        setMessage('Error connecting to {model_name} backend');
      }
    };

    fetchMessage();
  }, []); // Empty dependency array ensures this runs only once on mount

  return (
    <main>
      <h1>{'{model_name} App'}</h1>
      <p className="message">{message}</p>
    </main>
  );
};

export default App;
