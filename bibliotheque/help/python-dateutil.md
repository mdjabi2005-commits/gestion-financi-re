# 📚 Bibliothèque : python-dateutil

## 🎯 Qu'est-ce que python-dateutil ?

**python-dateutil** est une extension puissante du module standard `datetime`. Elle offre des fonctionnalités avancées pour parser, calculer et manipuler des dates de manière intuitive.

**PyPI** : https://pypi.org/project/python-dateutil/  
**Documentation** : https://dateutil.readthedocs.io

---

## 💡 Pourquoi python-dateutil dans notre projet ?

1. **Récurrences financières** : Calculer échéances mensuelles, annuelles
2. **Parsing flexible** : Analyser dates variées ("23/12/2024", "Dec 23, 2024")
3. **Calculs de périodes** : Ajouter/soustraire mois, années précisément
4. **Gestion budgets** : Calculer début/fin de mois, trimestre
5. **Fuseaux horaires** : Support timezone si nécessaire

---

## 🔧 Concepts de base

### 1. Parsing de dates

```python
from dateutil import parser

# Parse automatiquement différents formats
date1 = parser.parse("2024-12-23")
date2 = parser.parse("23/12/2024", dayfirst=True)  # Format européen
date3 = parser.parse("Dec 23, 2024")
date4 = parser.parse("23 décembre 2024")

print(date1)  # datetime.datetime(2024, 12, 23, 0, 0)
```

### 2. relativedelta (différence flexible)

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta

today = datetime(2024, 12, 23)

# Ajouter 1 mois (gère nombres de jours différents)
next_month = today + relativedelta(months=1)
print(next_month)  # 2025-01-23

# Ajouter 1 an
next_year = today + relativedelta(years=1)
print(next_year)  # 2025-12-23

# Combiné
date = today + relativedelta(months=3, days=5)
print(date)  # 2025-03-28
```

### 3. Différence entre deux dates

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta

start = datetime(2024, 1, 15)
end = datetime(2024, 12, 23)

diff = relativedelta(end, start)

print(f"{diff.years} ans, {diff.months} mois, {diff.days} jours")
# 0 ans, 11 mois, 8 jours
```

---

## 📊 Exemples concrets de notre app

### Générer transactions récurrentes (`recurrence_generation.py`)

```python
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict

def generate_recurrence_dates(
    start_date: date,
    frequency: str,
    num_occurrences: int = 12
) -> List[date]:
    """
    Génère les dates de récurrence.
    
    frequency: 'quotidienne', 'hebdomadaire', 'mensuelle', 'annuelle'
    """
    dates = [start_date]
    current = start_date
    
    delta_map = {
        'quotidienne': relativedelta(days=1),
        'hebdomadaire': relativedelta(weeks=1),
        'mensuelle': relativedelta(months=1),
        'annuelle': relativedelta(years=1)
    }
    
    delta = delta_map.get(frequency.lower(), relativedelta(months=1))
    
    for _ in range(num_occurrences - 1):
        current = current + delta
        dates.append(current)
    
    return dates

# Exemple : Loyer mensuel
loyer_dates = generate_recurrence_dates(
    start_date=date(2024, 1, 1),
    frequency='mensuelle',
    num_occurrences=12
)

for d in loyer_dates:
    print(f"Loyer dû le {d.strftime('%d/%m/%Y')}")
# Loyer dû le 01/01/2024
# Loyer dû le 01/02/2024
# ...
```

### Calculer échéances à venir (`portfolio.py`)

```python
from datetime import date
from dateutil.relativedelta import relativedelta

def get_upcoming_deadlines(recurrence_data: dict, months_ahead: int = 3):
    """
    Calcule les prochaines échéances d'une récurrence.
    """
    today = date.today()
    end_date = today + relativedelta(months=months_ahead)
    
    frequency = recurrence_data['frequence']
    last_generated = recurrence_data.get('derniere_generation')
    
    if not last_generated:
        last_generated = today
    
    # Calculer prochaine échéance
    if frequency == 'mensuelle':
        next_due = last_generated + relativedelta(months=1)
    elif frequency == 'annuelle':
        next_due = last_generated + relativedelta(years=1)
    elif frequency == 'hebdomadaire':
        next_due = last_generated + relativedelta(weeks=1)
    else:
        next_due = last_generated + relativedelta(days=1)
    
    # Générer toutes les échéances jusqu'à end_date
    deadlines = []
    current = next_due
    
    while current <= end_date:
        deadlines.append({
            'date': current,
            'montant': recurrence_data['montant'],
            'description': recurrence_data['description']
        })
        
        if frequency == 'mensuelle':
            current = current + relativedelta(months=1)
        elif frequency == 'annuelle':
            current = current + relativedelta(years=1)
        elif frequency == 'hebdomadaire':
            current = current + relativedelta(weeks=1)
        else:
            current = current + relativedelta(days=1)
    
    return deadlines
```

### Calculer période budget (`services.py`)

```python
from datetime import date
from dateutil.relativedelta import relativedelta

def get_current_month_period() -> tuple[date, date]:
    """
    Retourne le premier et dernier jour du mois actuel.
    """
    today = date.today()
    
    # Premier jour du mois
    first_day = today.replace(day=1)
    
    # Dernier jour du mois
    next_month = first_day + relativedelta(months=1)
    last_day = next_month - relativedelta(days=1)
    
    return first_day, last_day

# Exemple
start, end = get_current_month_period()
print(f"Budget du {start} au {end}")
# Budget du 2024-12-01 au 2024-12-31

def get_quarter_period(year: int, quarter: int) -> tuple[date, date]:
    """
    Retourne le premier et dernier jour d'un trimestre.
    """
    quarter_start_months = {1: 1, 2: 4, 3: 7, 4: 10}
    
    start_month = quarter_start_months[quarter]
    start_date = date(year, start_month, 1)
    end_date = start_date + relativedelta(months=3) - relativedelta(days=1)
    
    return start_date, end_date

# Exemple Q4 2024
start, end = get_quarter_period(2024, 4)
print(f"Q4 2024 : {start} au {end}")
# Q4 2024 : 2024-10-01 au 2024-12-31
```

### Normaliser colonne récurrence (`helpers.py`)

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sqlite3

def normalize_recurrence_column(conn: sqlite3.Connection):
    """
    Migre l'ancienne colonne 'recurrence' vers le nouveau système.
    """
    cursor = conn.cursor()
    
    # Récupérer anciennes récurrences
    old_recurrences = cursor.execute("""
        SELECT id, recurrence, date_fin 
        FROM echeances 
        WHERE recurrence IS NOT NULL
    """).fetchall()
    
    for rec_id, freq, date_fin in old_recurrences:
        # Convertir fréquence texte en périodicité
        frequency_map = {
            'Mensuelle': 'mensuelle',
            'Annuelle': 'annuelle',
            'Hebdomadaire': 'hebdomadaire',
            'Quotidienne': 'quotidienne'
        }
        
        new_freq = frequency_map.get(freq, 'mensuelle')
        
        # Si pas de date_fin, calculer 1 an
        if not date_fin:
            today = datetime.now().date()
            date_fin = today + relativedelta(years=1)
        
        # Mettre à jour
        cursor.execute("""
            UPDATE echeances 
            SET type_echeance = 'recurrente',
                recurrence = ?
            WHERE id = ?
        """, (new_freq, rec_id))
    
    conn.commit()
```

---

## ⚠️ Pièges courants

### 1. relativedelta vs timedelta

```python
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

date = datetime(2024, 1, 31)

# ❌ timedelta ne gère pas les mois variables
# 1 mois = 30 jours ?
next_month_wrong = date + timedelta(days=30)
print(next_month_wrong)  # 2024-03-01 (pas le bon mois!)

# ✅ relativedelta gère correctement
next_month_right = date + relativedelta(months=1)
print(next_month_right)  # 2024-02-29 (dernier jour de février)
```

### 2. Parser avec dayfirst

```python
from dateutil import parser

# ❌ Format ambigu, assume mois d'abord (US)
date = parser.parse("01/02/2024")
print(date)  # 2024-01-02 (2 janvier)

# ✅ Spécifier format européen
date = parser.parse("01/02/2024", dayfirst=True)
print(date)  # 2024-02-01 (1er février)
```

### 3. Gérer exceptions parsing

```python
from dateutil import parser
from dateutil.parser import ParserError

# ❌ Crash si format invalide
date = parser.parse("invalid")

# ✅ Gérer l'exception
try:
    date = parser.parse(user_input, dayfirst=True)
except ParserError:
    print("Date invalide")
    date = None
```

---

## 🔥 Opérations avancées

### Calculer âge précis

```python
from datetime import date
from dateutil.relativedelta import relativedelta

birth_date = date(1990, 5, 15)
today = date.today()

age = relativedelta(today, birth_date)

print(f"{age.years} ans, {age.months} mois, {age.days} jours")
```

### Trouver dernier jour du mois

```python
from datetime import date
from dateutil.relativedelta import relativedelta

def last_day_of_month(d: date) -> date:
    # Premier jour du mois suivant - 1 jour
    first_next = d.replace(day=1) + relativedelta(months=1)
    return first_next - relativedelta(days=1)

print(last_day_of_month(date(2024, 2, 15)))  # 2024-02-29
print(last_day_of_month(date(2024, 4, 1)))   # 2024-04-30
```

---

## 📖 Ressources

- **Documentation** : https://dateutil.readthedocs.io
- **PyPI** : https://pypi.org/project/python-dateutil/
- **Source** : https://github.com/dateutil/dateutil

---

## 💡 python-dateutil dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `recurrence_generation.py` | Générer échéances récurrentes |
| `portfolio/helpers.py` | Normaliser colonnes récurrences |
| `services/recurrence.py` | Backfill transactions récurrentes |
| `portfolio/manage.py` | Calculer prochaines échéances |

**Commande d'installation** :
```bash
pip install python-dateutil
```

**Bonnes pratiques** :
- ✅ Utiliser `relativedelta` pour mois/années
- ✅ Spécifier `dayfirst=True` pour format européen
- ✅ Gérer `ParserError` pour inputs utilisateur
- ❌ Ne pas utiliser `timedelta` pour périodes \> 1 mois
- ❌ Ne pas assumer format date sans `dayfirst`
