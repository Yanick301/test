import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    const requestUrl = new URL(request.url);
    const code = requestUrl.searchParams.get('code');
    const next = requestUrl.searchParams.get('next') || '/account';
    const error = requestUrl.searchParams.get('error');
    const errorDescription = requestUrl.searchParams.get('error_description');

    // Si une erreur est présente dans l'URL, rediriger vers la page de connexion
    if (error) {
      console.error('Auth callback error:', error, errorDescription);
      return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(error)}`, requestUrl.origin));
    }

    if (code) {
      const supabase = await createClient();
      const { data, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
      
      if (!exchangeError && data?.session) {
        // Redirection après confirmation réussie
        return NextResponse.redirect(new URL(next, requestUrl.origin));
      } else {
        console.error('Error exchanging code for session:', exchangeError);
        return NextResponse.redirect(new URL('/login?error=auth_failed', requestUrl.origin));
      }
    }

    // Si aucun code n'est présent, rediriger vers la page de connexion
    return NextResponse.redirect(new URL('/login?error=no_code', requestUrl.origin));
  } catch (error) {
    console.error('Unexpected error in auth callback:', error);
    const requestUrl = new URL(request.url);
    return NextResponse.redirect(new URL('/login?error=unexpected_error', requestUrl.origin));
  }
}








