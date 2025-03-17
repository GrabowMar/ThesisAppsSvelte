import React, { useState, useEffect } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";

function App() {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("");
  const [archived, setArchived] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    axios.get("http://localhost:5000/notes")
      .then(response => {
        setNotes(response.data.notes);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleCreateNote = (event) => {
    event.preventDefault();
    axios.post("http://localhost:5000/notes", {
      title,
      content,
      category,
    })
      .then(response => {
        setNotes([...notes, response.data]);
        setTitle("");
        setContent("");
        setCategory("");
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleUpdateNote = (id) => {
    axios.put(`http://localhost:5000/notes/${id}`, {
      title,
      content,
      category,
    })
      .then(response => {
        setNotes(notes.map(note => note.id === id ? response.data : note));
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleDeleteNote = (id) => {
    axios.delete(`http://localhost:5000/notes/${id}`)
      .then(response => {
        setNotes(notes.filter(note => note.id !== id));
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleSearchNotes = (event) => {
    event.preventDefault();
    axios.get(`http://localhost:5000/notes/search?query=${query}`)
      .then(response => {
        setNotes(response.data.notes);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleArchiveNote = (id) => {
    axios.put(`http://localhost:5000/notes/archive`, {
      id,
    })
      .then(response => {
        setNotes(notes.map(note => note.id === id ? { ...note, archived: true } : note));
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleUnarchiveNote = (id) => {
    axios.put(`http://localhost:5000/notes/unarchive`, {
      id,
    })
      .then(response => {
        setNotes(notes.map(note => note.id === id ? { ...note, archived: false } : note));
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div className="container">
      <h1>Notes App</h1>
      <form onSubmit={handleCreateNote}>
        <div className="form-group">
          <label>Title:</label>
          <input type="text" value={title} onChange={(event) => setTitle(event.target.value)} />
        </div>
        <div className="form-group">
          <label>Content:</label>
          <textarea value={content} onChange={(event) => setContent(event.target.value)} />
        </div>
        <div className="form-group">
          <label>Category:</label>
          <input type="text" value={category} onChange={(event) => setCategory(event.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary">Create Note</button>
      </form>
      <h2>Notes:</h2>
      <ul>
        {notes.map(note => (
          <li key={note.id}>
            <h3>{note.title}</h3>
            <p>{note.content}</p>
            <p>Category: {note.category}</p>
            <p>Archived: {note.archived ? "Yes" : "No"}</p>
            <button onClick={() => handleUpdateNote(note.id)} className="btn btn-primary">Update Note</button>
            <button onClick={() => handleDeleteNote(note.id)} className="btn btn-danger">Delete Note</button>
            <button onClick={() => handleArchiveNote(note.id)} className="btn btn-secondary">Archive Note</button>
            <button onClick={() => handleUnarchiveNote(note.id)} className="btn btn-secondary">Unarchive Note</button>
          </li>
        ))}
      </ul>
      <form onSubmit={handleSearchNotes}>
        <div className="form-group">
          <label>Search:</label>
          <input type="text" value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary">Search Notes</button>
      </form>
    </div>
  );
}

export default App;
