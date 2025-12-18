#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour importer les accessoires hommes depuis faguo-store.com avec Selenium
Remplace les produits existants dans la sous-catégorie accessoires-homme
"""

import json
import os
import re
import time
import sys
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        USE_WEBDRIVER_MANAGER = True
    except ImportError:
        USE_WEBDRIVER_MANAGER = False
except ImportError:
    print("❌ Selenium n'est pas installé!")
    print("\n📦 Installation nécessaire:")
    print("   1. Installez Selenium:")
    print("      pip3 install selenium --break-system-packages")
    print("      OU")
    print("      pip3 install --user selenium")
    print("\n   2. Installez ChromeDriver:")
    print("      - Téléchargez depuis: https://chromedriver.chromium.org/")
    print("      - Ou installez avec: sudo apt-get install chromium-chromedriver")
    print("      - Ou utilisez: pip3 install webdriver-manager")
    print("\n   3. Assurez-vous que Google Chrome est installé")
    sys.exit(1)

import requests
from bs4 import BeautifulSoup

# Configuration
SOURCE_SITE = "https://www.faguo-store.com"
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

def setup_driver():
    """Configure et retourne le driver Selenium"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Mode sans interface (commentez pour voir le navigateur)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Chercher Chrome dans différents emplacements
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/snap/bin/chromium',
    ]
    
    chrome_binary = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_binary = path
            break
    
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        print(f"  ✓ Chrome trouvé: {chrome_binary}")
    
    try:
        if USE_WEBDRIVER_MANAGER:
            # Utiliser webdriver-manager pour télécharger automatiquement ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Utiliser ChromeDriver du système
            driver = webdriver.Chrome(options=chrome_options)
        
        # Exécuter du JavaScript pour masquer l'automation
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        return driver
    except Exception as e:
        print(f"❌ Erreur lors de la création du driver: {e}")
        print("   Assurez-vous que Google Chrome est installé")
        if not USE_WEBDRIVER_MANAGER:
            print("   Installez webdriver-manager: pip3 install --user webdriver-manager")
            print("   OU installez ChromeDriver manuellement depuis: https://chromedriver.chromium.org/")
        sys.exit(1)

def is_accessoire_homme(name, category, description, tags):
    """Vérifie si le produit est un accessoire pour homme"""
    text = (name + " " + category + " " + description + " " + tags).lower()
    
    accessoire_keywords = ['accessoire', 'accessory', 'sac', 'bag', 'portefeuille', 'wallet', 
                          'ceinture', 'belt', 'montre', 'watch', 'lunettes', 'glasses',
                          'chapeau', 'hat', 'casquette', 'cap', 'écharpe', 'scarf']
    
    homme_keywords = ['homme', 'man', 'men', 'mens', 'masculin', 'masculine', 'gentleman']
    femme_keywords = ['femme', 'woman', 'women', 'ladies', 'féminin', 'feminine']
    
    is_homme = any(keyword in text for keyword in homme_keywords)
    is_femme = any(keyword in text for keyword in femme_keywords)
    
    if is_femme and not is_homme:
        return False
    
    is_accessoire = any(keyword in text for keyword in accessoire_keywords)
    
    if is_homme and is_accessoire:
        return True
    
    if 'accessoire' in category.lower() and not is_femme:
        return True
    
    return False

def scrape_products_with_selenium():
    """Scrape les produits avec Selenium"""
    print(f"🔍 Accès au site avec Selenium...\n")
    
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        print("✓ Driver Selenium initialisé\n")
        
        # Accéder à la page d'accueil
        print(f"  Accès à {SOURCE_SITE}...")
        driver.get(SOURCE_SITE)
        time.sleep(3)  # Attendre le chargement
        
        print(f"  ✓ Page chargée: {driver.title}\n")
        
        # Chercher les liens vers les collections accessoires-homme
        urls_to_try = [
            f"{SOURCE_SITE}/collections/accessoires-homme",
            f"{SOURCE_SITE}/collections/homme-accessoires",
            f"{SOURCE_SITE}/collections/homme",
            f"{SOURCE_SITE}/collections/accessoires",
            f"{SOURCE_SITE}/collections/all",
        ]
        
        product_links = set()
        
        for url in urls_to_try:
            try:
                print(f"  Tentative: {url}")
                driver.get(url)
                time.sleep(3)
                
                # Chercher les liens produits
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product"], a[href*="/p/"]')
                    for link in links:
                        href = link.get_attribute('href')
                        if href and '/product' in href.lower():
                            product_links.add(href)
                    print(f"  ✓ {len(links)} liens produits trouvés")
                except:
                    pass
                
                # Chercher aussi dans les éléments avec classe produit
                try:
                    product_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="product"], [class*="item"], [class*="card"]')
                    for elem in product_elements:
                        link = elem.find_element(By.TAG_NAME, 'a')
                        href = link.get_attribute('href')
                        if href and '/product' in href.lower():
                            product_links.add(href)
                except:
                    pass
                
                if product_links:
                    break
                    
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                continue
        
        print(f"\n  Total de {len(product_links)} produits uniques trouvés\n")
        
        # Scraper chaque page produit
        for i, product_url in enumerate(list(product_links)[:200]):  # Limiter à 200
            try:
                print(f"  [{i+1}/{min(len(product_links), 200)}] Scraping: {product_url[:60]}...")
                driver.get(product_url)
                time.sleep(2)
                
                # Extraire les informations
                product = extract_product_from_page(driver, product_url)
                if product and is_accessoire_homme(
                    product.get('name', ''),
                    product.get('category', ''),
                    product.get('description', ''),
                    product.get('tags', '')
                ):
                    products.append(product)
                    print(f"    ✓ Accessoire homme ajouté: {product.get('name', '')[:50]}")
                else:
                    print(f"    ⚠ Produit ignoré (pas un accessoire homme)")
                    
            except Exception as e:
                print(f"    ✗ Erreur: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("\n✓ Driver fermé")
    
    return products

def extract_product_from_page(driver, url):
    """Extrait les informations d'un produit depuis la page"""
    try:
        # Nom
        name = ""
        try:
            name_elem = driver.find_element(By.CSS_SELECTOR, 'h1, [class*="title"], [class*="name"]')
            name = name_elem.text.strip()
        except:
            try:
                name_elem = driver.find_element(By.TAG_NAME, 'h1')
                name = name_elem.text.strip()
            except:
                pass
        
        if not name:
            return None
        
        # Prix
        price = 0
        old_price = None
        try:
            price_elem = driver.find_element(By.CSS_SELECTOR, '[class*="price"]')
            price_text = price_elem.text
            price = extract_price(price_text)
            
            # Chercher un prix barré (ancien prix)
            try:
                old_price_elem = driver.find_element(By.CSS_SELECTOR, '[class*="old"], [class*="compare"], s, strike')
                old_price_text = old_price_elem.text
                old_price = extract_price(old_price_text)
            except:
                pass
        except:
            pass
        
        # Description
        description = ""
        try:
            desc_elem = driver.find_element(By.CSS_SELECTOR, '[class*="description"], [class*="content"]')
            description = desc_elem.text.strip()
        except:
            pass
        
        # Images
        image_urls = []
        try:
            img_elems = driver.find_elements(By.CSS_SELECTOR, 'img[class*="product"], img[class*="main"], img[src*="product"]')
            for img in img_elems:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                    if not src.startswith('http'):
                        src = SOURCE_SITE + src
                    image_urls.append(src)
        except:
            pass
        
        # Catégorie
        category = ""
        try:
            breadcrumb = driver.find_element(By.CSS_SELECTOR, '[class*="breadcrumb"], nav, ol')
            links = breadcrumb.find_elements(By.TAG_NAME, 'a')
            if links:
                category = links[-1].text.strip()
        except:
            pass
        
        return {
            'name': name,
            'price': price,
            'old_price': old_price,
            'image_urls': image_urls[:3],  # Max 3 images
            'description': description,
            'category': category,
            'tags': '',
            'url': url
        }
    except Exception as e:
        print(f"    Erreur extraction: {e}")
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
    
    category = 'mens-clothing'
    subcategory = 'accessoires-homme'
    product_id = f'accessoires-homme-{index+1:03d}'
    
    name_fr = name
    name_en = name
    name_de = name
    
    description = product_data.get('description', f'Un accessoire élégant pour homme {name}')
    description_fr = description
    description_en = description
    description_de = description
    
    image_urls = product_data.get('image_urls', [])
    image_ids = []
    if image_urls:
        for i, img_url in enumerate(image_urls[:3]):
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
    print("🚀 Importation des accessoires hommes depuis faguo-store.com (Selenium)\n")
    print("⚠️  Cette opération va REMPLACER les produits existants dans accessoires-homme\n")
    
    # Scraper les produits
    products_data = scrape_products_with_selenium()
    
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
        print(f"\n[{i+1}/{len(products_data)}] {product_data.get('name', '')[:60]}")
        
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

