"use client";

import { useState, useEffect } from 'react';
import MovieCard from '../../../components/MovieCard';
import '../../globals.css';

export default function Wishlist() {
  const [profile, setProfile] = useState(null);
  const [wishlistItems, setWishlistItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

    // Get profile
    fetch(`${baseUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(data => {
      setProfile(data);
      
      // Get wishlist
      return fetch(`${baseUrl}/wishlist`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
    })
    .then(r => r.json())
    .then(data => {
      setWishlistItems(data.wishlist || []);
      setLoading(false);
    })
    .catch((err) => {
      setError(err.message);
      setLoading(false);
    });
  }, []);

  if (loading) return <div style={{marginTop: '2rem'}}>Loading your wishlist...</div>;

  return (
    <div>
      <h1 className="page-title">❤️ Your Wishlist</h1>
      <p className="page-sub">Movies you want to watch later</p>

      {error && (
        <div style={{color: '#e50914', marginTop: '1rem'}}>Error: {error}</div>
      )}

      {wishlistItems.length > 0 ? (
        <div>
          <p style={{color: '#aaa', marginBottom: '1.5rem'}}>You have {wishlistItems.length} movie{wishlistItems.length !== 1 ? 's' : ''} in your wishlist</p>
          <div className="grid">
            {wishlistItems.map((item) => (
              <MovieCard 
                key={item.movie_id} 
                movie={{
                  movieId: item.movie_id,
                  title: item.movie_title,
                  genres: item.movie_genres,
                  score: 0,
                  source: "wishlist"
                }}
                userId={profile?.id}
                showScore={false}
              />
            ))}
          </div>
        </div>
      ) : (
        <div style={{background: 'rgba(255,255,255,0.05)', padding: '3rem', borderRadius: '10px', textAlign: 'center', marginTop: '2rem'}}>
          <p style={{color: '#aaa', fontSize: '1.1rem', marginBottom: '1rem'}}>Your wishlist is empty</p>
          <p style={{color: '#777', fontSize: '0.95rem'}}>Start adding movies from the For You or Similar Items pages!</p>
        </div>
      )}
    </div>
  );
}
