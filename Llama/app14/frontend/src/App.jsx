// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

function App() {
    const [files, setFiles] = useState([]);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [fileType, setFileType] = useState('');
    const [quota, setQuota] = useState(0);
    const [usedQuota, setUsedQuota] = useState(0);

    useEffect(() => {
        axios.get('http://localhost:5027/files/')
            .then(response => {
                setFiles(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    }, []);

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        axios.post('http://localhost:5027/upload', formData)
            .then(response => {
                setUploadedFile(file);
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleFileTypeChange = (event) => {
        setFileType(event.target.value);
        axios.get(`http://localhost:5027/files/${event.target.value}`)
            .then(response => {
                setFiles(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleQuotaCheck = () => {
        axios.get('http://localhost:5027/quota')
            .then(response => {
                setQuota(response.data.quota);
                setUsedQuota(response.data.used);
            })
            .catch(error => {
                console.error(error);
            });
    };

    return (
        <div>
            <h1>File Storage Application</h1>
            <input type="file" onChange={handleFileUpload} />
            <select value={fileType} onChange={handleFileTypeChange}>
                <option value="">All Files</option>
                <option value="image/jpeg">Images</option>
                <option value="video/mp4">Videos</option>
                <option value="application/pdf">PDFs</option>
            </select>
            <button onClick={handleQuotaCheck}>Check Quota</button>
            <p>Quota: {quota} bytes</p>
            <p>Used Quota: {usedQuota} bytes</p>
            <ul>
                {files.map((file, index) => (
                    <li key={index}>{file.filename}</li>
                ))}
            </ul>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
