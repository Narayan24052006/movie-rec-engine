"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import '../globals.css';

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch(`${baseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Login failed");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/home");

    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const isValid = username && password;

  return (
    <div style={{minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0a0a0a, #1a1a1a)'}}>
      <div style={{background: 'rgba(20, 20, 20, 0.95)', padding: '3.5rem', borderRadius: '12px', width: '100%', maxWidth: '500px', boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)', backdropFilter: 'blur(4px)', border: '1px solid rgba(255, 255, 255, 0.05)'}}>
        <div className="brand" style={{marginBottom: '2.5rem', textAlign: 'center', fontSize: '1.8rem', fontWeight: 'bold'}}>STREAM<span style={{color: '#e50914'}}>REC</span></div>

        <div style={{marginBottom: '2rem'}}>
          <h1 style={{fontSize: '2rem', marginBottom: '0.5rem', fontWeight: '600'}}>Sign In</h1>
          <p style={{color: '#aaa', fontSize: '0.95rem', margin: 0}}>Welcome back to StreamRec</p>
        </div>

        {error && (
          <div style={{background: 'rgba(229, 9, 20, 0.2)', border: '1px solid #e50914', color: '#ff6b6b', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <span>⚠️</span> {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
          <div>
            <label style={{display: 'block', marginBottom: '0.5rem', color: '#fff', fontSize: '0.95rem', fontWeight: '500'}}>Email Address</label>
            <input
              type="email"
              placeholder="your.email@gmail.com"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{width: '100%', padding: '1rem', background: 'rgba(51, 51, 51, 0.8)', border: '1px solid #444', borderRadius: '6px', color: '#fff', fontSize: '1rem', transition: 'all 0.3s', outline: 'none'}}
              onFocus={(e) => e.target.style.borderColor = '#666'}
              onBlur={(e) => e.target.style.borderColor = '#444'}
              required
            />
          </div>

          <div>
            <label style={{display: 'block', marginBottom: '0.5rem', color: '#fff', fontSize: '0.95rem', fontWeight: '500'}}>Password</label>
            <div style={{position: 'relative'}}>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{width: '100%', padding: '1rem 3rem 1rem 1rem', background: 'rgba(51, 51, 51, 0.8)', border: '1px solid #444', borderRadius: '6px', color: '#fff', fontSize: '1rem', transition: 'all 0.3s', outline: 'none'}}
                onFocus={(e) => e.target.style.borderColor = '#666'}
                onBlur={(e) => e.target.style.borderColor = '#444'}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: '#999', cursor: 'pointer', fontSize: '0.9rem', fontWeight: '500', transition: 'color 0.2s'}}
                onMouseEnter={(e) => e.target.style.color = '#fff'}
                onMouseLeave={(e) => e.target.style.color = '#999'}
              >
                {showPassword ? '🙈 Hide' : '👁️ Show'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={!isValid || loading}
            style={{width: '100%', padding: '1rem', marginTop: '1rem', background: !isValid ? '#555' : '#e50914', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '1rem', fontWeight: '600', cursor: !isValid ? 'not-allowed' : 'pointer', transition: 'all 0.3s', opacity: !isValid ? 0.6 : 1, boxShadow: !isValid ? 'none' : '0 4px 15px rgba(229, 9, 20, 0.4)'}}
          >
            {loading ? "Signing In..." : "Sign In"}
          </button>
        </form>

        <div style={{marginTop: '2rem', color: '#737373', fontSize: '0.9rem', textAlign: 'center'}}>
          New to StreamRec? <Link href="/register" style={{color: '#e50914', fontWeight: '600', textDecoration: 'none'}}>Sign up now</Link>
        </div>
      </div>
    </div>
  );
}
