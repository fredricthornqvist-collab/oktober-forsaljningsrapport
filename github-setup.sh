#!/bin/bash

# Guide för att publicera till GitHub och GitHub Pages

echo "📦 GitHub Setup Guide för Försäljningsrapport"
echo "=============================================="
echo ""

# Steg 1: Git init
echo "Steg 1: Initialisera Git repository"
echo "Kör: git init"
echo ""

# Steg 2: Första commit
echo "Steg 2: Lägg till filer och gör första commit"
echo "Kör:"
echo "  git add ."
echo "  git commit -m 'Initial commit: Oktober försäljningsrapport'"
echo ""

# Steg 3: Skapa GitHub repo
echo "Steg 3: Skapa GitHub repository"
echo "1. Gå till: https://github.com/new"
echo "2. Repository name: t.ex. 'oktober-forsnajlingsrapport' eller 'sales-dashboard'"
echo "3. Välj Private (om data är känslig) eller Public"
echo "4. SKAPA INTE README, .gitignore etc (vi har redan dessa)"
echo "5. Klicka 'Create repository'"
echo ""

# Steg 4: Länka och pusha
echo "Steg 4: Länka till GitHub och pusha"
echo "GitHub visar dessa kommandon efter du skapat repot:"
echo "  git remote add origin git@github.com:DIN-ANVÄNDARNAMN/REPO-NAMN.git"
echo "  git branch -M main"
echo "  git push -u origin main"
echo ""

# Steg 5: GitHub Pages
echo "Steg 5: Aktivera GitHub Pages (för att dela länk)"
echo "1. Gå till Settings i ditt GitHub repo"
echo "2. Klicka på 'Pages' i vänstermenyn"
echo "3. Under 'Source', välj 'main' branch"
echo "4. Klicka 'Save'"
echo "5. Efter några minuter kommer din dashboard finnas på:"
echo "   https://DIN-ANVÄNDARNAMN.github.io/REPO-NAMN/oktober_dashboard.html"
echo ""

echo "✅ När detta är klart kan du dela länken med kollegor!"
echo ""
echo "💡 Tips: Om data är känslig, använd Private repo och ge specifika personer access"
