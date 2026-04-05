"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function LandingPage() {
  const router = useRouter();

  // If already logged in, skip landing page
  useEffect(() => {
    if (localStorage.getItem("token")) {
      router.push("/home");
    }
  }, [router]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("https://images.unsplash.com/photo-1536440136628-849c177e76a1?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80") center/cover no-repeat fixed'
    }}>
      <header style={{padding: '2rem 3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div className="brand" style={{fontSize: '2rem'}}>STREAM<span>REC</span></div>
        <div>
          <Link href="/login" style={{color: '#fff', fontWeight: 600, marginRight: '1.5rem'}}>Sign In</Link>
          <Link href="/register">
            <button style={{padding: '0.6rem 1.5rem'}}>Sign Up</button>
          </Link>
        </div>
      </header>
      
      <main style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '2rem'}}>
        <h1 style={{fontSize: '3.5rem', fontWeight: 800, marginBottom: '1rem', maxWidth: '800px', lineHeight: 1.1}}>
          Unlimited movies, tailored specifically to your taste.
        </h1>
        <p style={{fontSize: '1.4rem', marginBottom: '2rem', color: '#e5e5e5'}}>
          Our advanced AI hybrid engines discover the films you'll love.
        </p>
        <Link href="/register">
          <button style={{fontSize: '1.2rem', padding: '1rem 3rem', borderRadius: '4px'}}>
            Get Started ➜
          </button>
        </Link>
      </main>
    </div>
  );
}
