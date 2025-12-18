#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour importer les accessoires hommes depuis faguo_store.com
Remplace les produits existants dans la sous-catégorie accessoires-homme
"""

import json
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
import time

# Configuration
SOURCE_SITE = "https://www.faguo-store.com"  # Site e-commerce Faguo
PRODUCTS_DIR = "public/images/products"
NEW_PRODUCTS_FILE = "new_products.json"
PLACEHOLDER_IMAGES_FILE = "src/lib/placeholder-images.json"

def clean_filename(name):
    """Nettoie un nom pour en faire un nom de fichier valide"""
    name = name.lower()
    name = re.sub(r'[^a-z0-9\-_]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name

def download_image(url, filepath):
    """Télécharge une image depuis une URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  ✗ Erreur image {url}: {e}")
        return False

def scrape_products():
    """Scrape les produits depuis faguo_store.com"""
    print(f"🔍 Scraping des accessoires hommes depuis {SOURCE_SITE}...\n")
    
    products = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        # Essayer l'API JSON Shopify
        api_urls = [
            f"{SOURCE_SITE}/products.json",
            f"{SOURCE_SITE}/collections/all/products.json",
            f"{SOURCE_SITE}/collections/homme/products.json",
            f"{SOURCE_SITE}/collections/accessoires-homme/products.json",
            f"{SOURCE_SITE}/collections/accessoires/products.json",
        ]
        
        for api_url in api_urls:
            try:
                print(f"  Tentative API: {api_url}")
                session = requests.Session()
                session.headers.update(headers)
                response = session.get(api_url, timeout=30, allow_redirects=True)
                if response.status_code == 200:
                    data = response.json()
                    if 'products' in data:
                        print(f"  ✓ {len(data['products'])} produits trouvés via API\n")
                        for product_data in data['products']:
                            product = parse_shopify_product(product_data)
                            if product:
                                products.append(product)
                        return products
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Erreur API: {type(e).__name__}")
                time.sleep(1)
                continue
            except Exception as e:
                print(f"  ✗ Erreur API: {e}")
                continue
        
        # Si l'API ne fonctionne pas, scraper HTML
        print("  Tentative scraping HTML...")
        urls_to_try = [
            f"{SOURCE_SITE}/collections/accessoires-homme",
            f"{SOURCE_SITE}/collections/homme-accessoires",
            f"{SOURCE_SITE}/collections/homme",
            f"{SOURCE_SITE}/collections/all",
            f"{SOURCE_SITE}/collections/accessoires",
            f"{SOURCE_SITE}/products",
            f"{SOURCE_SITE}",
        ]
        
        session = requests.Session()
        session.headers.update(headers)
        
        # D'abord, accéder à la page d'accueil pour obtenir les cookies
        try:
            print(f"  Accès à la page d'accueil pour obtenir les cookies...")
            home_response = session.get(SOURCE_SITE, timeout=30, allow_redirects=True)
            print(f"  ✓ Page d'accueil chargée (status: {home_response.status_code})")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠ Erreur page d'accueil: {e}")
        
        for url in urls_to_try:
            try:
                print(f"  Tentative HTML: {url}")
                response = session.get(url, timeout=30, allow_redirects=True)
                print(f"  Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"  ✗ Status non-200: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher les liens produits de différentes manières
                product_links = soup.find_all('a', href=re.compile(r'/product|/p/', re.I))
                
                # Chercher aussi des liens avec des patterns différents
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    # Patterns possibles pour les produits
                    if any(pattern in href.lower() for pattern in ['/product', '/p/', '/item', '/article']):
                        if href not in [l.get('href') for l in product_links]:
                            product_links.append(link)
                
                # Aussi chercher dans les divs avec des classes produit
                product_divs = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'product|item|card|grid', re.I))
                for div in product_divs:
                    link = div.find('a', href=True)
                    if link and link not in product_links:
                        product_links.append(link)
                
                # Chercher des données dans les scripts JSON-LD ou dans window.__INITIAL_STATE__
                scripts = soup.find_all('script')
                for script in scripts:
                    script_text = script.string or ''
                    # Chercher des URLs de produits dans les scripts
                    if 'product' in script_text.lower() or '/p/' in script_text:
                        # Essayer d'extraire des URLs
                        urls = re.findall(r'["\'](https?://[^"\']*product[^"\']*)["\']', script_text, re.I)
                        urls += re.findall(r'["\'](/[^"\']*product[^"\']*)["\']', script_text, re.I)
                        for url in urls:
                            if url not in [l.get('href') for l in product_links]:
                                from bs4 import Tag
                                fake_link = Tag(name='a', attrs={'href': url})
                                product_links.append(fake_link)
                
                print(f"  Trouvé {len(product_links)} liens produits potentiels")
                
                if not product_links:
                    # Essayer de trouver des données JSON dans la page
                    scripts = soup.find_all('script', type='application/json')
                    for script in scripts:
                        try:
                            data = json.loads(script.string)
                            if 'products' in str(data).lower():
                                print(f"  ✓ Données JSON trouvées dans la page")
                                # Essayer d'extraire les produits
                                if isinstance(data, dict) and 'products' in data:
                                    for prod in data['products']:
                                        product = parse_shopify_product(prod)
                                        if product and is_accessoire_homme(product):
                                            products.append(product)
                        except:
                            pass
                
                seen_urls = set()
                for link in product_links:
                    href = link.get('href', '')
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    product_url = urljoin(SOURCE_SITE, href)
                    if '/product' in product_url.lower():
                        product = scrape_product_page(product_url)
                        if product and is_accessoire_homme(product):
                            products.append(product)
                            print(f"  ✓ Produit ajouté: {product.get('name', '')[:50]}")
                            time.sleep(0.5)
                        if len(products) >= 200:
                            break
                if products:
                    break
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Erreur connexion: {type(e).__name__} - {e}")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                import traceback
                traceback.print_exc()
                continue
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
    
    return products

def is_accessoire_homme(product):
    """Vérifie si le produit est un accessoire pour homme"""
    name = product.get('name', '').lower()
    category = product.get('category', '').lower()
    description = product.get('description', '').lower()
    tags = product.get('tags', '').lower()
    
    text = name + " " + category + " " + description + " " + tags
    
    # Mots-clés pour accessoires
    accessoire_keywords = ['accessoire', 'accessory', 'sac', 'bag', 'portefeuille', 'wallet', 
                          'ceinture', 'belt', 'montre', 'watch', 'lunettes', 'glasses',
                          'chapeau', 'hat', 'casquette', 'cap', 'écharpe', 'scarf']
    
    # Mots-clés pour homme
    homme_keywords = ['homme', 'man', 'men', 'mens', 'masculin', 'masculine', 'gentleman']
    
    # Mots-clés à exclure (femme)
    femme_keywords = ['femme', 'woman', 'women', 'ladies', 'féminin', 'feminine']
    
    # Vérifier que c'est pour homme
    is_homme = any(keyword in text for keyword in homme_keywords)
    is_femme = any(keyword in text for keyword in femme_keywords)
    
    if is_femme and not is_homme:
        return False
    
    # Vérifier que c'est un accessoire
    is_accessoire = any(keyword in text for keyword in accessoire_keywords)
    
    # Si c'est clairement pour homme et un accessoire
    if is_homme and is_accessoire:
        return True
    
    # Si c'est dans une catégorie accessoires et pas explicitement pour femme
    if 'accessoire' in category and not is_femme:
        return True
    
    return False

def parse_shopify_product(product_data):
    """Parse un produit depuis l'API Shopify"""
    try:
        name = product_data.get('title', '')
        if not name or len(name) < 3:
            return None
        
        # Vérifier si c'est un accessoire homme
        product_type = product_data.get('product_type', '')
        tags = ' '.join(product_data.get('tags', []))
        
        # Prix
        variants = product_data.get('variants', [])
        price = 0
        old_price = None
        if variants:
            price = int(float(variants[0].get('price', 0)))
            compare_at_price = variants[0].get('compare_at_price')
            if compare_at_price:
                old_price = int(float(compare_at_price))
        
        # Description
        description = product_data.get('body_html', '')
        if description:
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text(strip=True)
        
        # Images
        images = product_data.get('images', [])
        image_urls = []
        if images:
            for img in images:
                img_url = img.get('src', '')
                if img_url and not img_url.startswith('http'):
                    img_url = 'https:' + img_url
                if img_url:
                    image_urls.append(img_url)
        
        return {
            'name': name,
            'price': price,
            'old_price': old_price,
            'image_urls': image_urls,
            'description': description,
            'category': product_type,
            'tags': tags,
            'handle': product_data.get('handle', '')
        }
    except Exception as e:
        print(f"  Erreur parsing produit: {e}")
        return None

def scrape_product_page(url):
    """Scrape une page produit individuelle"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Referer': SOURCE_SITE,
        }
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Nom
        name_elem = soup.find('h1', class_=re.compile(r'title|name|product', re.I))
        if not name_elem:
            name_elem = soup.find('h1')
        name = name_elem.get_text(strip=True) if name_elem else None
        
        if not name or len(name) < 3:
            return None
        
        # Prix
        price = 0
        old_price = None
        price_elem = soup.find(['span', 'div'], class_=re.compile(r'price', re.I))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price = extract_price(price_text)
        
        # Description
        description = ""
        desc_elem = soup.find(['div', 'section'], class_=re.compile(r'description|content', re.I))
        if desc_elem:
            desc_paras = desc_elem.find_all('p')
            if desc_paras:
                description = ' '.join([p.get_text(strip=True) for p in desc_paras[:3]])
            else:
                description = desc_elem.get_text(strip=True)
        
        # Images
        image_urls = []
        img_elems = soup.find_all('img', class_=re.compile(r'product|main', re.I))
        for img_elem in img_elems:
            src = img_elem.get('src') or img_elem.get('data-src')
            if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                image_urls.append(urljoin(SOURCE_SITE, src))
        
        # Catégorie
        category = ''
        breadcrumb = soup.find(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb', re.I))
        if breadcrumb:
            links = breadcrumb.find_all('a')
            if links:
                category = links[-1].get_text(strip=True)
        
        return {
            'name': name,
            'price': price,
            'old_price': old_price,
            'image_urls': image_urls,
            'description': description,
            'category': category,
            'tags': '',
            'url': url
        }
    except Exception as e:
        print(f"  Erreur scraping {url}: {e}")
        return None

def extract_price(price_text):
    """Extrait le prix d'un texte"""
    match = re.search(r'(\d+[.,]?\d*)', price_text.replace(' ', ''))
    if match:
        price_str = match.group(1).replace(',', '.')
        try:
            return int(float(price_str))
        except:
            return 0
    return 0

def create_product_entry(product_data, index):
    """Crée une entrée produit au format du site"""
    name = product_data['name']
    slug = clean_filename(name)
    
    # Catégorie fixe : accessoires-homme
    category = 'mens-clothing'
    subcategory = 'accessoires-homme'
    product_id = f'accessoires-homme-{index+1:03d}'
    
    # Noms multilingues
    name_fr = name
    name_en = name
    name_de = name
    
    # Descriptions
    description = product_data.get('description', f'Un accessoire élégant pour homme {name}')
    description_fr = description
    description_en = description
    description_de = description
    
    # Images
    image_urls = product_data.get('image_urls', [])
    image_ids = []
    if image_urls:
        for i, img_url in enumerate(image_urls[:3]):  # Max 3 images
            img_id = slug.replace('-', '_')
            if i > 0:
                img_id += f'_{i+1}'
            image_ids.append(img_id)
    else:
        image_ids = [slug.replace('-', '_')]
    
    product = {
        'id': product_id,
        'name': name_de,
        'name_fr': name_fr,
        'name_en': name_en,
        'slug': slug,
        'price': product_data.get('price', 0),
        'oldPrice': product_data.get('old_price'),
        'description': description_de,
        'description_fr': description_fr,
        'description_en': description_en,
        'category': category,
        'subcategory': subcategory,
        'images': image_ids,
        'sizes': None,
        'colors': None
    }
    
    return product, image_ids, image_urls

def main():
    print("🚀 Importation des accessoires hommes depuis faguo_store.com\n")
    print("⚠️  Cette opération va REMPLACER les produits existants dans accessoires-homme\n")
    
    # Scraper les produits
    products_data = scrape_products()
    
    if not products_data:
        print("\n❌ Aucun produit trouvé.")
        return
    
    print(f"\n✓ {len(products_data)} accessoires hommes trouvés\n")
    
    # Charger les produits existants
    try:
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            all_products = json.load(f)
    except:
        all_products = []
    
    # Supprimer les anciens produits accessoires-homme
    old_count = len([p for p in all_products if p.get('subcategory') == 'accessoires-homme'])
    all_products = [p for p in all_products if p.get('subcategory') != 'accessoires-homme']
    print(f"🗑️  {old_count} anciens produits accessoires-homme supprimés\n")
    
    # Charger les images existantes
    try:
        with open(PLACEHOLDER_IMAGES_FILE, 'r', encoding='utf-8') as f:
            placeholder_data = json.load(f)
            placeholder_images = placeholder_data.get('placeholderImages', [])
    except:
        placeholder_images = []
    
    # Supprimer les images des anciens produits accessoires-homme
    old_image_ids = {img.get('id') for img in placeholder_images if 'accessoires-homme' in img.get('description', '').lower() or any(p.get('subcategory') == 'accessoires-homme' and img.get('id') in p.get('images', []) for p in all_products)}
    placeholder_images = [img for img in placeholder_images if img.get('id') not in old_image_ids]
    
    # Traiter chaque nouveau produit
    new_products = []
    new_images = []
    existing_image_ids = {img.get('id') for img in placeholder_images}
    
    for i, product_data in enumerate(products_data):
        print(f"\n[{i+1}/{len(products_data)}] {product_data.get('name', '')[:60]}")
        
        # Créer l'entrée produit
        product, image_ids, image_urls = create_product_entry(product_data, i)
        
        # Télécharger les images
        for j, (image_id, image_url) in enumerate(zip(image_ids, image_urls)):
            if image_id in existing_image_ids:
                continue
            
            image_filename = f"{image_id}.jpg"
            image_path = os.path.join(PRODUCTS_DIR, image_filename)
            image_relative_path = f"/images/products/{image_filename}"
            
            if download_image(image_url, image_path):
                new_images.append({
                    'id': image_id,
                    'description': product['name_fr'],
                    'imageUrl': image_relative_path,
                    'imageHint': 'accessoire homme'
                })
                existing_image_ids.add(image_id)
                print(f"  ✓ Image {j+1} téléchargée: {image_id}")
        
        new_products.append(product)
    
    # Fusionner
    all_products = all_products + new_products
    
    # Vérifier la limite de 1100
    if len(all_products) > 1100:
        print(f"\n⚠️  Limite de 1100 produits dépassée! Limitation...")
        all_products = all_products[:1100]
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde de {len(new_products)} nouveaux produits accessoires-homme...")
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"✓ {NEW_PRODUCTS_FILE} mis à jour ({len(all_products)} produits au total)")
    
    # Fusionner les images
    all_images = placeholder_images + new_images
    
    print(f"\n💾 Sauvegarde de {len(new_images)} nouvelles images...")
    with open(PLACEHOLDER_IMAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump({'placeholderImages': all_images}, f, ensure_ascii=False, indent=2)
    print(f"✓ {PLACEHOLDER_IMAGES_FILE} mis à jour")
    
    print(f"\n✅ Importation terminée!")
    print(f"   - {old_count} anciens produits supprimés")
    print(f"   - {len(new_products)} nouveaux produits ajoutés")
    print(f"   - {len(new_images)} images téléchargées")
    print(f"   - Total: {len(all_products)} produits")

if __name__ == '__main__':
    main()

