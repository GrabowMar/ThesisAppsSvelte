// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// 2. State Management

function App() {
    const [currentPage, setCurrentPage] = useState('gallery'); // Initial page
    const [images, setImages] = useState({});
    const [galleries, setGalleries] = useState([]);
    const [selectedGallery, setSelectedGallery] = useState('default');
    const [selectedImage, setSelectedImage] = useState(null);
    const [uploadMessage, setUploadMessage] = useState('');

    // 3. Lifecycle Functions
    useEffect(() => {
        fetchImages();
        fetchGalleries();
    }, []);

    const fetchImages = async () => {
        try {
            const response = await fetch('/api/images');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setImages(data);
        } catch (error) {
            console.error("Could not fetch images:", error);
            setUploadMessage("Error fetching images. Please try again.");
        }
    };

    const fetchGalleries = async () => {
        try {
            const response = await fetch('/api/galleries');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setGalleries(data);
        } catch (error) {
            console.error("Could not fetch galleries:", error);
            setUploadMessage("Error fetching galleries. Please try again.");
        }
    };


    // 4. Event Handlers
    const handleImageUpload = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setUploadMessage(data.message);
                fetchImages(); // Refresh image list
                fetchGalleries(); // Refresh galleries
                event.target.reset(); // Clear form
            } else {
                const errorData = await response.json();
                setUploadMessage(errorData.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setUploadMessage('Upload failed');
        }
    };

    const handleGalleryChange = (event) => {
        setSelectedGallery(event.target.value);
    };

    const handleImageClick = (filename) => {
        setSelectedImage(filename);
    };

    const handleCloseImageDetails = () => {
        setSelectedImage(null);
    };

    const goToPage = (pageName) => {
        setCurrentPage(pageName);
    }

    // 5. API Calls (already covered in useEffect and event handlers)

    // Helper function to get images in the selected gallery
    const getImagesInSelectedGallery = () => {
        return Object.keys(images).filter(filename => images[filename].gallery === selectedGallery);
    };

    // Render Functions for different pages
    const renderGalleryPage = () => (
        <div>
            <h2>Gallery</h2>
            <div className="gallery-controls">
                <select value={selectedGallery} onChange={handleGalleryChange}>
                    <option value="default">Default Gallery</option>
                    {galleries.map(gallery => (
                        <option key={gallery} value={gallery}>{gallery}</option>
                    ))}
                </select>
            </div>

            <div className="image-grid">
                {getImagesInSelectedGallery().map(filename => (
                    <div key={filename} className="image-item" onClick={() => handleImageClick(filename)}>
                        <img src={`/api/images/${filename}`} alt={images[filename].title} />
                        <p>{images[filename].title}</p>
                    </div>
                ))}
            </div>
            {selectedImage && (
                <div className="image-details-overlay">
                    <div className="image-details">
                        <button className="close-button" onClick={handleCloseImageDetails}>X</button>
                        <h3>{images[selectedImage].title}</h3>
                        <p>{images[selectedImage].description}</p>
                        <img src={`/api/images/${selectedImage}`} alt={images[selectedImage].title} />
                    </div>
                </div>
            )}
        </div>
    );

    const renderUploadPage = () => (
        <div>
            <h2>Upload Image</h2>
            <form onSubmit={handleImageUpload}>
                <div>
                    <label htmlFor="file">Choose Image:</label>
                    <input type="file" id="file" name="file" required />
                </div>
                <div>
                    <label htmlFor="title">Title:</label>
                    <input type="text" id="title" name="title" />
                </div>
                <div>
                    <label htmlFor="description">Description:</label>
                    <textarea id="description" name="description"></textarea>
                </div>
                <div>
                    <label htmlFor="gallery">Gallery:</label>
                    <input type="text" id="gallery" name="gallery" placeholder="Gallery Name" />
                </div>
                <button type="submit">Upload</button>
            </form>
            {uploadMessage && <p>{uploadMessage}</p>}
        </div>
    );

    return (
        <div className="app-container">
            <nav className="app-nav">
                <button onClick={() => goToPage('gallery')}>Gallery</button>
                <button onClick={() => goToPage('upload')}>Upload</button>
            </nav>
            <main className="app-main">
                {currentPage === 'gallery' && renderGalleryPage()}
                {currentPage === 'upload' && renderUploadPage()}
            </main>
        </div>
    );
}

export default App;

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
