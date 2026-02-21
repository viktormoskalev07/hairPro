import type { Metadata } from "next";
import "./globals.css";
import Footer from "../components/Footer";

export const metadata: Metadata = {
  title: "Примерка причесок",
  description: "Примерьте новые прически с помощью вашей веб-камеры",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', margin: 0 }}>
        <main style={{ flex: '1' }}>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
