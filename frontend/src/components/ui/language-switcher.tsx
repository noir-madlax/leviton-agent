'use client';

import { useTranslation } from 'react-i18next';
import { supportedLngs, languageConfig } from '@/i18n/config';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLang = i18n.language;

  const switchLanguage = (newLang: string) => {
    i18n.changeLanguage(newLang);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm">
          <Globe className="h-4 w-4 mr-2" />
          {languageConfig[currentLang as keyof typeof languageConfig]?.label || 'English'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {supportedLngs.map((lang) => (
          <DropdownMenuItem
            key={lang}
            onClick={() => switchLanguage(lang)}
            className={currentLang === lang ? 'bg-accent' : ''}
          >
            <span className="mr-2">
              {languageConfig[lang as keyof typeof languageConfig]?.flag}
            </span>
            {languageConfig[lang as keyof typeof languageConfig]?.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 