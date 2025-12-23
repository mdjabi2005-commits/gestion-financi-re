# 📚 Bibliothèque : Requests

## 🎯 Qu'est-ce que Requests ?

**Requests** est LA bibliothèque HTTP pour Python. Elle simplifie énormément les requêtes web (GET, POST, etc.) avec une API élégante et pythonique.

**Site officiel** : https://requests.readthedocs.io  
**Documentation** : https://requests.readthedocs.io/en/latest/

---

## 💡 Pourquoi Requests dans notre projet ?

1. **Vérifications de mise à jour** : Consulter l'API GitHub pour les releases
2. **Téléchargements** : Récupérer des fichiers (mises à jour, données)
3. **APIs externes** : Communication avec services web
4. **Simplicité** : Bien plus simple que `urllib`
5. **Robustesse** : Gestion automatique des sessions, cookies, redirections

---

## 🔧 Concepts de base

### 1. Requête GET simple

```python
import requests

# Requête basique
response = requests.get('https://api.github.com')

# Vérifier le statut
if response.status_code == 200:
    print("✅ Succès")
    data = response.json()  # Parse JSON automatiquement
else:
    print(f"❌ Erreur {response.status_code}")
```

### 2. Paramètres de requête

```python
# Paramètres dans l'URL
params = {
    'q': 'gestion financière',
    'sort': 'stars',
    'order': 'desc'
}

response = requests.get('https://api.github.com/search/repositories', 
                       params=params)
# URL générée: .../search/repositories?q=gestion+financière&sort=stars&order=desc
```

### 3. Headers personnalisés

```python
headers = {
    'User-Agent': 'GestioV4/4.0',
    'Accept': 'application/json',
    'Authorization': 'Bearer TOKEN'
}

response = requests.get(url, headers=headers)
```

---

## 📊 Exemples concrets de notre app

### Vérifier les mises à jour GitHub

```python
import requests
from packaging import version

def check_for_updates(current_version: str) -> dict:
    """
    Vérifie si une nouvelle version est disponible sur GitHub.
    """
    url = "https://api.github.com/repos/mdjabi2005-commits/gestion-financiere_little/releases/latest"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lève exception si erreur HTTP
        
        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')
        
        if version.parse(latest_version) > version.parse(current_version):
            return {
                'update_available': True,
                'latest_version': latest_version,
                'download_url': release_data['assets'][0]['browser_download_url'],
                'release_notes': release_data['body']
            }
        else:
            return {'update_available': False}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur vérification mise à jour: {e}")
        return {'error': str(e)}
```

### Télécharger un fichier avec progression

```python
import requests
from pathlib import Path

def download_file(url: str, destination: Path, chunk_size: int = 8192):
    """
    Télécharge un fichier avec barre de progression.
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                
                # Progression
                percent = (downloaded / total_size) * 100 if total_size else 0
                print(f"\rTéléchargement: {percent:.1f}%", end='')
    
    print("\n✅ Téléchargement terminé")
    return destination
```

### Envoyer des logs à un service externe

```python
import requests
import json

def send_error_log(error_data: dict):
    """
    Envoie les erreurs critiques à un service de monitoring.
    """
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    payload = {
        'text': f"🚨 Erreur Gestio V4",
        'attachments': [{
            'color': 'danger',
            'fields': [
                {'title': 'Type', 'value': error_data.get('type'), 'short': True},
                {'title': 'Message', 'value': error_data.get('message'), 'short': False}
            ]
        }]
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        response.raise_for_status()
        print("✅ Log envoyé")
    except requests.exceptions.RequestException:
        pass  # Silencieux si le webhook échoue
```

---

## ⚠️ Pièges courants

### 1. Toujours définir un timeout

```python
# ❌ Peut bloquer indéfiniment
response = requests.get(url)

# ✅ Timeout de 10 secondes
response = requests.get(url, timeout=10)

# ✅ Timeout séparé connect/read
response = requests.get(url, timeout=(3, 10))
```

### 2. Gérer les exceptions

```python
# ❌ Pas de gestion d'erreur
response = requests.get(url)
data = response.json()

# ✅ Gestion complète
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Erreur HTTP → exception
    data = response.json()
except requests.exceptions.Timeout:
    print("⏱️ Timeout")
except requests.exceptions.HTTPError as e:
    print(f"❌ Erreur HTTP: {e}")
except requests.exceptions.RequestException as e:
    print(f"❌ Erreur réseau: {e}")
```

### 3. SSL/TLS en production

```python
# ❌ DANGEREUX en production
response = requests.get(url, verify=False)

# ✅ Toujours vérifier le certificat
response = requests.get(url, verify=True)

# ✅ Certificat personnalisé si nécessaire
response = requests.get(url, verify='/path/to/certfile')
```

### 4. Sessions pour requêtes multiples

```python
# ❌ Inefficace (nouvelle connexion à chaque fois)
for i in range(10):
    response = requests.get(f'https://api.example.com/data/{i}')

# ✅ Réutilise la connexion
session = requests.Session()
session.headers.update({'User-Agent': 'GestioV4/4.0'})

for i in range(10):
    response = session.get(f'https://api.example.com/data/{i}')
```

---

## 🔥 Opérations avancées

### Retry automatique avec backoff

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

# Configuration retry
retry_strategy = Retry(
    total=3,                    # 3 tentatives max
    backoff_factor=1,           # 1s, 2s, 4s entre tentatives
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Utilisation
response = session.get('https://api.example.com/data')
```

### Requêtes POST avec données

```python
# POST avec JSON
data = {'username': 'user', 'password': 'pass'}
response = requests.post(url, json=data)

# POST avec formulaire
form_data = {'field1': 'value1', 'field2': 'value2'}
response = requests.post(url, data=form_data)

# POST avec fichier
files = {'file': open('document.pdf', 'rb')}
response = requests.post(url, files=files)
```

---

## 📖 Ressources

- **Documentation** : https://requests.readthedocs.io
- **Quickstart** : https://requests.readthedocs.io/en/latest/user/quickstart/
- **Advanced** : https://requests.readthedocs.io/en/latest/user/advanced/

---

## 💡 Requests dans notre projet

| Usage | Description |
|-------|-------------|
| Vérification mises à jour | API GitHub releases |
| Téléchargements | Mises à jour, ressources externes |
| Monitoring (optionnel) | Webhooks erreurs |

**Commande d'installation** :
```bash
pip install requests
```

**Bonnes pratiques** :
- ✅ Toujours définir `timeout`
- ✅ Utiliser `raise_for_status()` pour détecter erreurs HTTP
- ✅ Gérer les exceptions (`RequestException`)
- ✅ Utiliser `Session` pour requêtes multiples
- ❌ Jamais `verify=False` en production
- ❌ Ne pas ignorer les erreurs réseau
