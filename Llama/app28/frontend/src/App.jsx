import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [artworks, setArtworks] = useState([]);
  const [galleries, setGalleries] = useState([]);
  const [portfolios, setPortfolios] = useState([]);
  const [artists, setArtists] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [galleryName, setGalleryName] = useState('');
  const [galleryArtworks, setGalleryArtworks] = useState([]);
  const [portfolioName, setPortfolioName] = useState('');
  const [portfolioGalleries, setPortfolioGalleries] = useState([]);
  const [artistName, setArtistName] = useState('');
  const [artistBio, setArtistBio] = useState('');

  useEffect(() => {
    fetch('/api/artworks')
      .then(response => response.json())
      .then(data => setArtworks(data));
    fetch('/api/galleries')
      .then(response => response.json())
      .then(data => setGalleries(data));
    fetch('/api/portfolios')
      .then(response => response.json())
      .then(data => setPortfolios(data));
    fetch('/api/artists')
      .then(response => response.json())
      .then(data => setArtists(data));
  }, []);

  const handleArtworkSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('file', file);
    fetch('/api/artworks', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => setArtworks([...artworks, data]));
  };

  const handleGallerySubmit = (event) => {
    event.preventDefault();
    fetch('/api/galleries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: galleryName, artworks: galleryArtworks })
    })
      .then(response => response.json())
      .then(data => setGalleries([...galleries, data]));
  };

  const handlePortfolioSubmit = (event) => {
    event.preventDefault();
    fetch('/api/portfolios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: portfolioName, galleries: portfolioGalleries })
    })
      .then(response => response.json())
      .then(data => setPortfolios([...portfolios, data]));
  };

  const handleArtistSubmit = (event) => {
    event.preventDefault();
    fetch('/api/artists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: artistName, bio: artistBio })
    })
      .then(response => response.json())
      .then(data => setArtists([...artists, data]));
  };

  return (
    <div>
      <h1>Art Portfolio Management System</h1>
      <section>
        <h2>Artworks</h2>
        <ul>
          {artworks.map(artwork => (
            <li key={artwork.id}>
              <img src={`/uploads/${artwork.filename}`} alt={artwork.title} />
              <h3>{artwork.title}</h3>
              <p>{artwork.description}</p>
            </li>
          ))}
        </ul>
        <form onSubmit={handleArtworkSubmit}>
          <input type="text" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Title" />
          <input type="text" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Description" />
          <input type="file" onChange={(event) => setFile(event.target.files[0])} />
          <button type="submit">Upload Artwork</button>
        </form>
      </section>
      <section>
        <h2>Galleries</h2>
        <ul>
          {galleries.map(gallery => (
            <li key={gallery.id}>
              <h3>{gallery.name}</h3>
              <ul>
                {gallery.artworks.map(artwork => (
                  <li key={artwork}>{artwork}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
        <form onSubmit={handleGallerySubmit}>
          <input type="text" value={galleryName} onChange={(event) => setGalleryName(event.target.value)} placeholder="Gallery Name" />
          <input type="text" value={galleryArtworks.join(',')} onChange={(event) => setGalleryArtworks(event.target.value.split(','))} placeholder="Artwork IDs (comma-separated)" />
          <button type="submit">Create Gallery</button>
        </form>
      </section>
      <section>
        <h2>Portfolios</h2>
        <ul>
          {portfolios.map(portfolio => (
            <li key={portfolio.id}>
              <h3>{portfolio.name}</h3>
              <ul>
                {portfolio.galleries.map(gallery => (
                  <li key={gallery}>{gallery}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
        <form onSubmit={handlePortfolioSubmit}>
          <input type="text" value={portfolioName} onChange={(event) => setPortfolioName(event.target.value)} placeholder="Portfolio Name" />
          <input type="text" value={portfolioGalleries.join(',')} onChange={(event) => setPortfolioGalleries(event.target.value.split(','))} placeholder="Gallery IDs (comma-separated)" />
          <button type="submit">Create Portfolio</button>
        </form>
      </section>
      <section>
        <h2>Artists</h2>
        <ul>
          {artists.map(artist => (
            <li key={artist.id}>
              <h3>{artist.name}</h3>
              <p>{artist.bio}</p>
            </li>
          ))}
        </ul>
        <form onSubmit={handleArtistSubmit}>
          <input type="text" value={artistName} onChange={(event) => setArtistName(event.target.value)} placeholder="Artist Name" />
          <input type="text" value={artistBio} onChange={(event) => setArtistBio(event.target.value)} placeholder="Artist Bio" />
          <button type="submit">Create Artist</button>
        </form>
      </section>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
