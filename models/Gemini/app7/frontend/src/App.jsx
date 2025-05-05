import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileList, setFileList] = useState([]);
    const [uploadStatus, setUploadStatus] = useState('');
    const [previewUrl, setPreviewUrl] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [currentPage, setCurrentPage] = useState('upload'); // upload | list

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
        setPreviewUrl(null);
        setErrorMessage('');
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setErrorMessage('Please select a file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            setUploadStatus('Uploading...');
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setUploadStatus(data.message);
                setSelectedFile(null);
                setErrorMessage('');
                fetchFiles();  // Refresh file list
            } else {
                const errorData = await response.json();
                setUploadStatus(`Upload failed: ${errorData.error}`);
                setErrorMessage(errorData.error);
            }
        } catch (error) {
            console.error("Upload error:", error);
            setUploadStatus('Upload failed: An unexpected error occurred.');
            setErrorMessage(error.message);
        }
    };

    const fetchFiles = async () => {
        try {
            const response = await fetch('/api/files');
            if (response.ok) {
                const data = await response.json();
                setFileList(data);
            } else {
                console.error("Failed to fetch files:", response.status);
                setErrorMessage('Failed to fetch files. Please try again.');
            }
        } catch (error) {
            console.error("Fetch files error:", error);
            setErrorMessage('Failed to fetch files. An unexpected error occurred.');
        }
    };

    const handleDownload = (filename) => {
        window.location.href = `/api/download/${filename}`;
    };

    const handlePreview = async (filename) => {
        setPreviewUrl(`/api/preview/${filename}`);
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const renderUploadPage = () => (
        <div>
            <h2>File Upload</h2>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleUpload} disabled={!selectedFile}>Upload</button>
            {uploadStatus && <p>{uploadStatus}</p>}
            {errorMessage && <p className="error">{errorMessage}</p>}
            {previewUrl && (
                <div>
                    <h3>Preview</h3>
                    {previewUrl.match(/\.(jpeg|jpg|gif|png)$/) ? (
                        <img src={previewUrl} alt="Preview" style={{ maxWidth: '300px' }} />
                    ) : (
                        <a href={previewUrl} target="_blank" rel="noopener noreferrer">Preview File</a>
                    )}
                </div>
            )}
        </div>
    );

    const renderFileList = () => (
        <div>
            <h2>File List</h2>
            {errorMessage && <p className="error">{errorMessage}</p>}
            <ul>
                {fileList.map((file, index) => (
                    <li key={index}>
                        {file}
                        <button onClick={() => handleDownload(file)}>Download</button>
                        <button onClick={() => handlePreview(file)}>Preview</button>
                    </li>
                ))}
            </ul>
        </div>
    );

    return (
        <div className="app-container">
            <header>
                <h1>File Uploader</h1>
                <nav>
                    <button onClick={() => setCurrentPage('upload')}>Upload</button>
                    <button onClick={() => setCurrentPage('list')}>File List</button>
                </nav>
            </header>
            <main>
                {currentPage === 'upload' ? renderUploadPage() : renderFileList()}
            </main>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
