import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Wig Editor',
  description: 'Try on different wigs instantly in your browser!',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
