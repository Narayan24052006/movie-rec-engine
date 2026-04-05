"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import '../globals.css';

const ALL_GENRES = [
  "Action", "Adventure", "Animation", "Comedy", "Crime",
  "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
  "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
];

// Password validation rules
const passwordRules = {
  minLength: { regex: /.{8,}/, label: "At least 8 characters" },
  uppercase: { regex: /[A-Z]/, label: "At least one uppercase letter" },
  number: { regex: /\d/, label: "At least one number" },
  special: { regex: /[!@#$%^&*()_+\-={}\[\]|\\:;"'<>,.?/]/, label: "At least one special character" },
};

export default function Register() {
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [selectedGenres, setSelectedGenres] = useState(new Set(["Action", "Sci-Fi"]));
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // Check password rules
  const passwordValidation = {
    minLength: passwordRules.minLength.regex.test(password),
    uppercase: passwordRules.uppercase.regex.test(password),
    number: passwordRules.number.regex.test(password),
    special: passwordRules.special.regex.test(password),
  };

  const isPasswordValid = Object.values(passwordValidation).every(v => v);
  const isUsernameValid = username.includes("@gmail.com") && username.length > 10;

  const toggleGenre = (g) => {
    const newSet = new Set(selectedGenres);
    if (newSet.has(g)) newSet.delete(g);
    else newSet.add(g);
    setSelectedGenres(newSet);
  };

  const handleNext = (e) => {
    e.preventDefault();
    if (!isUsernameValid || !isPasswordValid) return;
    setStep(2);
  };

  const handleRegister = async () => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

      // 1. Register User with pre-filled cold-start preferences
      const regRes = await fetch(`${baseUrl}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password,
          preferred_genres: Array.from(selectedGenres)
        }),
      });

      if (!regRes.ok) {
        const errorData = await regRes.json();
        throw new Error(errorData.detail || "Registration failed");
      }

      // 2. Auto-login
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const loginRes = await fetch(`${baseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (loginRes.ok) {
        const data = await loginRes.json();
        localStorage.setItem("token", data.access_token);
        router.push("/home");
      } else {
        router.push("/login"); // fallback
      }

    } catch (err) {
      setError(err.message);
      setStep(1);
    }
    setLoading(false);
  };

  return (
    <div style={{minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0a0a0a, #1a1a1a)'}}>
      <div style={{background: 'rgba(20, 20, 20, 0.95)', padding: '3.5rem', borderRadius: '12px', width: '100%', maxWidth: '600px', boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)', backdropFilter: 'blur(4px)', border: '1px solid rgba(255, 255, 255, 0.05)'}}>
        <div className="brand" style={{marginBottom: '2.5rem', textAlign: 'center', fontSize: '1.8rem', fontWeight: 'bold'}}>STREAM<span style={{color: '#e50914'}}>REC</span></div>

        {error && (
          <div style={{background: 'rgba(229, 9, 20, 0.2)', border: '1px solid #e50914', color: '#ff6b6b', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <span>⚠️</span> {error}
          </div>
        )}

        {step === 1 && (
          <form onSubmit={handleNext} style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
            <div>
              <h1 style={{fontSize: '2rem', marginBottom: '0.5rem', fontWeight: '600'}}>Create Account</h1>
              <p style={{color: '#aaa', fontSize: '0.95rem', margin: '0.5rem 0 1.5rem 0'}}>Join millions discovering movies they love</p>
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', color: '#fff', fontSize: '0.95rem', fontWeight: '500'}}>Email Address</label>
              <input
                type="email"
                placeholder="your.email@gmail.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{width: '100%', padding: '1rem', background: 'rgba(51, 51, 51, 0.8)', border: isUsernameValid ? '2px solid #22c55e' : '1px solid #444', borderRadius: '6px', color: '#fff', fontSize: '1rem', transition: 'all 0.3s', outline: 'none'}}
                required
              />
              {username && !isUsernameValid && (
                <p style={{color: '#ff6b6b', fontSize: '0.8rem', marginTop: '0.4rem'}}>Gmail address required</p>
              )}
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', color: '#fff', fontSize: '0.95rem', fontWeight: '500'}}>Password</label>
              <div style={{position: 'relative'}}>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{width: '100%', padding: '1rem 3rem 1rem 1rem', background: 'rgba(51, 51, 51, 0.8)', border: password && isPasswordValid ? '2px solid #22c55e' : password ? '2px solid #fbbf24' : '1px solid #444', borderRadius: '6px', color: '#fff', fontSize: '1rem', transition: 'all 0.3s', outline: 'none', paddingRight: '3rem'}}
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

              {/* Password Rules Checklist */}
              {password && (
                <div style={{marginTop: '1rem', padding: '1rem', background: 'rgba(31, 41, 55, 0.6)', borderRadius: '6px', border: '1px solid rgba(75, 85, 99, 0.5)'}}>
                  <p style={{color: '#bbb', fontSize: '0.8rem', fontWeight: '500', marginBottom: '0.8rem'}}>Password Requirements:</p>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                    {Object.entries(passwordValidation).map(([key, isValid]) => (
                      <div key={key} style={{display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.85rem', color: isValid ? '#22c55e' : '#9ca3af', transition: 'all 0.3s'}}>
                        <span style={{fontSize: '1rem'}}>{isValid ? '✓' : '○'}</span>
                        <span>{passwordRules[key].label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={!isUsernameValid || !isPasswordValid}
              style={{width: '100%', padding: '1rem', marginTop: '1.5rem', background: (!isUsernameValid || !isPasswordValid) ? '#555' : '#e50914', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '1rem', fontWeight: '600', cursor: (!isUsernameValid || !isPasswordValid) ? 'not-allowed' : 'pointer', transition: 'all 0.3s', opacity: (!isUsernameValid || !isPasswordValid) ? 0.6 : 1, boxShadow: (!isUsernameValid || !isPasswordValid) ? 'none' : '0 4px 15px rgba(229, 9, 20, 0.4)'}}
            >
              Next ➜
            </button>

            <div style={{marginTop: '1.5rem', color: '#737373', fontSize: '0.9rem', textAlign: 'center'}}>
              Already have an account? <Link href="/login" style={{color: '#e50914', fontWeight: '600', textDecoration: 'none'}}>Sign in</Link>
            </div>
          </form>
        )}

        {step === 2 && (
          <div>
            <h1 style={{fontSize: '2rem', marginBottom: '0.5rem', fontWeight: '600'}}>Personalise Profile</h1>
            <p style={{color: '#aaa', marginBottom: '2rem', fontSize: '0.95rem'}}>
              Select genres you love so our AI builds your perfect recommendations
            </p>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.8rem', marginBottom: '2rem'}}>
              {ALL_GENRES.map(g => {
                const isSel = selectedGenres.has(g);
                return (
                  <button
                    key={g}
                    onClick={() => toggleGenre(g)}
                    style={{
                      background: isSel ? 'rgba(229, 9, 20, 0.3)' : 'rgba(55, 65, 81, 0.5)',
                      color: isSel ? '#e50914' : '#aaa',
                      border: `2px solid ${isSel ? '#e50914' : '#444'}`,
                      borderRadius: '24px',
                      padding: '0.6rem 1.2rem',
                      fontSize: '0.9rem',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.3s',
                      background: isSel ? 'rgba(229, 9, 20, 0.15)' : 'transparent'
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
                )
              })}
            </div>
            <button
              onClick={handleRegister}
              disabled={loading || selectedGenres.size === 0}
              style={{width: '100%', padding: '1rem', background: selectedGenres.size === 0 ? '#555' : '#e50914', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '1rem', fontWeight: '600', cursor: selectedGenres.size === 0 ? 'not-allowed' : 'pointer', transition: 'all 0.3s', opacity: selectedGenres.size === 0 ? 0.6 : 1, boxShadow: selectedGenres.size === 0 ? 'none' : '0 4px 15px rgba(229, 9, 20, 0.4)'}}>
              {loading ? "Creating Profile..." : "Complete Registration ✓"}
            </button>
            <button
              onClick={() => setStep(1)}
              disabled={loading}
              style={{width: '100%', padding: '1rem', marginTop: '1rem', background: 'transparent', border: '1px solid #555', color: '#fff', borderRadius: '6px', fontSize: '1rem', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.3s', opacity: loading ? 0.6 : 1}}
              onMouseEnter={(e) => e.target.style.borderColor = '#fff'}
              onMouseLeave={(e) => e.target.style.borderColor = '#555'}
            >
              ← Back
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
