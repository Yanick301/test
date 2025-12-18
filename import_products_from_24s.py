#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour importer les produits depuis 24s.com
Récupère toutes les catégories, images, prix et descriptions
"""

import json
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
import time
from pathlib import Path

# Configuration
SOURCE_SITE = "https://24s.com"
PRODUCTS_DIR = "public/images/products"
NEW_PRODUCTS_FILE = "new_products.json"
PLACEHOLDER_IMAGES_FILE = "src/lib/placeholder-images.json"
MAX_TOTAL_PRODUCTS = 1100

# Mapping des catégories 24s vers les catégories du nouveau site
CATEGORY_MAPPING = {
    # Homme
    'homme': 'mens-clothing',
    'hommes': 'mens-clothing',
    'men': 'mens-clothing',
    'mens': 'mens-clothing',
    'chemise': 'mens-clothing',
    'chemises': 'mens-clothing',
    'shirt': 'mens-clothing',
    'shirts': 'mens-clothing',
    'pantalon': 'mens-clothing',
    'pantalons': 'mens-clothing',
    'trousers': 'mens-clothing',
    'veste': 'mens-clothing',
    'vestes': 'mens-clothing',
    'jacket': 'mens-clothing',
    'jackets': 'mens-clothing',
    'pull': 'mens-clothing',
    'pulls': 'mens-clothing',
    'sweater': 'mens-clothing',
    'sweaters': 'mens-clothing',
    
    # Femme
    'femme': 'womens-clothing',
    'femmes': 'womens-clothing',
    'women': 'womens-clothing',
    'womens': 'womens-clothing',
    'robe': 'womens-clothing',
    'robes': 'womens-clothing',
    'dress': 'womens-clothing',
    'dresses': 'womens-clothing',
    'top': 'womens-clothing',
    'tops': 'womens-clothing',
    'jupe': 'womens-clothing',
    'jupes': 'womens-clothing',
    'skirt': 'womens-clothing',
    'skirts': 'womens-clothing',
    
    # Accessoires
    'accessoire': 'accessories',
    'accessoires': 'accessories',
    'accessory': 'accessories',
    'accessories': 'accessories',
    'montre': 'accessories',
    'montres': 'accessories',
    'watch': 'accessories',
    'watches': 'accessories',
    'sac': 'accessories',
    'sacs': 'accessories',
    'bag': 'accessories',
    'bags': 'accessories',
    
    # Chaussures
    'chaussure': 'shoes',
    'chaussures': 'shoes',
    'shoe': 'shoes',
    'shoes': 'shoes',
    'bottine': 'shoes',
    'bottines': 'shoes',
    'boot': 'shoes',
    'boots': 'shoes',
    
    # Sport
    'sport': 'sport',
    'sports': 'sport',
    
    # Hiver
    'hiver': 'winter-clothing',
    'winter': 'winter-clothing',
    'doudoune': 'winter-clothing',
    'parka': 'winter-clothing',
    'manteau': 'winter-clothing',
}

# Mapping des sous-catégories
SUBCATEGORY_MAPPING = {
    # Homme
    'chemise': 'chemises-homme',
    'chemises': 'chemises-homme',
    'pantalon': 'pantalons-homme',
    'pantalons': 'pantalons-homme',
    'veste': 'vestes-homme',
    'vestes': 'vestes-homme',
    'pull': 'pulls-homme',
    'pulls': 'pulls-homme',
    'accessoire': 'accessoires-homme',
    'accessoires': 'accessoires-homme',
    
    # Femme
    'robe': 'robes-femme',
    'robes': 'robes-femme',
    'top': 'tops-femme',
    'tops': 'tops-femme',
    'pantalon': 'pantalons-femme',
    'pantalons': 'pantalons-femme',
    'jupe': 'jupes-femme',
    'jupes': 'jupes-femme',
    'veste': 'vestes-femme',
    'vestes': 'vestes-femme',
    'accessoire': 'accessoires-femme',
    'accessoires': 'accessoires-femme',
}

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

def map_category(category_name, subcategory_name=None):
    """Mappe une catégorie 24s vers une catégorie du nouveau site"""
    if not category_name:
        return 'accessories', None
    
    cat_lower = category_name.lower()
    
    # Chercher dans le mapping
    for key, mapped_cat in CATEGORY_MAPPING.items():
        if key in cat_lower:
            category = mapped_cat
            
            # Déterminer la sous-catégorie
            subcategory = None
            if subcategory_name:
                sub_lower = subcategory_name.lower()
                for key, mapped_sub in SUBCATEGORY_MAPPING.items():
                    if key in sub_lower:
                        # Vérifier que la sous-catégorie correspond à la catégorie
                        if (mapped_sub.startswith('accessoires') and category == 'accessories') or \
                           (mapped_sub.startswith('chemises') and category == 'mens-clothing') or \
                           (mapped_sub.startswith('pantalons') and category == 'mens-clothing') or \
                           (mapped_sub.startswith('vestes') and category == 'mens-clothing') or \
                           (mapped_sub.startswith('pulls') and category == 'mens-clothing') or \
                           (mapped_sub.startswith('robes') and category == 'womens-clothing') or \
                           (mapped_sub.startswith('tops') and category == 'womens-clothing') or \
                           (mapped_sub.startswith('jupes') and category == 'womens-clothing'):
                            subcategory = mapped_sub
                            break
            
            return category, subcategory
    
    # Par défaut
    return 'accessories', None

def determine_gender(category_name, subcategory_name, description, name):
    """Détermine le genre du produit"""
    text = (category_name + " " + subcategory_name + " " + description + " " + name).lower()
    
    femme_keywords = ['femme', 'woman', 'women', 'ladies', 'dame', 'dames', 'féminin', 'feminine']
    homme_keywords = ['homme', 'man', 'men', 'gentleman', 'herren', 'masculin', 'masculine']
    
    femme_score = sum(1 for keyword in femme_keywords if keyword in text)
    homme_score = sum(1 for keyword in homme_keywords if keyword in text)
    
    if femme_score > homme_score:
        return 'femme'
    elif homme_score > femme_score:
        return 'homme'
    return 'unisex'

def scrape_products():
    """Scrape les produits depuis 24s.com"""
    print(f"🔍 Scraping des produits depuis {SOURCE_SITE}...\n")
    
    products = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Essayer l'API JSON Shopify
        api_urls = [
            f"{SOURCE_SITE}/products.json",
            f"{SOURCE_SITE}/collections/all/products.json",
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
                time.sleep(2)  # Pause avant réessai
                continue
            except Exception as e:
                print(f"  ✗ Erreur API: {e}")
                continue
        
        # Si l'API ne fonctionne pas, scraper HTML
        print("  Tentative scraping HTML...")
        urls_to_try = [
            f"{SOURCE_SITE}/collections/all",
            f"{SOURCE_SITE}/products",
            f"{SOURCE_SITE}",
        ]
        
        for url in urls_to_try:
            try:
                session = requests.Session()
                session.headers.update(headers)
                response = session.get(url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher les liens produits
                product_links = soup.find_all('a', href=re.compile(r'/product', re.I))
                print(f"  Trouvé {len(product_links)} liens produits")
                
                seen_urls = set()
                for link in product_links:
                    href = link.get('href', '')
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    product_url = urljoin(SOURCE_SITE, href)
                    if '/product' in product_url.lower():
                        product = scrape_product_page(product_url)
                        if product:
                            products.append(product)
                            time.sleep(0.5)
                        if len(products) >= 500:
                            break
                break
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Erreur connexion: {type(e).__name__}")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
    
    return products

def parse_shopify_product(product_data):
    """Parse un produit depuis l'API Shopify"""
    try:
        name = product_data.get('title', '')
        if not name or len(name) < 3:
            return None
        
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
        
        # Catégorie et sous-catégorie depuis les tags ou le type
        product_type = product_data.get('product_type', '')
        tags = ' '.join(product_data.get('tags', []))
        category_name = product_type or tags
        
        # Déterminer le genre
        gender = determine_gender(category_name, '', description, name)
        
        # Mapper la catégorie
        category, subcategory = map_category(category_name, '')
        
        # Ajuster selon le genre si nécessaire
        if gender == 'femme' and category == 'mens-clothing':
            category = 'womens-clothing'
        elif gender == 'homme' and category == 'womens-clothing':
            category = 'mens-clothing'
        
        return {
            'name': name,
            'price': price,
            'old_price': old_price,
            'image_urls': image_urls,
            'description': description,
            'category': category,
            'subcategory': subcategory,
            'gender': gender,
            'product_type': product_type,
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
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
        category = 'accessories'
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
            'subcategory': None,
            'gender': 'unisex',
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

def create_product_entry(product_data, index, gender):
    """Crée une entrée produit au format du site"""
    name = product_data['name']
    slug = clean_filename(name)
    
    # Utiliser le genre du product_data si disponible
    if 'gender' in product_data:
        gender = product_data['gender']
    
    # Catégorie et sous-catégorie
    category = product_data.get('category', 'accessories')
    subcategory = product_data.get('subcategory')
    
    # Générer l'ID
    if category == 'womens-clothing' and subcategory:
        product_id = f'{subcategory}-{index+1:03d}'
    elif category == 'mens-clothing' and subcategory:
        product_id = f'{subcategory}-{index+1:03d}'
    elif category == 'accessories':
        if gender == 'femme':
            product_id = f'accessoires-femme-{index+1:03d}'
            subcategory = 'accessoires-femme'
            category = 'womens-clothing'
        elif gender == 'homme':
            product_id = f'accessoires-homme-{index+1:03d}'
            subcategory = 'accessoires-homme'
            category = 'mens-clothing'
        else:
            product_id = f'accessoires-{index+1:03d}'
    else:
        product_id = f'{category.replace("-", "_")}-{index+1:03d}'
    
    # Noms multilingues (basique)
    name_fr = name
    name_en = name
    name_de = name
    
    # Descriptions multilingues
    description = product_data.get('description', f'Un produit élégant {name}')
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
    print("🚀 Début de l'importation des produits depuis 24s.com\n")
    
    # Vérifier le nombre actuel de produits
    try:
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
        current_count = len(existing_products)
        print(f"📊 Produits actuels: {current_count}")
        remaining = MAX_TOTAL_PRODUCTS - current_count
        print(f"📊 Produits restants: {remaining}")
        print(f"📊 Limite maximale: {MAX_TOTAL_PRODUCTS}\n")
        
        if remaining <= 0:
            print("⚠️  Limite de 1100 produits atteinte!")
            print("   Utilisez limit_products_to_1100.py pour nettoyer si nécessaire.")
            return
    except:
        existing_products = []
        current_count = 0
        remaining = MAX_TOTAL_PRODUCTS
        print(f"📊 Produits actuels: 0")
        print(f"📊 Produits restants: {remaining}")
        print(f"📊 Limite maximale: {MAX_TOTAL_PRODUCTS}\n")
    
    # Scraper les produits
    products_data = scrape_products()
    
    if not products_data:
        print("\n❌ Aucun produit trouvé.")
        return
    
    print(f"\n✓ {len(products_data)} produits trouvés\n")
    
    # Limiter le nombre
    products_data = products_data[:remaining]
    print(f"📊 Limitation à {len(products_data)} produits pour respecter la limite\n")
    
    # Charger les images existantes
    try:
        with open(PLACEHOLDER_IMAGES_FILE, 'r', encoding='utf-8') as f:
            placeholder_data = json.load(f)
            placeholder_images = placeholder_data.get('placeholderImages', [])
    except:
        placeholder_images = []
    
    # Traiter chaque produit
    new_products = []
    new_images = []
    existing_image_ids = {img.get('id') for img in placeholder_images}
    
    for i, product_data in enumerate(products_data):
        print(f"\n[{i+1}/{len(products_data)}] {product_data.get('name', '')[:60]}")
        
        gender = product_data.get('gender', 'unisex')
        print(f"  Catégorie: {product_data.get('category', 'N/A')} | Genre: {gender}")
        
        # Créer l'entrée produit
        product, image_ids, image_urls = create_product_entry(product_data, i, gender)
        
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
                    'imageHint': product_data.get('product_type', 'product')
                })
                existing_image_ids.add(image_id)
                print(f"  ✓ Image {j+1} téléchargée: {image_id}")
        
        new_products.append(product)
    
    # Fusionner avec les produits existants
    all_products = existing_products + new_products
    
    # Vérifier la limite
    if len(all_products) > MAX_TOTAL_PRODUCTS:
        print(f"\n⚠️  Limite dépassée! Limitation à {MAX_TOTAL_PRODUCTS} produits")
        all_products = all_products[:MAX_TOTAL_PRODUCTS]
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde de {len(new_products)} nouveaux produits...")
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
    print(f"   - {len(new_products)} produits ajoutés")
    print(f"   - {len(new_images)} images téléchargées")
    print(f"   - Total: {len(all_products)}/{MAX_TOTAL_PRODUCTS} produits")

if __name__ == '__main__':
    main()

