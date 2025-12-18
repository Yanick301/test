#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour importer les produits depuis un fichier JSON exporté
Accepte un fichier JSON avec les produits de 24s.com
"""

import json
import requests
import os
import re
from urllib.parse import urljoin
import sys

# Configuration
PRODUCTS_DIR = "public/images/products"
NEW_PRODUCTS_FILE = "new_products.json"
PLACEHOLDER_IMAGES_FILE = "src/lib/placeholder-images.json"
MAX_TOTAL_PRODUCTS = 1100

# Mapping des catégories
CATEGORY_MAPPING = {
    'homme': 'mens-clothing',
    'hommes': 'mens-clothing',
    'men': 'mens-clothing',
    'mens': 'mens-clothing',
    'chemise': 'mens-clothing',
    'chemises': 'mens-clothing',
    'pantalon': 'mens-clothing',
    'pantalons': 'mens-clothing',
    'veste': 'mens-clothing',
    'vestes': 'mens-clothing',
    'pull': 'mens-clothing',
    'pulls': 'mens-clothing',
    
    'femme': 'womens-clothing',
    'femmes': 'womens-clothing',
    'women': 'womens-clothing',
    'womens': 'womens-clothing',
    'robe': 'womens-clothing',
    'robes': 'womens-clothing',
    'top': 'womens-clothing',
    'tops': 'womens-clothing',
    'jupe': 'womens-clothing',
    'jupes': 'womens-clothing',
    
    'accessoire': 'accessories',
    'accessoires': 'accessories',
    'montre': 'accessories',
    'montres': 'accessories',
    'sac': 'accessories',
    'sacs': 'accessories',
    
    'chaussure': 'shoes',
    'chaussures': 'shoes',
    'shoe': 'shoes',
    'shoes': 'shoes',
    
    'sport': 'sport',
    'hiver': 'winter-clothing',
    'winter': 'winter-clothing',
}

SUBCATEGORY_MAPPING = {
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
    """Mappe une catégorie vers une catégorie du nouveau site"""
    if not category_name:
        return 'accessories', None
    
    cat_lower = category_name.lower()
    
    for key, mapped_cat in CATEGORY_MAPPING.items():
        if key in cat_lower:
            category = mapped_cat
            
            subcategory = None
            if subcategory_name:
                sub_lower = subcategory_name.lower()
                for key, mapped_sub in SUBCATEGORY_MAPPING.items():
                    if key in sub_lower:
                        subcategory = mapped_sub
                        break
            
            return category, subcategory
    
    return 'accessories', None

def determine_gender(category_name, description, name):
    """Détermine le genre du produit"""
    text = (category_name + " " + description + " " + name).lower()
    
    femme_keywords = ['femme', 'woman', 'women', 'ladies', 'dame', 'dames', 'féminin', 'feminine']
    homme_keywords = ['homme', 'man', 'men', 'gentleman', 'herren', 'masculin', 'masculine']
    
    femme_score = sum(1 for keyword in femme_keywords if keyword in text)
    homme_score = sum(1 for keyword in homme_keywords if keyword in text)
    
    if femme_score > homme_score:
        return 'femme'
    elif homme_score > femme_score:
        return 'homme'
    return 'unisex'

def create_product_entry(product_data, index, gender):
    """Crée une entrée produit au format du site"""
    name = product_data.get('name') or product_data.get('title') or product_data.get('name_fr', '')
    if not name:
        return None, [], []
    
    slug = clean_filename(name)
    
    # Catégorie
    category_name = product_data.get('category') or product_data.get('product_type') or product_data.get('type', '')
    subcategory_name = product_data.get('subcategory') or product_data.get('collection', '')
    category, subcategory = map_category(category_name, subcategory_name)
    
    # Ajuster selon le genre
    if gender == 'femme' and category == 'mens-clothing':
        category = 'womens-clothing'
    elif gender == 'homme' and category == 'womens-clothing':
        category = 'mens-clothing'
    
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
    
    # Noms multilingues
    name_fr = product_data.get('name_fr') or name
    name_en = product_data.get('name_en') or name
    name_de = product_data.get('name_de') or name
    
    # Descriptions
    description = product_data.get('description') or product_data.get('body_html', '')
    if description:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(description, 'html.parser')
        description = soup.get_text(strip=True)
    
    description_fr = product_data.get('description_fr') or description or f'Un produit élégant {name}'
    description_en = product_data.get('description_en') or description or f'An elegant product {name}'
    description_de = product_data.get('description_de') or description or f'Ein elegantes Produkt {name}'
    
    # Prix
    price = product_data.get('price') or product_data.get('price_fr', 0)
    if isinstance(price, str):
        price = int(float(price.replace(',', '.')))
    old_price = product_data.get('old_price') or product_data.get('compare_at_price') or product_data.get('oldPrice')
    if old_price and isinstance(old_price, str):
        old_price = int(float(old_price.replace(',', '.')))
    
    # Images
    images = product_data.get('images', [])
    if not images:
        images = product_data.get('image_urls', [])
    if not images and product_data.get('image'):
        images = [product_data.get('image')]
    
    image_ids = []
    image_urls = []
    for i, img in enumerate(images[:3]):  # Max 3 images
        if isinstance(img, dict):
            img_url = img.get('src') or img.get('url') or img.get('image')
        else:
            img_url = img
        
        if img_url:
            img_id = slug.replace('-', '_')
            if i > 0:
                img_id += f'_{i+1}'
            image_ids.append(img_id)
            image_urls.append(img_url)
    
    if not image_ids:
        image_ids = [slug.replace('-', '_')]
    
    product = {
        'id': product_id,
        'name': name_de,
        'name_fr': name_fr,
        'name_en': name_en,
        'slug': slug,
        'price': price,
        'oldPrice': old_price,
        'description': description_de,
        'description_fr': description_fr,
        'description_en': description_en,
        'category': category,
        'subcategory': subcategory,
        'images': image_ids,
        'sizes': product_data.get('sizes'),
        'colors': product_data.get('colors')
    }
    
    return product, image_ids, image_urls

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_from_json_file.py <fichier_json>")
        print("\nLe fichier JSON doit contenir un tableau de produits avec:")
        print("  - name / title / name_fr")
        print("  - category / product_type")
        print("  - price")
        print("  - images / image_urls")
        print("  - description")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ Fichier non trouvé: {json_file}")
        sys.exit(1)
    
    print(f"🚀 Importation depuis {json_file}\n")
    
    # Charger le fichier JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        
        # Si c'est un objet avec une clé 'products'
        if isinstance(products_data, dict) and 'products' in products_data:
            products_data = products_data['products']
        
        if not isinstance(products_data, list):
            print("❌ Le fichier JSON doit contenir un tableau de produits")
            sys.exit(1)
        
        print(f"✓ {len(products_data)} produits trouvés dans le fichier\n")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        sys.exit(1)
    
    # Vérifier le nombre actuel
    try:
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
        current_count = len(existing_products)
        remaining = MAX_TOTAL_PRODUCTS - current_count
        print(f"📊 Produits actuels: {current_count}")
        print(f"📊 Produits restants: {remaining}")
        print(f"📊 Limite maximale: {MAX_TOTAL_PRODUCTS}\n")
        
        if remaining <= 0:
            print("⚠️  Limite de 1100 produits atteinte!")
            print("   Utilisez limit_products_to_1100.py pour nettoyer si nécessaire.")
            return
        
        products_data = products_data[:remaining]
        print(f"📊 Limitation à {len(products_data)} produits pour respecter la limite\n")
    except:
        existing_products = []
        current_count = 0
        remaining = MAX_TOTAL_PRODUCTS
        products_data = products_data[:remaining]
        print(f"📊 Produits actuels: 0")
        print(f"📊 Produits restants: {remaining}")
        print(f"📊 Limite maximale: {MAX_TOTAL_PRODUCTS}\n")
        print(f"📊 Limitation à {len(products_data)} produits\n")
    
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
        name = product_data.get('name') or product_data.get('title') or product_data.get('name_fr', 'Produit')
        print(f"\n[{i+1}/{len(products_data)}] {name[:60]}")
        
        # Déterminer le genre
        category_name = product_data.get('category') or product_data.get('product_type', '')
        description = product_data.get('description', '')
        gender = determine_gender(category_name, description, name)
        print(f"  Catégorie: {category_name} | Genre: {gender}")
        
        # Créer l'entrée produit
        product, image_ids, image_urls = create_product_entry(product_data, i, gender)
        if not product:
            print("  ⚠ Produit ignoré (nom manquant)")
            continue
        
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
                    'imageHint': category_name or 'product'
                })
                existing_image_ids.add(image_id)
                print(f"  ✓ Image {j+1} téléchargée: {image_id}")
        
        new_products.append(product)
    
    # Fusionner
    all_products = existing_products + new_products
    
    if len(all_products) > MAX_TOTAL_PRODUCTS:
        all_products = all_products[:MAX_TOTAL_PRODUCTS]
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde de {len(new_products)} nouveaux produits...")
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"✓ {NEW_PRODUCTS_FILE} mis à jour ({len(all_products)} produits au total)")
    
    # Images
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


