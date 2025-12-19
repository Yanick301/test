import type { Metadata } from 'next';
import type { Product, Category } from './types';
import { products, categories } from './data';
import placeholderImagesData from './placeholder-images.json';

const { placeholderImages } = placeholderImagesData;
const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ezcentials.com';

export function generateProductMetadata(product: Product, language: string = 'de'): Metadata {
  const productName = language === 'fr' ? product.name_fr : language === 'en' ? product.name_en : product.name;
  const productDescription = language === 'fr' ? product.description_fr : language === 'en' ? product.description_en : product.description;
  
  const mainImage = placeholderImages.find(p => p.id === product.images[0]);
  const imageUrl = mainImage ? `${baseUrl}${mainImage.imageUrl}` : `${baseUrl}/images/logo.png`;

  return {
    title: productName,
    description: productDescription.substring(0, 160),
    keywords: [
      productName,
      product.category,
      'luxury fashion',
      'premium clothing',
      'boutique',
      'EZCENTIALS'
    ],
    openGraph: {
      type: 'product',
      locale: language === 'fr' ? 'fr_FR' : language === 'en' ? 'en_GB' : 'de_DE',
      title: productName,
      description: productDescription.substring(0, 160),
      images: [
        {
          url: imageUrl,
          width: 1200,
          height: 1600,
          alt: productName,
        },
      ],
      siteName: 'EZCENTIALS',
    },
    twitter: {
      card: 'summary_large_image',
      title: productName,
      description: productDescription.substring(0, 160),
      images: [imageUrl],
    },
    alternates: {
      canonical: `${baseUrl}/product/${product.slug}`,
      languages: {
        'de': `${baseUrl}/product/${product.slug}`,
        'fr': `${baseUrl}/product/${product.slug}`,
        'en': `${baseUrl}/product/${product.slug}`,
      },
    },
  };
}

export function generateCategoryMetadata(category: Category, language: string = 'de'): Metadata {
  const categoryName = language === 'fr' ? category.name_fr : language === 'en' ? category.name_en : category.name;
  
  const categoryImage = placeholderImages.find(p => p.id === category.imageId);
  const imageUrl = categoryImage ? `${baseUrl}${categoryImage.imageUrl}` : `${baseUrl}/images/logo.png`;

  return {
    title: categoryName,
    description: `Entdecken Sie unsere ${categoryName} Kollektion bei EZCENTIALS. Premium Mode und Accessoires.`,
    keywords: [
      categoryName,
      'luxury fashion',
      'premium clothing',
      'boutique',
      'EZCENTIALS',
      category.slug,
    ],
    openGraph: {
      type: 'website',
      locale: language === 'fr' ? 'fr_FR' : language === 'en' ? 'en_GB' : 'de_DE',
      title: categoryName,
      description: `Entdecken Sie unsere ${categoryName} Kollektion bei EZCENTIALS.`,
      images: [
        {
          url: imageUrl,
          width: 1200,
          height: 1600,
          alt: categoryName,
        },
      ],
      siteName: 'EZCENTIALS',
    },
    twitter: {
      card: 'summary_large_image',
      title: categoryName,
      description: `Entdecken Sie unsere ${categoryName} Kollektion bei EZCENTIALS.`,
      images: [imageUrl],
    },
    alternates: {
      canonical: `${baseUrl}/products/${category.slug}`,
    },
  };
}

export function generateProductStructuredData(product: Product, language: string = 'de'): object {
  const productName = language === 'fr' ? product.name_fr : language === 'en' ? product.name_en : product.name;
  const productDescription = language === 'fr' ? product.description_fr : language === 'en' ? product.description_en : product.description;
  
  const mainImage = placeholderImages.find(p => p.id === product.images[0]);
  const imageUrl = mainImage ? `${baseUrl}${mainImage.imageUrl}` : `${baseUrl}/images/logo.png`;

  const category = categories.find(c => c.slug === product.category);
  const categoryName = category 
    ? (language === 'fr' ? category.name_fr : language === 'en' ? category.name_en : category.name)
    : 'Fashion';

  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: productName,
    description: productDescription,
    image: imageUrl,
    brand: {
      '@type': 'Brand',
      name: 'EZCENTIALS',
    },
    category: categoryName,
    offers: {
      '@type': 'Offer',
      url: `${baseUrl}/product/${product.slug}`,
      priceCurrency: 'EUR',
      price: product.price.toString(),
      availability: 'https://schema.org/InStock',
      itemCondition: 'https://schema.org/NewCondition',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '5',
      reviewCount: '10',
    },
  };
}














