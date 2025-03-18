// app/frontend/src/App.jsx

import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const BASE_URL = "http://localhost:5175";

const App = () => {
  const [threads, setThreads] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("latest");
  const [newThread, setNewThread] = useState({ title: "", content: "", category: "" });
  const [selectedThread, setSelectedThread] = useState(null);

  // Fetch threads and categories
  useEffect(() => {
    fetchThreads();
    fetchCategories();
  }, [selectedCategory, searchQuery, sortBy]);

  const fetchThreads = async () => {
    const url = `${BASE_URL}/threads?category=${selectedCategory}&search=${searchQuery}&sort_by=${sortBy}`;
    const response = await fetch(url);
    const data = await response.json();
    setThreads(data);
  };

  const fetchCategories = async () => {
    const response = await fetch(`${BASE_URL}/categories`);
    const data = await response.json();
    setCategories(data);
  };

  const handleCreateThread = async () => {
    const response = await fetch(`${BASE_URL}/threads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newThread),
    });
    if (response.ok) {
      setNewThread({ title: "", content: "", category: "" });
      fetchThreads();
    }
  };

  const handleAddComment = async (threadId, content) => {
    const response = await fetch(`${BASE_URL}/threads/${threadId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (response.ok) {
      fetchThreads();
    }
  };

  return (
    <div className="App">
      <h1>Forum Application</h1>

      {/* Thread creation form */}
      <div>
        <h2>Create a New Thread</h2>
        <input
          type="text"
          placeholder="Title"
          value={newThread.title}
          onChange={(e) => setNewThread({ ...newThread, title: e.target.value })}
        />
        <textarea
          placeholder="Content"
          value={newThread.content}
          onChange={(e) => setNewThread({ ...newThread, content: e.target.value })}
        />
        <select
          value={newThread.category}
          onChange={(e) => setNewThread({ ...newThread, category: e.target.value })}
        >
          <option value="">Select Category</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
        <button onClick={handleCreateThread}>Create Thread</button>
      </div>

      {/* Thread list */}
      <div>
        <h2>Threads</h2>
        <input
          type="text"
          placeholder="Search threads..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="latest">Latest</option>
          <option value="popular">Most Popular</option>
        </select>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
        {threads.map((thread) => (
          <div key={thread.id} onClick={() => setSelectedThread(thread)}>
            <h3>{thread.title}</h3>
            <p>{thread.content}</p>
          </div>
        ))}
      </div>

      {/* Thread detail view */}
      {selectedThread && (
        <div>
          <h2>{selectedThread.title}</h2>
          <p>{selectedThread.content}</p>
          <h3>Comments</h3>
          {selectedThread.comments.map((comment) => (
            <div key={comment.id}>
              <p>{comment.content}</p>
            </div>
          ))}
          <textarea
            placeholder="Add a comment..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.target.value.trim()) {
                handleAddComment(selectedThread.id, e.target.value.trim());
                e.target.value = "";
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
