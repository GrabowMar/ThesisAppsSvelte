import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

const App = () => {
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    // Simulate fetching or creating the message from your backend
    const backendPort = 'xxxx'; // Replace 'xxxx' with the actual backend port number if available
    const backendMessage = `hello from backend on port: ${backendPort}`;
    setMessage(backendMessage);
  }, []);

  return (
    <main>
      <h1>{message}</h1>
    </main>
  );
};

// Mount the App component to the DOM element with id 'root'
const container = document.getElementById('root');
if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(<App />);
}

export default App;
