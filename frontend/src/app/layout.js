import './globals.css';

export const metadata = {
  title: 'StreamRec',
  description: 'Movie Recommendation Engine',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
