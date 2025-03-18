import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
    const [pages, setPages] = useState([]);
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [search, setSearch] = useState('');

    useEffect(() => {
        fetchPages();
    }, []);

    const fetchPages = async () => {
        const response = await axios.get('http://localhost:5115/pages');
        setPages(response.data);
    };

    const createPage = async () => {
        await axios.post('http://localhost:5115/pages', { title, content });
        fetchPages();
    };

    const updatePage = async (id) => {
        await axios.put(`http://localhost:5115/pages/${id}`, { title, content });
        fetchPages();
    };

    const deletePage = async (id) => {
        await axios.delete(`http://localhost:5115/pages/${id}`);
        fetchPages();
    };

    const filteredPages = pages.filter(page => page.title.includes(search));

    return (
        <Router>
            <div className="app">
                <nav>
                    <Link to="/">Home</Link>
                    <Link to="/create">Create Page</Link>
                    <Link to="/search">Search</Link>
                </nav>
                <Switch>
                    <Route path="/" exact>
                        <h1>Wiki Pages</h1>
                        <ul>
                            {filteredPages.map(page => (
                                <li key={page.id}>
                                    <h2>{page.title}</h2>
                                    <p>{page.content}</p>
                                    <button onClick={() => deletePage(page.id)}>Delete</button>
                                </li>
                            ))}
                        </ul>
                    </Route>
                    <Route path="/create">
                        <h1>Create Page</h1>
                        <input type="text" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
                        <textarea placeholder="Content" value={content} onChange={(e) => setContent(e.target.value)}></textarea>
                        <button onClick={createPage}>Create</button>
                    </Route>
                    <Route path="/search">
                        <h1>Search Pages</h1>
                        <input type="text" placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} />
                    </Route>
                </Switch>
            </div>
        </Router>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
