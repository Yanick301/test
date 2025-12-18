#!/bin/bash
# Script d'installation de Selenium et ChromeDriver

echo "📦 Installation de Selenium et dépendances..."

# Installer Selenium
echo "1. Installation de Selenium..."
pip3 install --user selenium || pip3 install selenium --break-system-packages

# Vérifier si webdriver-manager est disponible (facilite l'installation de ChromeDriver)
echo "2. Installation de webdriver-manager (optionnel mais recommandé)..."
pip3 install --user webdriver-manager || pip3 install webdriver-manager --break-system-packages

echo ""
echo "✅ Installation terminée!"
echo ""
echo "📝 Note: Vous aurez aussi besoin de Google Chrome installé sur votre système."
echo "   Si ChromeDriver n'est pas trouvé automatiquement, installez-le:"
echo "   - sudo apt-get install chromium-chromedriver"
echo "   - OU téléchargez depuis https://chromedriver.chromium.org/"

