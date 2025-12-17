
'use client';

import { LanguageProvider } from '@/context/LanguageContext';
import type { ReactNode } from 'react';
import { CartProvider } from '@/context/CartContext';
import { SupabaseProvider } from '@/supabase';
import { FavoritesProvider } from '@/context/FavoritesContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <LanguageProvider>
      <ErrorBoundary>
        <SupabaseProvider>
          <FavoritesProvider>
            <CartProvider>{children}</CartProvider>
          </FavoritesProvider>
        </SupabaseProvider>
      </ErrorBoundary>
    </LanguageProvider>
  );
}
