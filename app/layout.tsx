import type { Metadata } from "next";
import "./globals.css";

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
      <body>{children}</body>
    </html>
  );
}
