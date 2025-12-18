
import type { Metadata } from 'next';
import { Inter, Cormorant_Garamond } from 'next/font/google';
import './globals.css';
import { AppProviders } from '@/components/AppProviders';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { Toaster } from '@/components/ui/toaster';
import { SkipLink } from '@/components/SkipLink';
import { DynamicLang } from '@/components/DynamicLang';
import { cn } from '@/lib/utils';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const cormorantGaramond = Cormorant_Garamond({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  display: 'swap',
  variable: '--font-cormorant-garamond',
});

export const metadata: Metadata = {
  title: {
    default: 'EZCENTIALS',
    template: '%s | EZCENTIALS',
  },
  description: 'Understated elegance and sophistication. Luxury fashion boutique offering premium clothing, accessories, and seasonal collections.',
  keywords: ['luxury fashion', 'premium clothing', 'boutique', 'elegance', 'sophistication'],
  openGraph: {
    type: 'website',
    locale: 'de_DE',
    alternateLocale: ['fr_FR', 'en_GB'],
    siteName: 'EZCENTIALS',
    title: 'EZCENTIALS',
    description: 'Understated elegance and sophistication.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'EZCENTIALS',
    description: 'Understated elegance and sophistication.',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de" suppressHydrationWarning className="light">
      <body
        className={cn(
          'font-body antialiased',
          inter.variable,
          cormorantGaramond.variable
        )}
      >
        <AppProviders>
          <SkipLink />
          <DynamicLang />
          <div className="relative z-10 flex min-h-screen flex-col">
            <Header />
            <main id="main-content" className="flex-grow">{children}</main>
            <Footer />
          </div>
          <Toaster />
        </AppProviders>
      </body>
    </html>
  );
}
