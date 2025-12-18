#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour limiter le nombre de produits à 1100 maximum
"""

import json

NEW_PRODUCTS_FILE = "new_products.json"
PLACEHOLDER_IMAGES_FILE = "src/lib/placeholder-images.json"
MAX_PRODUCTS = 1100

def main():
    print(f"🔍 Vérification du nombre de produits...\n")
    
    # Charger les produits
    try:
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    current_count = len(products)
    print(f"📊 Produits actuels: {current_count}")
    print(f"📊 Limite maximale: {MAX_PRODUCTS}")
    
    if current_count <= MAX_PRODUCTS:
        print(f"\n✅ Le nombre de produits est correct ({current_count} ≤ {MAX_PRODUCTS})")
        return
    
    # Limiter à 1100
    excess = current_count - MAX_PRODUCTS
    print(f"\n⚠️  {excess} produits en trop! Limitation à {MAX_PRODUCTS} produits...")
    
    # Garder les 1100 premiers produits
    limited_products = products[:MAX_PRODUCTS]
    
    # Récupérer les IDs d'images utilisées
    used_image_ids = set()
    for product in limited_products:
        for img_id in product.get('images', []):
            used_image_ids.add(img_id)
    
    # Charger les images
    try:
        with open(PLACEHOLDER_IMAGES_FILE, 'r', encoding='utf-8') as f:
            placeholder_data = json.load(f)
            all_images = placeholder_data.get('placeholderImages', [])
    except:
        all_images = []
    
    # Garder seulement les images utilisées
    limited_images = [img for img in all_images if img.get('id') in used_image_ids]
    removed_images = len(all_images) - len(limited_images)
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde de {len(limited_products)} produits...")
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(limited_products, f, ensure_ascii=False, indent=2)
    print(f"✓ {NEW_PRODUCTS_FILE} mis à jour")
    
    if removed_images > 0:
        print(f"\n💾 Suppression de {removed_images} images orphelines...")
        with open(PLACEHOLDER_IMAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump({'placeholderImages': limited_images}, f, ensure_ascii=False, indent=2)
        print(f"✓ {PLACEHOLDER_IMAGES_FILE} mis à jour")
    
    print(f"\n✅ Limitation terminée!")
    print(f"   - {excess} produits supprimés")
    print(f"   - {removed_images} images orphelines supprimées")
    print(f"   - Total final: {len(limited_products)}/{MAX_PRODUCTS} produits")

if __name__ == '__main__':
    main()

