'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { TranslatedText } from '@/components/TranslatedText';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { Settings } from 'lucide-react';

const COOKIE_CONSENT_KEY = 'ezcentials-cookie-consent';

type CookiePreferences = {
  necessary: boolean;
  analytics: boolean;
  marketing: boolean;
  timestamp: number;
};

const defaultPreferences: CookiePreferences = {
  necessary: true, // Always true, cannot be disabled
  analytics: false,
  marketing: false,
  timestamp: Date.now(),
};

export function CookieConsent() {
  const [isOpen, setIsOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>(defaultPreferences);

  useEffect(() => {
    // Check if consent has been given
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(COOKIE_CONSENT_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved) as CookiePreferences;
          setPreferences(parsed);
          setIsOpen(false);
        } catch {
          setIsOpen(true);
        }
      } else {
        setIsOpen(true);
      }
    }
  }, []);

  const savePreferences = (prefs: CookiePreferences) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(prefs));
      setPreferences(prefs);
      setIsOpen(false);
      setShowSettings(false);
    }
  };

  const handleAcceptAll = () => {
    const allAccepted: CookiePreferences = {
      necessary: true,
      analytics: true,
      marketing: true,
      timestamp: Date.now(),
    };
    savePreferences(allAccepted);
  };

  const handleRejectAll = () => {
    const onlyNecessary: CookiePreferences = {
      necessary: true,
      analytics: false,
      marketing: false,
      timestamp: Date.now(),
    };
    savePreferences(onlyNecessary);
  };

  const handleSavePreferences = () => {
    savePreferences(preferences);
  };

  const updatePreference = (key: keyof CookiePreferences, value: boolean) => {
    if (key === 'necessary') return; // Cannot disable necessary cookies
    setPreferences((prev) => ({ ...prev, [key]: value }));
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Cookie Banner */}
      <div
        className={cn(
          'fixed bottom-0 left-0 right-0 z-50 bg-background border-t shadow-2xl',
          'animate-in slide-in-from-bottom duration-300',
          isOpen ? 'block' : 'hidden'
        )}
      >
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex-1 space-y-2">
              <h3 className="font-headline text-lg font-semibold">
                <TranslatedText fr="Gestion des cookies" en="Cookie Management">
                  Cookie-Verwaltung
                </TranslatedText>
              </h3>
              <p className="text-sm text-muted-foreground max-w-2xl">
                <TranslatedText
                  fr="Nous utilisons des cookies pour améliorer votre expérience, analyser le trafic et personnaliser le contenu. Vous pouvez accepter tous les cookies ou personnaliser vos préférences."
                  en="We use cookies to enhance your experience, analyze traffic, and personalize content. You can accept all cookies or customize your preferences."
                >
                  Wir verwenden Cookies, um Ihr Erlebnis zu verbessern, den Datenverkehr zu analysieren und Inhalte zu personalisieren. Sie können alle Cookies akzeptieren oder Ihre Einstellungen anpassen.
                </TranslatedText>
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(true)}
                className="whitespace-nowrap"
              >
                <Settings className="mr-2 h-4 w-4" />
                <TranslatedText fr="Paramètres" en="Settings">
                  Einstellungen
                </TranslatedText>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRejectAll}
                className="whitespace-nowrap"
              >
                <TranslatedText fr="Refuser" en="Reject">
                  Ablehnen
                </TranslatedText>
              </Button>
              <Button
                size="sm"
                onClick={handleAcceptAll}
                className="whitespace-nowrap"
              >
                <TranslatedText fr="Tout accepter" en="Accept All">
                  Alle akzeptieren
                </TranslatedText>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-headline text-2xl">
              <TranslatedText fr="Paramètres des cookies" en="Cookie Settings">
                Cookie-Einstellungen
              </TranslatedText>
            </DialogTitle>
            <DialogDescription>
              <TranslatedText
                fr="Gérez vos préférences de cookies. Vous pouvez activer ou désactiver différents types de cookies ci-dessous."
                en="Manage your cookie preferences. You can enable or disable different types of cookies below."
              >
                Verwalten Sie Ihre Cookie-Einstellungen. Sie können verschiedene Cookie-Typen unten aktivieren oder deaktivieren.
              </TranslatedText>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Necessary Cookies */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="necessary" className="text-base font-semibold">
                    <TranslatedText fr="Cookies nécessaires" en="Necessary Cookies">
                      Notwendige Cookies
                    </TranslatedText>
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    <TranslatedText
                      fr="Ces cookies sont essentiels au fonctionnement du site et ne peuvent pas être désactivés."
                      en="These cookies are essential for the website to function and cannot be disabled."
                    >
                      Diese Cookies sind für die Funktionalität der Website unerlässlich und können nicht deaktiviert werden.
                    </TranslatedText>
                  </p>
                </div>
                <Switch
                  id="necessary"
                  checked={preferences.necessary}
                  disabled
                  className="opacity-50"
                />
              </div>
            </div>

            <Separator />

            {/* Analytics Cookies */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5 flex-1 mr-4">
                  <Label htmlFor="analytics" className="text-base font-semibold">
                    <TranslatedText fr="Cookies analytiques" en="Analytics Cookies">
                      Analyse-Cookies
                    </TranslatedText>
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    <TranslatedText
                      fr="Ces cookies nous aident à comprendre comment les visiteurs interagissent avec notre site en collectant des informations anonymes."
                      en="These cookies help us understand how visitors interact with our site by collecting anonymous information."
                    >
                      Diese Cookies helfen uns zu verstehen, wie Besucher mit unserer Website interagieren, indem sie anonyme Informationen sammeln.
                    </TranslatedText>
                  </p>
                </div>
                <Switch
                  id="analytics"
                  checked={preferences.analytics}
                  onCheckedChange={(checked) => updatePreference('analytics', checked)}
                />
              </div>
            </div>

            <Separator />

            {/* Marketing Cookies */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5 flex-1 mr-4">
                  <Label htmlFor="marketing" className="text-base font-semibold">
                    <TranslatedText fr="Cookies marketing" en="Marketing Cookies">
                      Marketing-Cookies
                    </TranslatedText>
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    <TranslatedText
                      fr="Ces cookies sont utilisés pour vous montrer des publicités pertinentes et mesurer l'efficacité de nos campagnes marketing."
                      en="These cookies are used to show you relevant advertisements and measure the effectiveness of our marketing campaigns."
                    >
                      Diese Cookies werden verwendet, um Ihnen relevante Werbung anzuzeigen und die Effektivität unserer Marketingkampagnen zu messen.
                    </TranslatedText>
                  </p>
                </div>
                <Switch
                  id="marketing"
                  checked={preferences.marketing}
                  onCheckedChange={(checked) => updatePreference('marketing', checked)}
                />
              </div>
            </div>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={handleRejectAll}
              className="w-full sm:w-auto"
            >
              <TranslatedText fr="Tout refuser" en="Reject All">
                Alle ablehnen
              </TranslatedText>
            </Button>
            <Button
              variant="outline"
              onClick={handleAcceptAll}
              className="w-full sm:w-auto"
            >
              <TranslatedText fr="Tout accepter" en="Accept All">
                Alle akzeptieren
              </TranslatedText>
            </Button>
            <Button
              onClick={handleSavePreferences}
              className="w-full sm:w-auto"
            >
              <TranslatedText fr="Enregistrer les préférences" en="Save Preferences">
                Einstellungen speichern
              </TranslatedText>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

