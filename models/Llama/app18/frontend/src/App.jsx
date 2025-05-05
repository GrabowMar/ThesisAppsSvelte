// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

// 2. State Management
const [pages, setPages] = useState([]);
const [page, setPage] = useState({});
const [version, setVersion] = useState({});
const [searchQuery, setSearchQuery] = useState('');
const [searchResults, setSearchResults] = useState([]);

// 3. Lifecycle Functions
useEffect(() => {
    axios.get('/api/pages')
        .then(response => {
            setPages(response.data);
        })
        .catch(error => {
            console.error(error);
        });
}, []);

// 4. Event Handlers
const handlePageCreate = () => {
    axios.post('/api/pages', {
        title: 'New Page',
        content: 'This is a new page.'
    })
        .then(response => {
            setPages([...pages, response.data]);
        })
        .catch(error => {
            console.error(error);
        });
};

const handlePageUpdate = (id) => {
    axios.put(`/api/pages/${id}`, {
        title: page.title,
        content: page.content
    })
        .then(response => {
            setPages(pages.map(p => p.id === id ? response.data : p));
        })
        .catch(error => {
            console.error(error);
        });
};

const handlePageDelete = (id) => {
    axios.delete(`/api/pages/${id}`)
        .then(() => {
            setPages(pages.filter(p => p.id !== id));
        })
        .catch(error => {
            console.error(error);
        });
};

const handleVersionCreate = (id) => {
    axios.post(`/api/pages/${id}/versions`, {
        content: 'This is a new version.'
    })
        .then(response => {
            console.log(response.data);
        })
        .catch(error => {
            console.error(error);
        });
};

const handleSearch = () => {
    axios.get('/api/search', {
        params: {
            query: searchQuery
        }
    })
        .then(response => {
            setSearchResults(response.data);
        })
        .catch(error => {
            console.error(error);
        });
};

// 5. API Calls
const getPage = (id) => {
    axios.get(`/api/pages/${id}`)
        .then(response => {
            setPage(response.data);
        })
        .catch(error => {
            console.error(error);
        });
};

const getVersions = (id) => {
    axios.get(`/api/versions`)
        .then(response => {
            setVersion(response.data.find(v => v.page_id === id));
        })
        .catch(error => {
            console.error(error);
        });
};

// 6. UI Components
const PageList = () => {
    return (
        <ul>
            {pages.map(page => (
                <li key={page.id}>
                    <h2>{page.title}</h2>
                    <p>{page.content}</p>
                    <button onClick={() => handlePageUpdate(page.id)}>Update</button>
                    <button onClick={() => handlePageDelete(page.id)}>Delete</button>
                    <button onClick={() => handleVersionCreate(page.id)}>Create Version</button>
                </li>
            ))}
        </ul>
    );
};

const SearchBar = () => {
    return (
        <div>
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            <button onClick={handleSearch}>Search</button>
            <ul>
                {searchResults.map(page => (
                    <li key={page.id}>
                        <h2>{page.title}</h2>
                        <p>{page.content}</p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

const App = () => {
    return (
        <div>
            <h1>Wiki App</h1>
            <button onClick={handlePageCreate}>Create Page</button>
            <PageList />
            <SearchBar />
        </div>
    );
};

// 7. Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
