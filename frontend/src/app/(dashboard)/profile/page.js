"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import '../../globals.css';

const ALL_GENRES = [
  "Action", "Adventure", "Animation", "Comedy", "Crime",
  "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
  "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
];

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [selectedGenres, setSelectedGenres] = useState(new Set());
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    fetch(`${baseUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(data => {
      setProfile(data);
      setSelectedGenres(new Set(data.preferred_genres || []));
      setLoading(false);
    })
    .catch(() => setLoading(false));
  }, []);

  const handleSaveGenres = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const token = localStorage.getItem("token");
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      
      const res = await fetch(`${baseUrl}/auth/me/genres`, {
        method: "PUT",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          preferred_genres: Array.from(selectedGenres)
        })
      });

      if (res.ok) {
        setProfile({ ...profile, preferred_genres: Array.from(selectedGenres) });
        setEditMode(false);
        setMessage({ type: "success", text: "Genres updated successfully!" });
      } else {
        setMessage({ type: "error", text: "Failed to update genres" });
      }
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
    setSaving(false);
  };

  const toggleGenre = (genre) => {
    const newSet = new Set(selectedGenres);
    if (newSet.has(genre)) {
      newSet.delete(genre);
    } else {
      newSet.add(genre);
    }
    setSelectedGenres(newSet);
  };

  if (loading) return <div style={{marginTop: '2rem'}}>Loading profile...</div>;
  if (!profile) return <div style={{color: '#e50914', marginTop: '2rem'}}>Failed to load profile.</div>;

  return (
    <div>
      <h1 className="page-title">Profile Settings</h1>
      <p className="page-sub">Manage your account details and preferences.</p>

      {message && (
        <div style={{background: message.type === "success" ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)', border: `1px solid ${message.type === "success" ? '#22c55e' : '#ef4444'}`, color: message.type === "success" ? '#22c55e' : '#ff6b6b', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem'}}>
          {message.text}
        </div>
      )}

      <div style={{background: 'rgba(20, 20, 20, 0.7)', border: '1px solid #333', padding: '2rem', borderRadius: '10px', maxWidth: '800px'}}>
        {/* Account Info Section */}
        <div style={{marginBottom: '2.5rem'}}>
          <h2 style={{fontSize: '1.3rem', marginBottom: '1.5rem', fontWeight: '600'}}>Account Information</h2>
          
          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #333'}}>
            <div style={{color: '#aaa'}}>Platform ID</div>
            <div style={{fontWeight: 600}}>User #{profile.id}</div>
          </div>

          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #333'}}>
            <div style={{color: '#aaa'}}>Email Address</div>
            <div style={{fontWeight: 600}}>{profile.username}</div>
          </div>

          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #333'}}>
            <div style={{color: '#aaa'}}>Account Role</div>
            <div style={{fontWeight: 600, color: profile.is_admin ? '#e50914' : '#4caf50'}}>
              {profile.is_admin ? "🔐 Administrator" : "👤 Standard User"}
            </div>
          </div>

          <div style={{display: 'flex', justifyContent: 'space-between'}}>
            <div style={{color: '#aaa'}}>Member Since</div>
            <div style={{fontWeight: 600}}>{new Date(profile.created_at).toLocaleDateString()}</div>
          </div>
        </div>

        {/* Admin Portal Link */}
        {profile.is_admin && (
          <div style={{background: 'rgba(229, 9, 20, 0.1)', border: '1px solid rgba(229, 9, 20, 0.3)', padding: '1rem', borderRadius: '6px', marginBottom: '2.5rem'}}>
            <p style={{color: '#e50914', fontWeight: '500', marginBottom: '0.8rem'}}>🔐 Admin Access</p>
            <Link href="/admin" style={{color: '#e50914', fontWeight: '600', textDecoration: 'underline'}}>
              Go to Admin Dashboard →
            </Link>
          </div>
        )}

        {/* Genres Section */}
        <div>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem'}}>
            <h2 style={{fontSize: '1.3rem', fontWeight: '600'}}>Preferred Genres</h2>
            {!editMode && (
              <button
                onClick={() => setEditMode(true)}
                style={{background: '#e50914', color: '#fff', padding: '0.5rem 1rem', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '0.9rem', fontWeight: '600'}}
              >
                Edit Genres
              </button>
            )}
          </div>

          {!editMode ? (
            <div>
              <p style={{color: '#aaa', fontSize: '0.9rem', marginBottom: '1rem'}}>These genres help personalize your recommendations:</p>
              <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                {profile.preferred_genres && profile.preferred_genres.length > 0 ? (
                  profile.preferred_genres.map(g => (
                    <span key={g} style={{background: 'rgba(229, 9, 20, 0.2)', border: '1px solid #e50914', color: '#e50914', padding: '0.5rem 1rem', borderRadius: '20px', fontSize: '0.85rem', fontWeight: '500'}}>
                      {g}
                    </span>
                  ))
                ) : (
                  <span style={{color: '#777'}}>No genres selected. Click "Edit Genres" to add some.</span>
                )}
              </div>
            </div>
          ) : (
            <div>
              <p style={{color: '#aaa', fontSize: '0.9rem', marginBottom: '1rem'}}>Select the genres you enjoy:</p>
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
                        border: `2px solid ${isSel ? '#e50914' : '#444'}`,
                        borderRadius: '24px',
                        padding: '0.5rem 1rem',
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'all 0.3s'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.borderColor = '#e50914';
                        e.target.style.color = '#e50914';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.borderColor = isSel ? '#e50914' : '#444';
                        e.target.style.color = isSel ? '#e50914' : '#aaa';
                      }}
                    >
                      {g} {isSel && '✓'}
                    </button>
                  );
                })}
              </div>

              <div style={{display: 'flex', gap: '1rem'}}>
                <button
                  onClick={handleSaveGenres}
                  disabled={saving || selectedGenres.size === 0}
                  style={{flex: 1, padding: '0.8rem', background: selectedGenres.size === 0 ? '#555' : '#e50914', color: '#fff', border: 'none', borderRadius: '6px', cursor: selectedGenres.size === 0 ? 'not-allowed' : 'pointer', fontWeight: '600', opacity: selectedGenres.size === 0 ? 0.6 : 1}}
                >
                  {saving ? "Saving..." : "Save Genres"}
                </button>
                <button
                  onClick={() => {
                    setEditMode(false);
                    setSelectedGenres(new Set(profile.preferred_genres || []));
                  }}
                  disabled={saving}
                  style={{flex: 1, padding: '0.8rem', background: 'transparent', color: '#fff', border: '1px solid #555', borderRadius: '6px', cursor: 'pointer', fontWeight: '600'}}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
