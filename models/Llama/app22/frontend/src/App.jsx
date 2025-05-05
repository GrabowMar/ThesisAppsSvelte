import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [token, setToken] = useState(null);
  const [vocabulary, setVocabulary] = useState([]);
  const [grammarExercises, setGrammarExercises] = useState([]);
  const [progress, setProgress] = useState({});
  const [quizAnswers, setQuizAnswers] = useState([]);
  const [score, setScore] = useState(null);

  useEffect(() => {
    fetch('/api/vocabulary')
      .then(response => response.json())
      .then(data => setVocabulary(data));
    fetch('/api/grammar-exercises')
      .then(response => response.json())
      .then(data => setGrammarExercises(data));
  }, []);

  const handleLogin = (event) => {
    event.preventDefault();
    const username = event.target.username.value;
    const password = event.target.password.value;
    fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.token) {
          setToken(data.token);
        } else {
          alert('Invalid credentials');
        }
      });
  };

  const handleProgressUpdate = (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target));
    fetch('/api/progress', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token,
      },
      body: JSON.stringify(data),
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleQuizSubmit = (event) => {
    event.preventDefault();
    fetch('/api/quiz', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token,
      },
      body: JSON.stringify({ answers: quizAnswers }),
    })
      .then(response => response.json())
      .then(data => setScore(data.score));
  };

  return (
    <div>
      <h1>Language Learning App</h1>
      {token ? (
        <div>
          <h2>Vocabulary</h2>
          <ul>
            {vocabulary.map((item) => (
              <li key={item.id}>
                {item.word} ({item.translation})
              </li>
            ))}
          </ul>
          <h2>Grammar Exercises</h2>
          <ul>
            {grammarExercises.map((exercise) => (
              <li key={exercise.id}>
                {exercise.question}
                <ul>
                  {exercise.options.map((option, index) => (
                    <li key={index}>
                      <input
                        type="radio"
                        name={`exercise-${exercise.id}`}
                        value={index}
                        onChange={(event) =>
                          setQuizAnswers((prevAnswers) => [
                            ...prevAnswers,
                            { question: exercise.id, answer: event.target.value },
                          ])
                        }
                      />
                      {option}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
          <form onSubmit={handleQuizSubmit}>
            <button type="submit">Submit Quiz</button>
          </form>
          {score !== null && <p>Your score: {score}</p>}
          <h2>Progress</h2>
          <form onSubmit={handleProgressUpdate}>
            <input type="text" name="progress" placeholder="Update progress" />
            <button type="submit">Update</button>
          </form>
        </div>
      ) : (
        <form onSubmit={handleLogin}>
          <input type="text" name="username" placeholder="Username" />
          <input type="password" name="password" placeholder="Password" />
          <button type="submit">Login</button>
        </form>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
