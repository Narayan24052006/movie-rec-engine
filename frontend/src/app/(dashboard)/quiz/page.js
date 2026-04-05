"use client";

import { useState } from 'react';
import MovieCard from '../../../components/MovieCard';

const ALL_GENRES = [
  "Action", "Adventure", "Animation", "Comedy", "Crime",
  "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
  "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
];

export default function NewUserQuiz() {
  const [selectedGenres, setSelectedGenres] = useState(new Set(["Action", "Sci-Fi"]));
  const [topN, setTopN] = useState(12);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  const toggleGenre = (g) => {
    const newSet = new Set(selectedGenres);
    if (newSet.has(g)) newSet.delete(g);
    else newSet.add(g);
    setSelectedGenres(newSet);
  };

  const handleGenFeed = async () => {
    if (selectedGenres.size === 0) return;
    setLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const res = await fetch(`${baseUrl}/quiz`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preferred_genres: Array.from(selectedGenres),
          top_n: topN
        })
      });
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (err) {
      console.error("Failed to generate quiz feed", err);
    }
    setLoading(false);
  };

  return (
    <div>
      <h1 className="page-title">Build Your Profile</h1>
      <p className="page-sub">Pick the genres you love and we'll craft your personal feed instantly.</p>

      <div style={{marginBottom: '2rem'}}>
        <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.6rem', marginBottom: '1.5rem'}}>
          {ALL_GENRES.map(g => {
            const isSel = selectedGenres.has(g);
            return (
              <button 
                key={g} 
                onClick={() => toggleGenre(g)}
                style={{
                  background: isSel ? 'rgba(229, 9, 20, 0.2)' : 'transparent',
                  color: isSel ? '#e50914' : '#aaa',
                  border: `1px solid ${isSel ? '#e50914' : '#444'}`,
                  borderRadius: '20px',
                  padding: '0.4rem 1rem',
                  fontSize: '0.85rem'
                }}
              >
                {g} {isSel && '✓'}
              </button>
            )
          })}
        </div>

        <div className="form-group">
          <div>
            <label style={{display: 'block', marginBottom: '0.5rem', color: '#aaa', fontSize: '0.85rem'}}>Recommendations to show ({topN})</label>
            <input 
              type="range" 
              min="6" max="30" 
              value={topN} 
              onChange={(e) => setTopN(parseInt(e.target.value))}
              style={{accentColor: '#e50914'}}
            />
          </div>
          <div style={{display: 'flex', alignItems: 'flex-end'}}>
            <button onClick={handleGenFeed} disabled={loading || selectedGenres.size === 0}>
              {loading ? "Calibrating..." : "Get My Feed"}
            </button>
          </div>
        </div>
      </div>

      {recommendations.length > 0 && (
        <>
          <hr />
          <div style={{color: '#4caf50', marginBottom: '1rem', fontWeight: 600}}>
            Found {recommendations.length} movies for you!
          </div>
          <div className="grid">
            {recommendations.map((rec) => (
              <MovieCard key={rec.movieId} movie={rec} showScore={false} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
