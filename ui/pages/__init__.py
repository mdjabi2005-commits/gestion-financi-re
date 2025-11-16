# -*- coding: utf-8 -*-
"""
Package ui.pages - Pages de l'interface utilisateur
"""

# Import des modules de pages pour faciliter l'accès
from . import accueil
from . import transactions
from . import portefeuille
from . import scan_tickets
from . import scan_revenus
from . import recurrences
from . import analytics
from . import investissements

__all__ = [
    'accueil',
    'transactions',
    'portefeuille',
    'scan_tickets',
    'scan_revenus',
    'recurrences',
    'analytics',
    'investissements',
]
