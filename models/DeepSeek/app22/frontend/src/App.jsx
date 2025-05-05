import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

const App = () => {
  // Application state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('home');
  const [languages, setLanguages] = useState([]);
  const [progress, setProgress] = useState(null);
  const [vocabulary, setVocabulary] = useState([]);
  const [grammar, setGrammar] = useState([]);
  const [pronunciation, setPronunciation] = useState([]);
  const [quizzes, setQuizzes] = useState([]);
  const [quizResult, setQuizResult] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  
  // Form states
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', password: '', email: '' });

  // Check authentication status on load
  useEffect(() => {
    checkAuth();
    fetchAvailableLanguages();
  }, []);

  // API calls
  const checkAuth = async () => {
    try {
      const response = await fetch('/api/check-auth', { credentials: 'include' });
      const data = await response.json();
      
      if (data.authenticated) {
        setIsAuthenticated(true);
        setUser(data.user);
        setSelectedLanguage(data.user.current_language);
        fetchUserProgress();
        fetchLearningContent(data.user.current_language);
      }
    } catch (error) {
      console.error('Auth check error:', error);
    }
  };

  const login = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(loginForm)
      });
      
      const data = await response.json();
      if (response.ok) {
        await checkAuth();
        setCurrentPage('dashboard');
      } else {
        alert(data.error || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed');
    }
  };

  const register = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(registerForm)
      });
      
      const data = await response.json();
      if (response.ok) {
        setCurrentPage('login');
      } else {
        alert(data.error || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('Registration failed');
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setIsAuthenticated(false);
      setUser(null);
      setCurrentPage('home');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const fetchAvailableLanguages = async () => {
    try {
      const response = await fetch('/api/languages');
      const data = await response.json();
      setLanguages(data);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const fetchUserProgress = async () => {
    try {
      const response = await fetch('/api/progress', { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setProgress(data);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const fetchLearningContent = async (language) => {
    if (!language) return;
    
    try {
      // Vocabulary
      const vocabResponse = await fetch(`/api/vocabulary/${language}`);
      const vocabData = await vocabResponse.json();
      setVocabulary(vocabData);
      
      // Grammar
      const grammarResponse = await fetch(`/api/grammar/${language}`);
      const grammarData = await grammarResponse.json();
      setGrammar(grammarData);
      
      // Pronunciation
      const pronResponse = await fetch(`/api/pronunciation/${language}`);
      const pronData = await pronResponse.json();
      setPronunciation(pronData);
      
      // Quizzes
      const quizResponse = await fetch(`/api/quizzes/${language}`);
      const quizData = await quizResponse.json();
      setQuizzes(quizData);
    } catch (error) {
      console.error('Error fetching content:', error);
    }
  };

  const changeLanguage = async (language) => {
    try {
      const response = await fetch('/api/change-language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ language })
      });
      
      if (response.ok) {
        setSelectedLanguage(language);
        if (user) {
          setUser({ ...user, current_language: language });
        }
        fetchUserProgress();
        fetchLearningContent(language);
      }
    } catch (error) {
      console.error('Error changing language:', error);
    }
  };

  const submitQuiz = async (quizId, selectedAnswer) => {
    try {
      const response = await fetch('/api/quiz/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ quiz_id: quizId, selected_answer: selectedAnswer })
      });
      
      const data = await response.json();
      setQuizResult(data);
      fetchUserProgress(); // Refresh progress
      
      return data;
    } catch (error) {
      console.error('Error submitting quiz:', error);
      return null;
    }
  };

  // Render functions for different pages
  const renderHomePage = () => (
    <div className="home-page">
      <h1>Welcome to Language Learner</h1>
      <p>Start your language learning journey today with our interactive platform!</p>
      <div className="cta-buttons">
        {!isAuthenticated ? (
          <>
            <button onClick={() => setCurrentPage('login')} className="btn btn-primary">Login</button>
            <button onClick={() => setCurrentPage('register')} className="btn btn-secondary">Register</button>
          </>
        ) : (
          <button onClick={() => setCurrentPage('dashboard')} className="btn btn-primary">Go to Dashboard</button>
        )}
      </div>
    </div>
  );

  const renderLoginPage = () => (
    <div className="auth-form">
      <h2>Login</h2>
      <form onSubmit={login}>
        <div className="form-group">
          <label>Username:</label>
          <input 
            type="text" 
            value={loginForm.username} 
            onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
            required 
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            value={loginForm.password} 
            onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
            required 
          />
        </div>
        <button type="submit" className="btn btn-primary">Login</button>
      </form>
      <p>Don't have an account? <button onClick={() => setCurrentPage('register')} className="btn-link">Register</button></p>
    </div>
  );

  const renderRegisterPage = () => (
    <div className="auth-form">
      <h2>Register</h2>
      <form onSubmit={register}>
        <div className="form-group">
          <label>Username:</label>
          <input 
            type="text" 
            value={registerForm.username} 
            onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
            required 
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input 
            type="password" 
            value={registerForm.password} 
            onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
            required 
          />
        </div>
        <div className="form-group">
          <label>Email (optional):</label>
          <input 
            type="email" 
            value={registerForm.email} 
            onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
          />
        </div>
        <button type="submit" className="btn btn-primary">Register</button>
      </form>
      <p>Already have an account? <button onClick={() => setCurrentPage('login')} className="btn-link">Login</button></p>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome, {user?.username}!</h1>
        <button onClick={logout} className="btn btn-secondary">Logout</button>
      </div>
      
      <div className="language-selector">
        <h3>Currently Learning: {selectedLanguage}</h3>
        <select 
          value={selectedLanguage}
          onChange={(e) => changeLanguage(e.target.value)}
          className="form-select"
        >
          {languages.map((lang) => (
            <option key={lang} value={lang}>{lang}</option>
          ))}
        </select>
      </div>
      
      <div className="dashboard-grid">
        {progress && (
          <div className="progress-card">
            <h3>Your Progress</h3>
            <p>Vocabulary Learned: {progress.current_progress?.vocabulary_learned || 0}</p>
            <p>Grammar Learned: {progress.current_progress?.grammar_learned || 0}</p>
            <p>Quizzes Completed: {progress.current_progress?.quizzes_completed || 0}</p>
          </div>
        )}
        
        <div className="menu-card">
          <h3>Menu</h3>
          <button onClick={() => setCurrentPage('vocabulary')} className="btn btn-block">Vocabulary</button>
          <button onClick={() => setCurrentPage('grammar')} className="btn btn-block">Grammar</button>
          <button onClick={() => setCurrentPage('pronunciation')} className="btn btn-block">Pronunciation</button>
          <button onClick={() => setCurrentPage('quizzes')} className="btn btn-block">Quizzes</button>
        </div>
      </div>
    </div>
  );

  const renderVocabularyPage = () => (
    <div className="content-page">
      <h2>Vocabulary Lessons ({selectedLanguage})</h2>
      <button onClick={() => setCurrentPage('dashboard')} className="btn btn-back">← Back to Dashboard</button>
      
      {vocabulary.length === 0 ? (
        <p>No vocabulary lessons available yet.</p>
      ) : (
        <div className="vocabulary-list">
          {vocabulary.map((item) => (
            <div key={item.id} className="vocabulary-item">
              <h3>{item.word} - {item.translation}</h3>
              <p>Category: {item.category}</p>
              <p>Example: <i>{item.example}</i></p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderGrammarPage = () => (
    <div className="content-page">
      <h2>Grammar Exercises ({selectedLanguage})</h2>
      <button onClick={() => setCurrentPage('dashboard')} className="btn btn-back">← Back to Dashboard</button>
      
      {grammar.length === 0 ? (
        <p>No grammar exercises available yet.</p>
      ) : (
        <div className="grammar-list">
          {grammar.map((item) => (
            <div key={item.id} className="grammar-item">
              <h3>{item.topic}</h3>
              <div className="grammar-explanation">
                <p>{item.explanation}</p>
                <p>Example: <i>{item.example}</i></p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderPronunciationPage = () => (
    <div className="content-page">
      <h2>Pronunciation Guides ({selectedLanguage})</h2>
      <button onClick={() => setCurrentPage('dashboard')} className="btn btn-back">← Back to Dashboard</button>
      
      {pronunciation.length === 0 ? (
        <p>No pronunciation guides available yet.</p>
      ) : (
        <div className="pronunciation-list">
          {pronunciation.map((item) => (
            <div key={item.id} className="pronunciation-item">
              <h3>Sound: {item.sound}</h3>
              <p>{item.description}</p>
              {item.audio_file && (
                <audio controls src={`/audio/${item.audio_file}`}>
                  Your browser does not support the audio element.
                </audio>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderQuizzesPage = () => (
    <div className="content-page">
      <h2>Quizzes ({selectedLanguage})</h2>
      <button onClick={() => setCurrentPage('dashboard')} className="btn btn-back">← Back to Dashboard</button>
      
      {quizzes.length === 0 ? (
        <p>No quizzes available yet.</p>
      ) : (
        <div className="quiz-list">
          {quizzes.map((quiz) => (
            <QuizComponent 
              key={quiz.id} 
              quiz={quiz} 
              onSubmit={submitQuiz} 
              result={quizResult?.quiz_id === quiz.id ? quizResult : null}
            />
          ))}
        </div>
      )}
    </div>
  );

  const QuizComponent = ({ quiz, onSubmit, result }) => {
    const [selectedOption, setSelectedOption] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);
    
    const handleSubmit = () => {
      if (selectedOption === null) return;
      onSubmit(quiz.id, selectedOption);
      setIsSubmitted(true);
    };
    
    const resetQuiz = () => {
      setSelectedOption(null);
      setIsSubmitted(false);
    };
    
    return (
      <div className={`quiz-item ${isSubmitted ? 'submitted' : ''}`}>
        <h3>{quiz.question}</h3>
        <div className="quiz-options">
          {quiz.options.map((option, idx) => (
            <label key={idx} className="quiz-option">
              <input
                type="radio"
                name={`quiz-${quiz.id}`}
                value={option}
                checked={selectedOption === option}
                onChange={() => setSelectedOption(option)}
                disabled={isSubmitted}
              />
              {option}
            </label>
          ))}
        </div>
        
        {isSubmitted ? (
          <>
            <div className={`quiz-feedback ${result.is_correct ? 'correct' : 'incorrect'}`}>
              {result.is_correct ? 'Correct!' : 'Incorrect!'}
              {!result.is_correct && <p>The correct answer is: {result.correct_answer}</p>}
            </div>
            <button onClick={resetQuiz} className="btn btn-secondary">Try Again</button>
          </>
        ) : (
          <button 
            onClick={handleSubmit} 
            className="btn btn-primary"
            disabled={selectedOption === null}
          >
            Submit
          </button>
        )}
      </div>
    );
  };

  // Main routing logic
  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'login':
        return renderLoginPage();
      case 'register':
        return renderRegisterPage();
      case 'dashboard':
        return renderDashboard();
      case 'vocabulary':
        return renderVocabularyPage();
      case 'grammar':
        return renderGrammarPage();
      case 'pronunciation':
        return renderPronunciationPage();
      case 'quizzes':
        return renderQuizzesPage();
      default:
        return renderHomePage();
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 onClick={() => setCurrentPage('home')} className="app-title">Language Learner</h1>
        {isAuthenticated && (
          <nav className="app-nav">
            <button onClick={() => setCurrentPage('dashboard')} className="btn-link">Dashboard</button>
          </nav>
        )}
      </header>
      
      <main className="app-main">
        {renderCurrentPage()}
      </main>
      
      <footer className="app-footer">
        <p>© 2023 Language Learner</p>
      </footer>
    </div>
  );
};

// Mount the app
const root = createRoot(document.getElementById('root'));
root.render(<App />);
