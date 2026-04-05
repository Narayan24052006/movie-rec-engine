"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function DashboardLayout({ children }) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Verify token & get profile
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    fetch(`${baseUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => {
      if (!res.ok) throw new Error("Invalid token");
      return res.json();
    })
    .then(data => {
      setUsername(data.username);
      setIsAdmin(data.is_admin);
      setLoading(false);
    })
    .catch(() => {
      localStorage.removeItem("token");
      router.push("/login");
    });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) return <div style={{padding: '3rem'}}>Authenticating...</div>;

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">STREAM<span>REC</span></div>
        
        <div className="status-online" style={{color: '#aaa', fontSize: '0.8rem'}}>
          Logged in as <strong style={{color: '#fff'}}>{username}</strong>
          {isAdmin && <span style={{marginLeft: '8px', color: '#e50914', border: '1px solid currentColor', borderRadius: '4px', padding: '1px 4px', fontSize: '0.6rem'}}>ADMIN</span>}
        </div>

        <hr style={{margin: '0'}}/>

        <nav className="nav-links">
          {!isAdmin ? (
            <>
              <Link href="/home" className="nav-link">🎯 For You</Link>
              <Link href="/similar" className="nav-link">🔍 Similar Movies</Link>
              <Link href="/wishlist" className="nav-link">❤️ My Wishlist</Link>
              <Link href="/profile" className="nav-link">⚙️ Profile Settings</Link>
            </>
          ) : (
            <Link href="/profile" className="nav-link">⚙️ Profile Settings</Link>
          )}
          {isAdmin && (
            <>
              <hr style={{margin: '1rem 0'}}/>
              <Link href="/admin" className="nav-link" style={{color: '#e50914', fontWeight: '600'}}>
                🔐 Admin Dashboard
              </Link>
            </>
          )}
          <button onClick={handleLogout} style={{background: 'transparent', border: '1px solid #333', marginTop: 'auto', textAlign: 'left', padding: '0.8rem 1rem'}} className="nav-link">
            🚪 Log Out
          </button>
        </nav>
      </aside>
      
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
