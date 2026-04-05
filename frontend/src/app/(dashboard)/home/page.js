"use client";

import { useState, useEffect } from 'react';
import MovieCard from '../../../components/MovieCard';

export default function Home() {
  const [currentUserProfile, setCurrentUserProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isColdStart, setIsColdStart] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    
    // First figure out who we are
    fetch(`${baseUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(me => {
      setCurrentUserProfile(me);
      // Immediately fetch their recommendations
      return fetch(`${baseUrl}/recommendations/${me.id}?top_n=15`);
    })
    .then(r => {
      if (!r.ok) throw new Error("Could not fetch recommendations");
      return r.json();
    })
    .then(data => {
      setRecommendations(data.recommendations || []);
      setIsColdStart(data.is_cold_start || false);
      setLoading(false);
    })
    .catch((err) => {
      setError(err.message);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div style={{marginTop: '2rem'}}>Loading your personalised feed...</div>;
  }

  if (error) {
    return <div style={{color: '#e50914', marginTop: '2rem'}}>Error: {error}</div>;
  }

  return (
    <div>
      <h1 className="page-title">For You</h1>
      <p className="page-sub">Personalised picks based on your rating history and ML vectors.</p>

      {isColdStart && (
        <div style={{background: 'rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '6px', marginBottom: '1rem'}}>
          ℹ️ Generating recommendations using your saved profile genres.
        </div>
      )}

      {recommendations.length > 0 ? (
        <div className="grid">
          {recommendations.map((rec) => (
            <MovieCard key={rec.movieId} movie={rec} userId={currentUserProfile.id} />
          ))}
        </div>
      ) : (
        <p style={{color: '#777'}}>No recommendations found.</p>
      )}
    </div>
  );
}
