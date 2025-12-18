
'use client';

import Link from 'next/link';
import { Menu, Heart } from 'lucide-react';
import { useState } from 'react';

import { categories } from '@/lib/data';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { TranslatedText } from './TranslatedText';
import { SearchDialog } from './search/SearchDialog';
import { Separator } from './ui/separator';
import { LanguageSwitcher } from './LanguageSwitcher';
import { CartButton } from './cart/CartButton';
import { UserButton } from './auth/UserButton';
import { ThemeToggle } from './ThemeToggle';

export function Header() {
  const [isSheetOpen, setIsSheetOpen] = useState(false);

  const handleLinkClick = () => {
    setIsSheetOpen(false);
  };

  const handleFooterActionClick = () => {
    // We want the dropdowns inside to open, but not immediately close the sheet.
    // The sheet should close when an item *inside* the dropdown is selected.
    // For now, let's assume clicking the trigger should close it.
    // A better UX might be to pass the `setIsSheetOpen` to the components themselves.
  };


  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-20 items-center">
        <div className="flex flex-1 items-center justify-start">
          <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">
                  <TranslatedText fr="Ouvrir le menu" en="Toggle menu">
                    Menü umschalten
                  </TranslatedText>
                </span>
              </Button>
            </SheetTrigger>
            <SheetContent
              side="left"
              className="flex w-[300px] flex-col bg-background p-0 sm:w-[350px]"
            >
              {/* Visually hidden title for accessibility */}
              <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
              <header className="border-b p-6">
                <Link
                  href="/"
                  className="flex items-center space-x-2"
                  onClick={handleLinkClick}
                >
                  <span className="font-bold font-headline text-2xl">
                    EZCENTIALS
                  </span>
                </Link>
              </header>
              <main className="flex-grow overflow-y-auto p-6">
                <nav>
                  <ul className="flex flex-col space-y-6">
                    {categories.map((category) => (
                      <li key={category.id} className="space-y-2">
                        <Link
                          href={`/products/${category.slug}`}
                          className="text-xl text-foreground/80 transition-colors hover:text-foreground font-semibold"
                          onClick={handleLinkClick}
                          prefetch={true}
                        >
                          <TranslatedText
                            fr={category.name_fr}
                            en={category.name_en}
                          >
                            {category.name}
                          </TranslatedText>
                        </Link>
                        {category.subcategories && category.subcategories.length > 0 && (
                          <ul className="ml-4 mt-2 flex flex-col space-y-2 border-l border-border pl-4">
                            {category.subcategories.map((subcategory) => (
                              <li key={subcategory.id}>
                                <Link
                                  href={`/products/${category.slug}/${subcategory.slug}`}
                                  className="text-base text-foreground/70 transition-colors hover:text-foreground"
                                  onClick={handleLinkClick}
                                  prefetch={true}
                                >
                                  <TranslatedText
                                    fr={subcategory.name_fr}
                                    en={subcategory.name_en}
                                  >
                                    {subcategory.name}
                                  </TranslatedText>
                                </Link>
                              </li>
                            ))}
                          </ul>
                        )}
                      </li>
                    ))}
                  </ul>
                </nav>
              </main>
              <footer className="border-t p-6">
                <div className="flex items-center justify-between" onClick={() => setIsSheetOpen(false)}>
                   <UserButton />
                   <LanguageSwitcher />
                </div>
              </footer>
            </SheetContent>
          </Sheet>

          <div className="hidden lg:flex lg:items-center">
            <Link href="/" className="flex items-center space-x-2">
              <span className="font-bold font-headline text-2xl tracking-wider">
                EZCENTIALS
              </span>
            </Link>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center lg:hidden">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold font-headline text-2xl tracking-wider">
              EZCENTIALS
            </span>
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-end space-x-1 md:space-x-2 shrink-0 flex-nowrap">
          <nav className="hidden lg:flex lg:items-center lg:space-x-6 text-sm font-medium">
            {categories.map((category) => (
              <Link
                key={category.id}
                href={`/products/${category.slug}`}
                className="transition-colors hover:text-primary text-foreground/80"
                prefetch={true}
              >
                <TranslatedText fr={category.name_fr} en={category.name_en}>
                  {category.name}
                </TranslatedText>
              </Link>
            ))}
          </nav>
          <div className="hidden lg:flex items-center">
            <Separator orientation="vertical" className="h-6 mx-2" />
            <LanguageSwitcher />
            <Separator orientation="vertical" className="h-6 mx-2" />
            <ThemeToggle />
          </div>
          
          <SearchDialog />
           <Button variant="ghost" size="icon" asChild>
            <Link href="/favorites">
                <Heart className="h-5 w-5" />
                <span className="sr-only">
                    <TranslatedText fr="Favoris" en="Favorites">
                        Favoriten
                    </TranslatedText>
                </span>
            </Link>
          </Button>
          <div className="hidden md:flex">
             <UserButton />
          </div>
          <CartButton />
        </div>
      </div>
    </header>
  );
}
