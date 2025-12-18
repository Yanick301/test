#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour remplacer les accessoires hommes depuis un fichier JSON exporté
Remplace les produits existants dans la sous-catégorie accessoires-homme
"""

import json
import requests
import os
import re
import sys

# Configuration
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

def is_accessoire_homme(product_data):
    """Vérifie si le produit est un accessoire pour homme"""
    name = (product_data.get('name') or product_data.get('title') or '').lower()
    category = (product_data.get('category') or product_data.get('product_type') or '').lower()
    description = (product_data.get('description') or '').lower()
    tags = (product_data.get('tags') or '').lower()
    
    text = name + " " + category + " " + description + " " + tags
    
    # Mots-clés pour accessoires
    accessoire_keywords = ['accessoire', 'accessory', 'sac', 'bag', 'portefeuille', 'wallet', 
                          'ceinture', 'belt', 'montre', 'watch', 'lunettes', 'glasses',
                          'chapeau', 'hat', 'casquette', 'cap', 'écharpe', 'scarf']
    
    # Mots-clés pour homme
    homme_keywords = ['homme', 'man', 'men', 'mens', 'masculin', 'masculine', 'gentleman']
    
    # Mots-clés à exclure (femme)
    femme_keywords = ['femme', 'woman', 'women', 'ladies', 'féminin', 'feminine']
    
    is_homme = any(keyword in text for keyword in homme_keywords)
    is_femme = any(keyword in text for keyword in femme_keywords)
    
    if is_femme and not is_homme:
        return False
    
    is_accessoire = any(keyword in text for keyword in accessoire_keywords)
    
    if is_homme and is_accessoire:
        return True
    
    if 'accessoire' in category and not is_femme:
        return True
    
    return False

def create_product_entry(product_data, index):
    """Crée une entrée produit au format du site"""
    name = product_data.get('name') or product_data.get('title') or product_data.get('name_fr', '')
    if not name:
        return None, [], []
    
    slug = clean_filename(name)
    
    # Catégorie fixe : accessoires-homme
    category = 'mens-clothing'
    subcategory = 'accessoires-homme'
    product_id = f'accessoires-homme-{index+1:03d}'
    
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
    
    description_fr = product_data.get('description_fr') or description or f'Un accessoire élégant pour homme {name}'
    description_en = product_data.get('description_en') or description or f'An elegant men\'s accessory {name}'
    description_de = product_data.get('description_de') or description or f'Ein elegantes Herrenaccessoire {name}'
    
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
        print("Usage: python3 replace_accessoires_homme_from_json.py <fichier_json>")
        print("\nLe fichier JSON doit contenir un tableau de produits accessoires pour hommes")
        print("Les produits existants dans accessoires-homme seront REMPLACÉS")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ Fichier non trouvé: {json_file}")
        sys.exit(1)
    
    print(f"🚀 Remplacement des accessoires hommes depuis {json_file}\n")
    print("⚠️  Cette opération va REMPLACER les produits existants dans accessoires-homme\n")
    
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
        
        # Filtrer pour ne garder que les accessoires hommes
        products_data = [p for p in products_data if is_accessoire_homme(p)]
        
        print(f"✓ {len(products_data)} accessoires hommes trouvés dans le fichier\n")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        sys.exit(1)
    
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
    
    # Supprimer les images des anciens produits
    old_image_ids = set()
    for product in all_products:
        if product.get('subcategory') == 'accessoires-homme':
            for img_id in product.get('images', []):
                old_image_ids.add(img_id)
    
    placeholder_images = [img for img in placeholder_images if img.get('id') not in old_image_ids]
    
    # Traiter chaque nouveau produit
    new_products = []
    new_images = []
    existing_image_ids = {img.get('id') for img in placeholder_images}
    
    for i, product_data in enumerate(products_data):
        name = product_data.get('name') or product_data.get('title') or product_data.get('name_fr', 'Produit')
        print(f"\n[{i+1}/{len(products_data)}] {name[:60]}")
        
        # Créer l'entrée produit
        product, image_ids, image_urls = create_product_entry(product_data, i)
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
    
    # Images
    all_images = placeholder_images + new_images
    print(f"\n💾 Sauvegarde de {len(new_images)} nouvelles images...")
    with open(PLACEHOLDER_IMAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump({'placeholderImages': all_images}, f, ensure_ascii=False, indent=2)
    print(f"✓ {PLACEHOLDER_IMAGES_FILE} mis à jour")
    
    print(f"\n✅ Remplacement terminé!")
    print(f"   - {old_count} anciens produits supprimés")
    print(f"   - {len(new_products)} nouveaux produits ajoutés")
    print(f"   - {len(new_images)} images téléchargées")
    print(f"   - Total: {len(all_products)} produits")

if __name__ == '__main__':
    main()

