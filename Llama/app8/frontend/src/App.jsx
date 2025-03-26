import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [threads, setThreads] = useState([]);
  const [newThreadTitle, setNewThreadTitle] = useState('');
  const [newThreadContent, setNewThreadContent] = useState('');
  const [newThreadCategory, setNewThreadCategory] = useState('');
  const [newCommentContent, setNewCommentContent] = useState('');
  const [selectedThread, setSelectedThread] = useState(null);

  useEffect(() => {
    axios.get('/api/threads')
      .then(response => {
        setThreads(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const createNewThread = () => {
    axios.post('/api/threads', {
      title: newThreadTitle,
      content: newThreadContent,
      category: newThreadCategory,
    })
      .then(response => {
        setThreads([...threads, response.data]);
        setNewThreadTitle('');
        setNewThreadContent('');
        setNewThreadCategory('');
      })
      .catch(error => {
        console.error(error);
      });
  };

  const createNewComment = () => {
    axios.post(`/api/threads/${selectedThread.id}/comments`, {
      content: newCommentContent,
    })
      .then(response => {
        // Update the comments for the selected thread
        const updatedThreads = threads.map(thread => {
          if (thread.id === selectedThread.id) {
            return { ...thread, comments: [...thread.comments, response.data] };
          }
          return thread;
        });
        setThreads(updatedThreads);
        setNewCommentContent('');
      })
      .catch(error => {
        console.error(error);
      });
  };

  const selectThread = (thread) => {
    setSelectedThread(thread);
  };

  return (
    <main>
      <h1>Forum Application</h1>
      <section>
        <h2>Create New Thread</h2>
        <input
          type="text"
          value={newThreadTitle}
          onChange={(e) => setNewThreadTitle(e.target.value)}
          placeholder="Title"
        />
        <textarea
          value={newThreadContent}
          onChange={(e) => setNewThreadContent(e.target.value)}
          placeholder="Content"
        />
        <input
          type="text"
          value={newThreadCategory}
          onChange={(e) => setNewThreadCategory(e.target.value)}
          placeholder="Category"
        />
        <button onClick={createNewThread}>Create Thread</button>
      </section>
      <section>
        <h2>Threads</h2>
        <ul>
          {threads.map(thread => (
            <li key={thread.id}>
              <h3>{thread.title}</h3>
              <p>{thread.content}</p>
              <p>Category: {thread.category}</p>
              <button onClick={() => selectThread(thread)}>View Comments</button>
            </li>
          ))}
        </ul>
      </section>
      {selectedThread && (
        <section>
          <h2>Comments for {selectedThread.title}</h2>
          <ul>
            {selectedThread.comments && selectedThread.comments.map(comment => (
              <li key={comment.id}>
                <p>{comment.content}</p>
              </li>
            ))}
          </ul>
          <input
            type="text"
            value={newCommentContent}
            onChange={(e) => setNewCommentContent(e.target.value)}
            placeholder="New Comment"
          />
          <button onClick={createNewComment}>Create Comment</button>
        </section>
      )}
    </main>
  );
}

export default App;
