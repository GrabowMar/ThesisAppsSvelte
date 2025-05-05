import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import axios from 'axios';

const App = () => {
    const [files, setFiles] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [quota, setQuota] = useState({ used: 0, total: 0 });
    const [currentPage, setCurrentPage] = useState('home'); // Multipage routing

    useEffect(() => {
        fetchFiles();
        fetchQuota();
    }, []);

    const fetchFiles = async () => {
        try {
            const response = await axios.get('/api/files');
            setFiles(response.data);
        } catch (error) {
            console.error('Error fetching files:', error);
        }
    };

    const fetchQuota = async () => {
        try {
            const response = await axios.get('/api/quota');
            setQuota(response.data);
        } catch (error) {
            console.error('Error fetching quota:', error);
        }
    };

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setUploadStatus('Please select a file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await axios.post('/api/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setUploadStatus(response.data.message);
            fetchFiles();  // Refresh file list
            fetchQuota(); // Refresh quota
        } catch (error) {
            console.error('Error uploading file:', error);
            setUploadStatus(error.response?.data?.message || 'Upload failed.');
        }
    };

    const handleDownload = (filename) => {
        window.location.href = `/api/download/${filename}`; // Simple download
    };

    const handleDelete = async (filename) => {
        try {
            await axios.delete(`/api/delete/${filename}`);
            fetchFiles(); // Refresh file list
            fetchQuota(); // Refresh quota
        } catch (error) {
            console.error('Error deleting file:', error);
            alert('Error deleting file.');
        }
    };

    const navigateTo = (page) => {
        setCurrentPage(page);
    };

    // Conditional rendering for multipage routing
    let content;
    if (currentPage === 'home') {
        content = (
            <div>
                <h2>File Storage</h2>
                <div className="upload-section">
                    <input type="file" onChange={handleFileChange} />
                    <button onClick={handleUpload}>Upload</button>
                    {uploadStatus && <p>{uploadStatus}</p>}
                </div>

                <h3>Files:</h3>
                <ul className="file-list">
                    {files.map((file) => (
                        <li key={file.filename} className="file-item">
                            <span>{file.filename} ({formatBytes(file.size)})</span>
                            <button onClick={() => handleDownload(file.filename)}>Download</button>
                            <button onClick={() => handleDelete(file.filename)}>Delete</button>
                        </li>
                    ))}
                </ul>
                <p>Storage Used: {formatBytes(quota.used)} / {formatBytes(quota.total)}</p>
            </div>
        );
    } else if (currentPage === 'about') {
        content = (
            <div>
                <h2>About</h2>
                <p>This is a simple file storage application built with Flask and React.</p>
                <button onClick={() => navigateTo('home')}>Back to Home</button>
            </div>
        );
    } else {
        content = <div>Page not found.</div>;
    }

    // Helper function to format bytes into human-readable format
    function formatBytes(bytes, decimals = 2) {
        if (!+bytes) return '0 Bytes'

        const k = 1024
        const dm = decimals < 0 ? 0 : decimals
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

        const i = Math.floor(Math.log(bytes) / Math.log(k))

        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
    }

    return (
        <div className="container">
            <nav>
                <button onClick={() => navigateTo('home')}>Home</button>
                <button onClick={() => navigateTo('about')}>About</button>
            </nav>
            {content}
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
