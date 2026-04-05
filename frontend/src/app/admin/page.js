"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import '../globals.css';

export default function AdminDashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersTotal, setUsersTotal] = useState(0);
  const [usersPage, setUsersPage] = useState(0);
  const [message, setMessage] = useState(null);

  // Auth check on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

    if (!token) {
      router.push("/login");
      return;
    }

    fetch(`${baseUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(data => {
      if (!data.is_admin) {
        router.push("/home");
        return;
      }
      setProfile(data);
      setLoading(false);
      // Fetch users after setting profile
      fetchUsersData(0, token, baseUrl);
    })
    .catch(err => {
      console.error("Auth error:", err);
      router.push("/login");
    });
  }, [router]);

  const fetchUsersData = (page, token, baseUrl) => {
    if (!token) token = localStorage.getItem("token");
    if (!baseUrl) baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

    setUsersLoading(true);
    const offset = page * 50;

    fetch(`${baseUrl}/admin/users?limit=50&offset=${offset}`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(data => {
      console.log("✓ Users fetched:", data);
      setUsers(data.users || []);
      setUsersTotal(data.total || 0);
      setUsersPage(page);
    })
    .catch(err => {
      console.error("✗ Fetch error:", err);
      setMessage({ type: "error", text: `Failed to load users: ${err.message}` });
    })
    .finally(() => setUsersLoading(false));
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm("Are you sure? This cannot be undone.")) return;

    try {
      const token = localStorage.getItem("token");
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

      const res = await fetch(`${baseUrl}/admin/users/${userId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        setMessage({ type: "success", text: "User deleted" });
        fetchUsersData(usersPage, token, baseUrl);
      } else {
        throw new Error("Delete failed");
      }
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const handlePromoteUser = async (userId) => {
    try {
      const token = localStorage.getItem("token");
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

      const res = await fetch(`${baseUrl}/admin/users/${userId}/promote`, {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        setMessage({ type: "success", text: "User promoted to admin" });
        fetchUsersData(usersPage, token, baseUrl);
      } else {
        throw new Error("Promotion failed");
      }
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const handleDemoteAdmin = async (userId) => {
    try {
      const token = localStorage.getItem("token");
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

      const res = await fetch(`${baseUrl}/admin/users/${userId}/demote`, {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        setMessage({ type: "success", text: "Admin demoted to user" });
        fetchUsersData(usersPage, token, baseUrl);
      } else {
        throw new Error("Demotion failed");
      }
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const handleProfileClick = () => {
    router.push("/profile");
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f0f0f', color: '#fff' }}>
        Loading admin panel...
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0f0f0f', color: '#fff', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ background: '#1a1a1a', borderBottom: '1px solid #333', padding: '1.5rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', margin: '0 0 0.3rem 0', fontWeight: '700' }}>Admin Dashboard</h1>
          <p style={{ margin: 0, color: '#aaa', fontSize: '0.9rem' }}>{profile?.username}</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button
            onClick={handleProfileClick}
            style={{ background: '#333', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer', transition: 'all 0.2s' }}
            onMouseEnter={(e) => e.target.style.background = '#444'}
            onMouseLeave={(e) => e.target.style.background = '#333'}
          >
            ⚙️ Profile
          </button>
          <button
            onClick={handleLogout}
            style={{ background: '#e50914', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer', transition: 'all 0.2s' }}
            onMouseEnter={(e) => e.target.style.background = '#c40812'}
            onMouseLeave={(e) => e.target.style.background = '#e50914'}
          >
            🚪 Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>

        {/* Message */}
        {message && (
          <div style={{ background: message.type === "success" ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)', border: `1px solid ${message.type === "success" ? '#22c55e' : '#ef4444'}`, color: message.type === "success" ? '#22c55e' : '#ff6b6b', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
            {message.text}
          </div>
        )}

        {/* Users Section */}
        <div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', fontWeight: '700' }}>Users Management ({usersTotal})</h2>

          {usersLoading && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#aaa' }}>Loading users...</div>
          )}

          {!usersLoading && users.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem', background: '#1a1a1a', borderRadius: '8px', color: '#888' }}>
              <p style={{ margin: 0, fontSize: '1.1rem' }}>No users found in database</p>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem' }}>Check API connection or database</p>
            </div>
          )}

          {users.length > 0 && (
            <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #333', background: '#1a1a1a' }}>
                    <th style={{ textAlign: 'left', padding: '1rem', color: '#aaa', fontWeight: '600', fontSize: '0.9rem' }}>ID</th>
                    <th style={{ textAlign: 'left', padding: '1rem', color: '#aaa', fontWeight: '600', fontSize: '0.9rem' }}>Email</th>
                    <th style={{ textAlign: 'left', padding: '1rem', color: '#aaa', fontWeight: '600', fontSize: '0.9rem' }}>Role</th>
                    <th style={{ textAlign: 'left', padding: '1rem', color: '#aaa', fontWeight: '600', fontSize: '0.9rem' }}>Joined</th>
                    <th style={{ textAlign: 'left', padding: '1rem', color: '#aaa', fontWeight: '600', fontSize: '0.9rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id} style={{ borderBottom: '1px solid #222', transition: 'background 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.background = '#1a1a1a'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '1rem', fontSize: '0.9rem' }}>{user.id}</td>
                      <td style={{ padding: '1rem', fontSize: '0.9rem' }}>{user.username}</td>
                      <td style={{ padding: '1rem', fontSize: '0.9rem', color: user.is_admin ? '#e50914' : '#4caf50', fontWeight: '500' }}>
                        {user.is_admin ? 'Admin' : 'User'}
                      </td>
                      <td style={{ padding: '1rem', color: '#aaa', fontSize: '0.85rem' }}>
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          {!user.is_admin && (
                            <button
                              onClick={() => handlePromoteUser(user.id)}
                              style={{ background: '#fbbf24', color: '#000', padding: '0.3rem 0.6rem', borderRadius: '4px', border: 'none', cursor: 'pointer', fontSize: '0.75rem', fontWeight: '600', transition: 'all 0.2s' }}
                              onMouseEnter={(e) => e.target.style.opacity = '0.8'}
                              onMouseLeave={(e) => e.target.style.opacity = '1'}
                            >
                              Promote
                            </button>
                          )}
                          {user.is_admin && user.id !== profile?.id && (
                            <button
                              onClick={() => handleDemoteAdmin(user.id)}
                              style={{ background: '#f97316', color: '#fff', padding: '0.3rem 0.6rem', borderRadius: '4px', border: 'none', cursor: 'pointer', fontSize: '0.75rem', fontWeight: '600', transition: 'all 0.2s' }}
                              onMouseEnter={(e) => e.target.style.opacity = '0.8'}
                              onMouseLeave={(e) => e.target.style.opacity = '1'}
                            >
                              Demote
                            </button>
                          )}
                          {user.id !== profile?.id && (
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              style={{ background: '#ef4444', color: '#fff', padding: '0.3rem 0.6rem', borderRadius: '4px', border: 'none', cursor: 'pointer', fontSize: '0.75rem', fontWeight: '600', transition: 'all 0.2s' }}
                              onMouseEnter={(e) => e.target.style.opacity = '0.8'}
                              onMouseLeave={(e) => e.target.style.opacity = '1'}
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {users.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '2rem' }}>
              <button
                onClick={() => fetchUsersData(Math.max(0, usersPage - 1))}
                disabled={usersPage === 0}
                style={{ padding: '0.5rem 1rem', background: usersPage === 0 ? '#555' : '#e50914', color: '#fff', border: 'none', borderRadius: '6px', cursor: usersPage === 0 ? 'not-allowed' : 'pointer', fontWeight: '600', fontSize: '0.9rem', transition: 'all 0.2s' }}
              >
                ← Previous
              </button>
              <span style={{ padding: '0.5rem 1rem', color: '#aaa', alignSelf: 'center' }}>Page {usersPage + 1} of {Math.ceil(usersTotal / 50)}</span>
              <button
                onClick={() => fetchUsersData(usersPage + 1)}
                disabled={usersPage * 50 + 50 >= usersTotal}
                style={{ padding: '0.5rem 1rem', background: usersPage * 50 + 50 >= usersTotal ? '#555' : '#e50914', color: '#fff', border: 'none', borderRadius: '6px', cursor: usersPage * 50 + 50 >= usersTotal ? 'not-allowed' : 'pointer', fontWeight: '600', fontSize: '0.9rem', transition: 'all 0.2s' }}
              >
                Next →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
