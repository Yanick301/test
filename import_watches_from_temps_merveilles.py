#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour importer les montres depuis temps-et-merveilles.fr
Télécharge les images et les classe dans les bonnes catégories
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
SOURCE_SITE = "https://temps-et-merveilles.fr"  # Corrigez l'URL si nécessaire
PRODUCTS_DIR = "public/images/products"
NEW_PRODUCTS_FILE = "new_products.json"
PLACEHOLDER_IMAGES_FILE = "src/lib/placeholder-images.json"

def clean_filename(name):
    """Nettoie un nom pour en faire un nom de fichier valide"""
    # Convertir en minuscules et remplacer les espaces par des tirets
    name = name.lower()
    # Remplacer les caractères spéciaux
    name = re.sub(r'[^a-z0-9\-_]', '-', name)
    # Supprimer les tirets multiples
    name = re.sub(r'-+', '-', name)
    # Supprimer les tirets en début/fin
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
        print(f"  ✓ Image téléchargée: {filepath}")
        return True
    except Exception as e:
        print(f"  ✗ Erreur lors du téléchargement de {url}: {e}")
        return False

def determine_gender(description, name):
    """Détermine le genre de la montre basé sur la description et le nom"""
    text = (description + " " + name).lower()
    
    # Mots-clés pour femmes
    femme_keywords = ['femme', 'woman', 'women', 'ladies', 'dame', 'dames', 'féminin', 'feminine', 
                     'rose', 'pink', 'diamant', 'diamond', 'perle', 'pearl', 'délicat', 'delicate']
    
    # Mots-clés pour hommes
    homme_keywords = ['homme', 'man', 'men', 'gentleman', 'herren', 'masculin', 'masculine',
                     'sport', 'diver', 'plongée', 'aviation', 'pilot', 'militar']
    
    femme_score = sum(1 for keyword in femme_keywords if keyword in text)
    homme_score = sum(1 for keyword in homme_keywords if keyword in text)
    
    if femme_score > homme_score:
        return 'femme'
    elif homme_score > femme_score:
        return 'homme'
    else:
        # Par défaut, on met dans accessoires génériques
        return 'unisex'

def scrape_products():
    """Scrape les produits depuis le site"""
    print(f"🔍 Scraping des produits depuis {SOURCE_SITE}...")
    
    products = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Pour Shopify, essayer l'API JSON
        api_urls = [
            f"{SOURCE_SITE}/products.json",
            f"{SOURCE_SITE}/collections/all/products.json",
        ]
        
        for api_url in api_urls:
            try:
                print(f"  Tentative API: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'products' in data:
                        print(f"  ✓ {len(data['products'])} produits trouvés via API")
                        for product_data in data['products']:
                            product = parse_shopify_product(product_data)
                            if product:
                                products.append(product)
                        return products
            except:
                continue
        
        # Si l'API ne fonctionne pas, essayer le scraping HTML
        urls_to_try = [
            f"{SOURCE_SITE}/collections/all",
            f"{SOURCE_SITE}/products",
            f"{SOURCE_SITE}/collections/montres",
            f"{SOURCE_SITE}",
        ]
        
        html_content = None
        for url in urls_to_try:
            try:
                print(f"  Tentative HTML: {url}")
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                html_content = response.text
                print(f"  ✓ Page récupérée: {url}")
                break
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                continue
        
        if not html_content:
            print("❌ Impossible d'accéder au site. Vérifiez l'URL et votre connexion.")
            return products
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Chercher les produits - différentes structures possibles
        product_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'product|item|card', re.I))
        
        if not product_elements:
            # Essayer de trouver des liens produits
            product_links = soup.find_all('a', href=re.compile(r'/product', re.I))
            print(f"  Trouvé {len(product_links)} liens produits potentiels")
            
            seen_urls = set()
            for link in product_links:
                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue
                # Nettoyer l'URL
                if href.startswith('/'):
                    href = href
                elif not href.startswith('http'):
                    continue
                
                seen_urls.add(href)
                product_url = urljoin(SOURCE_SITE, href)
                if '/product' in product_url.lower():
                    product = scrape_product_page(product_url)
                    if product and is_valid_product(product.get('name', ''), product_url):
                        products.append(product)
                        print(f"  ✓ Produit ajouté: {product.get('name', '')[:50]}")
                        time.sleep(1)  # Pause pour ne pas surcharger le serveur
                    if len(products) >= 200:  # Limiter à 200 produits
                        break
        else:
            print(f"  Trouvé {len(product_elements)} éléments produits")
            seen_urls = set()
            for element in product_elements:
                product = extract_product_from_element(element)
                if product:
                    # Éviter les doublons
                    product_url = product.get('url', '')
                    if product_url and product_url in seen_urls:
                        continue
                    if product_url:
                        seen_urls.add(product_url)
                    products.append(product)
                    if len(products) >= 200:  # Limiter à 200 produits
                        break
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
    
    return products

def parse_shopify_product(product_data):
    """Parse un produit depuis l'API Shopify"""
    try:
        name = product_data.get('title', 'Montre')
        
        # Prix
        variants = product_data.get('variants', [])
        price = 0
        if variants:
            price = int(float(variants[0].get('price', 0)) * 100)  # Convertir en centimes puis en euros
        
        # Description
        description = product_data.get('body_html', '')
        # Nettoyer le HTML
        if description:
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text(strip=True)
        
        # Image
        images = product_data.get('images', [])
        image_url = None
        if images:
            image_url = images[0].get('src', '')
            if image_url and not image_url.startswith('http'):
                image_url = 'https:' + image_url
        
        # URL
        handle = product_data.get('handle', '')
        url = f"{SOURCE_SITE}/products/{handle}" if handle else None
        
        # Tags pour déterminer le genre
        tags = product_data.get('tags', '')
        gender = determine_gender(description + " " + tags, name)
        
        return {
            'name': name,
            'price': price,
            'image_url': image_url,
            'url': url,
            'description': description,
            'gender': gender
        }
    except Exception as e:
        print(f"  Erreur parsing produit: {e}")
        return None

def is_valid_product(name, url):
    """Vérifie si c'est un vrai produit (pas un élément de navigation)"""
    if not name or len(name.strip()) < 3:
        return False
    
    # Exclure les éléments de navigation
    excluded_keywords = [
        'acceuil', 'accueil', 'boutique', 'contact', 'blog', 'à propos', 'a propos',
        'information', 'emplacement', 'apprenez', 'notre', 'nous', 'connaître',
        'panier', 'loading', 'done', 'ajouter', 'produit en vente', '%',
        '📞', 'phone', 'téléphone', 'tel:', 'mailto:', 'facebook', 'instagram'
    ]
    
    name_lower = name.lower()
    for keyword in excluded_keywords:
        if keyword in name_lower:
            return False
    
    # Vérifier que l'URL est une vraie page produit
    if url and '/product' in url.lower():
        return True
    
    # Si pas d'URL mais nom valide (au moins 5 caractères et contient des lettres)
    if len(name) >= 5 and re.search(r'[a-zA-Z]', name):
        return True
    
    return False

def extract_product_from_element(element):
    """Extrait les informations d'un produit depuis un élément HTML"""
    try:
        # Chercher le nom
        name_elem = element.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|product', re.I))
        if not name_elem:
            name_elem = element.find('a')
        name = name_elem.get_text(strip=True) if name_elem else ""
        
        # Chercher le lien
        link_elem = element.find('a', href=True)
        product_url = None
        if link_elem:
            href = link_elem.get('href', '')
            if href and '/product' in href.lower():
                product_url = urljoin(SOURCE_SITE, href)
        
        # Vérifier si c'est un vrai produit
        if not is_valid_product(name, product_url):
            return None
        
        # Si on a une URL produit, scraper la page complète
        if product_url:
            return scrape_product_page(product_url)
        
        # Sinon, essayer d'extraire depuis l'élément
        # Chercher le prix
        price_elem = element.find(['span', 'div'], class_=re.compile(r'price', re.I))
        price_text = price_elem.get_text(strip=True) if price_elem else "0"
        price = extract_price(price_text)
        
        # Chercher l'image
        img_elem = element.find('img')
        image_url = None
        if img_elem:
            image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
            if image_url:
                image_url = urljoin(SOURCE_SITE, image_url)
        
        return {
            'name': name,
            'price': price,
            'image_url': image_url,
            'url': product_url,
            'description': ''
        }
    except Exception as e:
        print(f"  Erreur extraction: {e}")
        return None

def scrape_product_page(url):
    """Scrape une page produit individuelle"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraire le nom - chercher dans plusieurs endroits
        name = None
        name_elem = soup.find('h1', class_=re.compile(r'title|name|product', re.I))
        if not name_elem:
            name_elem = soup.find('h1')
        if not name_elem:
            name_elem = soup.find(['h2', 'h3'], class_=re.compile(r'product', re.I))
        if name_elem:
            name = name_elem.get_text(strip=True)
        
        if not name or len(name) < 3:
            return None
        
        # Extraire le prix - chercher dans plusieurs endroits
        price = 0
        price_elem = soup.find(['span', 'div'], class_=re.compile(r'price', re.I))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price = extract_price(price_text)
        
        # Si pas de prix trouvé, chercher dans le texte de la page
        if price == 0:
            price_matches = re.findall(r'(\d+[.,]?\d*)\s*€', soup.get_text())
            if price_matches:
                try:
                    price = int(float(price_matches[0].replace(',', '.')))
                except:
                    pass
        
        # Extraire la description
        description = ""
        desc_elem = soup.find(['div', 'section'], class_=re.compile(r'description|content|details', re.I))
        if desc_elem:
            # Prendre plusieurs paragraphes
            desc_paras = desc_elem.find_all('p')
            if desc_paras:
                description = ' '.join([p.get_text(strip=True) for p in desc_paras[:3]])
            else:
                description = desc_elem.get_text(strip=True)
        
        # Si pas de description, chercher dans meta description
        if not description:
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
        
        # Extraire l'image principale - chercher la meilleure image
        image_url = None
        # Chercher dans les images avec des classes product
        img_elems = soup.find_all('img', class_=re.compile(r'product|main|featured|hero', re.I))
        if not img_elems:
            # Chercher toutes les images et prendre la plus grande
            img_elems = soup.find_all('img')
        
        for img_elem in img_elems:
            src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
            if src:
                # Éviter les logos et icônes
                if any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'placeholder']):
                    continue
                image_url = urljoin(SOURCE_SITE, src)
                break
        
        return {
            'name': name,
            'price': price,
            'image_url': image_url,
            'url': url,
            'description': description
        }
    except Exception as e:
        print(f"  Erreur scraping page {url}: {e}")
        return None

def extract_price(price_text):
    """Extrait le prix d'un texte"""
    # Chercher des nombres avec éventuellement des décimales
    match = re.search(r'(\d+[.,]?\d*)', price_text.replace(' ', ''))
    if match:
        price_str = match.group(1).replace(',', '.')
        try:
            return int(float(price_str))
        except:
            return 0
    return 0

def create_product_entry(watch_data, index, gender=None):
    """Crée une entrée produit au format du site"""
    name = watch_data['name']
    slug = clean_filename(name)
    
    # Utiliser le genre du watch_data si disponible, sinon utiliser celui passé en paramètre
    if 'gender' in watch_data:
        gender = watch_data['gender']
    elif not gender:
        gender = determine_gender(watch_data.get('description', ''), name)
    
    # Déterminer la catégorie et sous-catégorie
    if gender == 'femme':
        category = 'womens-clothing'
        subcategory = 'accessoires-femme'
        product_id = f'accessoires-femme-{index+1:03d}'
    elif gender == 'homme':
        category = 'mens-clothing'
        subcategory = 'accessoires-homme'
        product_id = f'accessoires-homme-{index+1:03d}'
    else:
        category = 'accessories'
        subcategory = None
        product_id = f'accessoires-{index+1:03d}'
    
    # Générer les noms multilingues (basique - à améliorer)
    name_fr = name
    name_en = name  # À traduire si nécessaire
    name_de = name  # À traduire si nécessaire
    
    # Générer les descriptions multilingues
    description = watch_data.get('description', f'Une montre élégante {name}')
    description_fr = description
    description_en = description  # À traduire si nécessaire
    description_de = description  # À traduire si nécessaire
    
    # Nom de l'image
    image_id = slug.replace('-', '_')
    
    product = {
        'id': product_id,
        'name': name_de,
        'name_fr': name_fr,
        'name_en': name_en,
        'slug': slug,
        'price': watch_data.get('price', 0),
        'oldPrice': None,
        'description': description_de,
        'description_fr': description_fr,
        'description_en': description_en,
        'category': category,
        'subcategory': subcategory,
        'images': [image_id],
        'sizes': None,  # Les montres n'ont généralement pas de tailles
        'colors': None
    }
    
    return product, image_id, watch_data.get('image_url')

def main():
    print("🚀 Début de l'importation des montres depuis temps-et-merveilles.fr\n")
    
    # Scraper les produits
    watches = scrape_products()
    
    if not watches:
        print("\n❌ Aucun produit trouvé. Vérifiez l'URL et la structure du site.")
        return
    
    print(f"\n✓ {len(watches)} produits trouvés\n")
    
    # Charger les fichiers existants
    try:
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
    except:
        existing_products = []
    
    try:
        with open(PLACEHOLDER_IMAGES_FILE, 'r', encoding='utf-8') as f:
            placeholder_data = json.load(f)
            placeholder_images = placeholder_data.get('placeholderImages', [])
    except:
        placeholder_images = []
    
    # Traiter chaque montre
    new_products = []
    new_images = []
    
    for i, watch in enumerate(watches):
        print(f"\n[{i+1}/{len(watches)}] Traitement: {watch.get('name', 'Montre')}")
        
        # Le genre peut déjà être dans watch_data si venant de Shopify
        gender = watch.get('gender')
        if not gender:
            gender = determine_gender(watch.get('description', ''), watch.get('name', ''))
        print(f"  Genre détecté: {gender}")
        
        # Créer l'entrée produit
        product, image_id, image_url = create_product_entry(watch, i, gender)
        
        # Télécharger l'image
        if image_url:
            image_filename = f"{image_id}.jpg"
            image_path = os.path.join(PRODUCTS_DIR, image_filename)
            image_relative_path = f"/images/products/{image_filename}"
            
            if download_image(image_url, image_path):
                # Ajouter à placeholder_images
                new_images.append({
                    'id': image_id,
                    'description': product['name_fr'],
                    'imageUrl': image_relative_path,
                    'imageHint': 'watch'
                })
                print(f"  ✓ Image ajoutée: {image_id}")
            else:
                print(f"  ⚠ Image non téléchargée, utilisation d'un placeholder")
        else:
            print(f"  ⚠ Aucune image trouvée pour ce produit")
        
        new_products.append(product)
    
    # Fusionner avec les produits existants
    all_products = existing_products + new_products
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde de {len(new_products)} nouveaux produits...")
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"✓ {NEW_PRODUCTS_FILE} mis à jour")
    
    # Fusionner les images
    all_images = placeholder_images + new_images
    
    print(f"\n💾 Sauvegarde de {len(new_images)} nouvelles images...")
    with open(PLACEHOLDER_IMAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump({'placeholderImages': all_images}, f, ensure_ascii=False, indent=2)
    print(f"✓ {PLACEHOLDER_IMAGES_FILE} mis à jour")
    
    print(f"\n✅ Importation terminée!")
    print(f"   - {len(new_products)} produits ajoutés")
    print(f"   - {len(new_images)} images téléchargées")

if __name__ == '__main__':
    main()

