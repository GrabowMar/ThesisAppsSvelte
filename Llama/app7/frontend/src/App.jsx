import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

function App() {
    const [files, setFiles] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');

    useEffect(() => {
        axios.get('http://localhost:5013/files')
            .then(response => {
                setFiles(response.data.files);
            })
            .catch(error => {
                console.error(error);
            });
    }, []);

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleFileUpload = () => {
        const formData = new FormData();
        formData.append('file', selectedFile);
        axios.post('http://localhost:5013/upload', formData)
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleFileDownload = (filename) => {
        axios.get(`http://localhost:5013/download/${filename}`, { responseType: 'blob' })
            .then(response => {
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleFilePreview = (filename) => {
        axios.get(`http://localhost:5013/preview/${filename}`)
            .then(response => {
                setFileContent(response.data.content);
            })
            .catch(error => {
                console.error(error);
            });
    };

    return (
        <div>
            <h1>File Uploader</h1>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleFileUpload}>Upload File</button>
            <ul>
                {files.map((file, index) => (
                    <li key={index}>
                        {file}
                        <button onClick={() => handleFileDownload(file)}>Download</button>
                        <button onClick={() => handleFilePreview(file)}>Preview</button>
                    </li>
                ))}
            </ul>
            {fileContent && (
                <div>
                    <h2>File Content:</h2>
                    <pre>{fileContent}</pre>
                </div>
            )}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
