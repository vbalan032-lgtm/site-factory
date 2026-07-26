import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Новый проект",
  description: "Стартовая страница проекта",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}

