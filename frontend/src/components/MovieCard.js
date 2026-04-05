"use client";

import { useState, useEffect } from 'react';
import styles from './MovieCard.module.css';

export default function MovieCard({ movie, userId, showScore = true }) {
  const [expanded, setExpanded] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [inWishlist, setInWishlist] = useState(false);
  const [wishlistLoading, setWishlistLoading] = useState(false);

  useEffect(() => {
    // Check if movie is in wishlist
    if (userId) {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const token = localStorage.getItem("token");
      fetch(`${baseUrl}/wishlist/${movie.movieId}/check`, {
        headers: { "Authorization": `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(data => setInWishlist(data.in_wishlist))
        .catch(() => {});
    }
  }, [movie.movieId, userId]);

  const handleExpand = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (!explanation && userId) {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const res = await fetch(`${baseUrl}/explain/${userId}/${movie.movieId}`);
        if (res.ok) {
          setExplanation(await res.json());
        }
      } catch (err) {
        console.error("Failed to load explanation", err);
      }
      setLoading(false);
    }
  };

  const handleWishlist = async (e) => {
    e.stopPropagation();
    setWishlistLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const token = localStorage.getItem("token");
      const method = inWishlist ? "DELETE" : "POST";

      const res = await fetch(`${baseUrl}/wishlist/${movie.movieId}`, {
        method,
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: method === "POST" ? JSON.stringify({
          title: movie.title,
          genres: movie.genres
        }) : undefined
      });

      if (res.ok) {
        setInWishlist(!inWishlist);
      }
    } catch (err) {
      console.error("Failed to update wishlist", err);
    }
    setWishlistLoading(false);
  };

  const getSourceLabel = (src) => {
    switch(src) {
      case "popularity_fallback": return "Trending";
      case "content_fallback": return "Content";
      case "cold_start_quiz": return "Personalised";
      case "hybrid_similar": return "Similar";
      default: return src;
    }
  };

  const pct = movie.score > 0 ? Math.min(Math.floor(movie.score * 100), 99) : 0;

  return (
    <div className={styles.card}>
      <div>
        <div className={styles.title}>{movie.title || "Unknown Title"}</div>
        <div className={styles.genres}>{(movie.genres || "—").replace(/\|/g, "  ·  ")}</div>
        <div className={styles.badges}>
          {showScore && movie.score > 0 && (
            <span className={styles.matchBadge}>{pct}% Match</span>
          )}
          {movie.source && movie.source !== "hybrid" && (
            <span className={styles.sourceBadge}>{getSourceLabel(movie.source)}</span>
          )}
        </div>
      </div>

      <div style={{display: 'flex', gap: '0.5rem', marginTop: '1rem'}}>
        {userId && (
          <button
            onClick={handleWishlist}
            disabled={wishlistLoading}
            style={{flex: 1, padding: '0.5rem', background: inWishlist ? '#e50914' : 'transparent', color: inWishlist ? '#fff' : '#e50914', border: `1px solid #e50914`, borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: '600', transition: 'all 0.2s'}}
            title={inWishlist ? "Remove from wishlist" : "Add to wishlist"}
          >
            {inWishlist ? 'Saved' : 'Save'}
          </button>
        )}
        {userId && (
          <button className={styles.detailsBtn} onClick={handleExpand} style={{flex: 1}}>
            {expanded ? "Hide Details" : "Why this?"}
          </button>
        )}
      </div>

      {expanded && (
        <div className={styles.expandedDetails}>
          {loading && <div>Analysing model data...</div>}
          {!loading && explanation && (
            <>
              {explanation.explanation_text && <i style={{color: '#aaa', display: 'block', marginBottom: '10px'}}>{explanation.explanation_text}</i>}
              <div className={styles.metricRow}>
                <div className={styles.metricBox}>
                  <div className={styles.metricLabel}>CF Score</div>
                  <div className={styles.metricVal}>{explanation.cf_score.toFixed(3)}</div>
                </div>
                <div className={styles.metricBox}>
                  <div className={styles.metricLabel}>CBF Score</div>
                  <div className={styles.metricVal}>{explanation.cbf_score.toFixed(3)}</div>
                </div>
                <div className={styles.metricBox}>
                  <div className={styles.metricLabel}>Popularity</div>
                  <div className={styles.metricVal}>{Math.floor(explanation.popularity).toLocaleString()}</div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
