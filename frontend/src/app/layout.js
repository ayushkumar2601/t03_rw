import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "block",
  axes: ["opsz"],
  variable: "--font-inter",
});

export const metadata = {
  title: "Agarwal Constructions — Knowledge Base AI",
  description: "Ask anything about Agarwal Constructions. Verified answers grounded in our company documentation.",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `if(window.matchMedia('(prefers-reduced-motion: no-preference)').matches){document.documentElement.classList.add('anim');}`,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
