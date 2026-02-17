import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Lokkal News',
  description: 'Community-first local news platform'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="mx-auto min-h-screen max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
