
import Link from 'next/link';
import Image from 'next/image';
import placeholderImagesData from '@/lib/placeholder-images.json';
import { ArrowRight } from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo } from 'react';

type CategoryCardProps = {
    pretitle: ReactNode;
    title: ReactNode;
    description: ReactNode;
    linkText: ReactNode;
    href: string;
    imageId: string;
};

const { placeholderImages } = placeholderImagesData;

export function CategoryCard({ pretitle, title, description, linkText, href, imageId }: CategoryCardProps) {
    const image = useMemo(() => 
        placeholderImages.find((img) => img.id === imageId),
        [imageId]
    );

    if (!image) {
        return null;
    }

    return (
        <Link href={href} className="group relative block aspect-[3/4] w-full overflow-hidden">
            <Image
                src={image.imageUrl}
                alt={title?.toString() || 'Category'}
                fill
                sizes="(max-width: 768px) 80vw, (max-width: 1200px) 50vw, 33vw"
                className="object-cover transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
                data-ai-hint={image.imageHint}
            />
            <div className="absolute inset-0 bg-black/40" />
            <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-8 text-white">
                <p className="text-xs md:text-sm uppercase tracking-widest">{pretitle}</p>
                <h3 className="mt-2 font-headline text-3xl md:text-4xl">{title}</h3>
                <p className="mt-2 max-w-xs text-sm text-white/90">{description}</p>
                <div className="mt-4 md:mt-6 flex items-center gap-2 text-xs md:text-sm font-semibold uppercase tracking-wider transition-transform duration-300 group-hover:translate-x-2">
                    {linkText} <ArrowRight className="h-4 w-4" />
                </div>
            </div>
        </Link>
    );
}
