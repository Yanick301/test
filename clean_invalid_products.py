#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour nettoyer les produits invalides du fichier new_products.json
"""

import json
import re

NEW_PRODUCTS_FILE = "new_products.json"
PLACEHOLDER_IMAGES_FILE = "src/lib/placeholder-images.json"

def is_invalid_product(product):
    """Vérifie si un produit est invalide"""
    name = product.get('name', '') or product.get('name_fr', '')
    
    if not name or len(name.strip()) < 3:
        return True
    
    # Exclure les éléments de navigation
    excluded_keywords = [
        'acceuil', 'accueil', 'boutique', 'contact', 'blog', 'à propos', 'a propos',
        'information', 'emplacement', 'apprenez', 'notre', 'nous', 'connaître',
        'panier', 'loading', 'done', 'ajouter', 'produit en vente', '%',
        '📞', 'phone', 'téléphone', 'tel:', 'mailto:', 'facebook', 'instagram',
        '33 6 29', '29 61 06'
    ]
    
    name_lower = name.lower()
    for keyword in excluded_keywords:
        if keyword in name_lower:
            return True
    
    # Vérifier que le nom contient au moins quelques lettres
    if not re.search(r'[a-zA-Z]{3,}', name):
        return True
    
    # Vérifier que le slug n'est pas vide
    if not product.get('slug') or len(product.get('slug', '')) < 3:
        return True
    
    return False

def main():
    print("🧹 Nettoyage des produits invalides...\n")
    
    # Charger les produits
    try:
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return
    
    print(f"📊 {len(products)} produits au total\n")
    
    # Filtrer les produits valides
    valid_products = []
    invalid_count = 0
    
    for product in products:
        if is_invalid_product(product):
            invalid_count += 1
            print(f"  ✗ Supprimé: {product.get('name', '')[:50]}")
        else:
            valid_products.append(product)
    
    print(f"\n✓ {invalid_count} produits invalides supprimés")
    print(f"✓ {len(valid_products)} produits valides conservés\n")
    
    # Sauvegarder
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_products, f, ensure_ascii=False, indent=2)
    
    print(f"💾 {NEW_PRODUCTS_FILE} mis à jour")
    
    # Nettoyer aussi les images orphelines
    try:
        with open(PLACEHOLDER_IMAGES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            placeholder_images = data.get('placeholderImages', [])
    except:
        placeholder_images = []
    
    # Garder seulement les images référencées par les produits valides
    valid_image_ids = set()
    for product in valid_products:
        for img_id in product.get('images', []):
            valid_image_ids.add(img_id)
    
    valid_images = [img for img in placeholder_images if img.get('id') in valid_image_ids]
    removed_images = len(placeholder_images) - len(valid_images)
    
    if removed_images > 0:
        print(f"\n🗑️  {removed_images} images orphelines supprimées")
        with open(PLACEHOLDER_IMAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump({'placeholderImages': valid_images}, f, ensure_ascii=False, indent=2)
        print(f"💾 {PLACEHOLDER_IMAGES_FILE} mis à jour")
    
    print("\n✅ Nettoyage terminé!")

if __name__ == '__main__':
    main()


