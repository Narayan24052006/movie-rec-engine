"use client";

import { useState, useEffect } from 'react';
import MovieCard from '../../../components/MovieCard';

export default function SimilarMovies() {
  const [searchTerm, setSearchTerm] = useState("");
  const [movies, setMovies] = useState([]);
  const [selectedMovieId, setSelectedMovieId] = useState("");
  const [topN, setTopN] = useState(9);
  const [similarItems, setSimilarItems] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [userId, setUserId] = useState(null);

  // Fetch user profile
  useEffect(() => {
    const token = localStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

    fetch(`${baseUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(data => setUserId(data.id))
    .catch(() => {});
  }, []);

  // Debounced search
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      async function fetchMovies() {
        setLoadingSearch(true);
        try {
          const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
          const url = searchTerm 
            ? `${baseUrl}/movies?search=${encodeURIComponent(searchTerm)}&limit=50`
            : `${baseUrl}/movies?limit=50`;
          const res = await fetch(url);
          if (res.ok) {
            const data = await res.json();
            setMovies(data.movies || []);
            if (data.movies && data.movies.length > 0) {
              setSelectedMovieId(data.movies[0].movieId.toString());
            } else {
              setSelectedMovieId("");
            }
          }
        } catch (err) {
          console.error("Movie search failed", err);
        }
        setLoadingSearch(false);
      }
      fetchMovies();
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const handleFindSimilar = async () => {
    if (!selectedMovieId) return;
    setLoadingSimilar(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const res = await fetch(`${baseUrl}/similar-items/${selectedMovieId}?top_n=${topN}`);
      if (res.ok) {
        const data = await res.json();
        setSimilarItems(data.similar_items || []);
      }
    } catch (err) {
      console.error("Failed to find similar items", err);
    }
    setLoadingSimilar(false);
  };

  return (
    <div>
      <h1 className="page-title">Because you watched...</h1>
      <p className="page-sub">Find movies that share DNA with a title you love.</p>

      <div className="form-group">
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#aaa', fontSize: '0.85rem'}}>Search Catalogue</label>
          <input 
            type="text" 
            placeholder="e.g. Toy Story, Matrix..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#aaa', fontSize: '0.85rem'}}>
            Select Movie {loadingSearch && <span style={{fontSize: '0.7rem', color: '#e50914'}}>Loading...</span>}
          </label>
          <select 
            value={selectedMovieId} 
            onChange={(e) => setSelectedMovieId(e.target.value)}
            disabled={movies.length === 0}
          >
            {movies.length === 0 ? <option value="">No matches...</option> : null}
            {movies.map(m => <option key={m.movieId} value={m.movieId}>{m.title}</option>)}
          </select>
        </div>
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#aaa', fontSize: '0.85rem'}}>Matches ({topN})</label>
          <input 
            type="range" 
            min="3" max="20" 
            value={topN} 
            onChange={(e) => setTopN(parseInt(e.target.value))}
            style={{accentColor: '#e50914'}}
          />
        </div>
        <div style={{display: 'flex', alignItems: 'flex-end'}}>
          <button onClick={handleFindSimilar} disabled={loadingSimilar || !selectedMovieId}>
            {loadingSimilar ? "Analysing..." : "Find Similar"}
          </button>
        </div>
      </div>

      {similarItems.length > 0 && (
        <>
          <hr />
          <div className="grid">
            {similarItems.map((item) => (
              <MovieCard key={item.movieId} movie={item} userId={userId} showScore={true} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
