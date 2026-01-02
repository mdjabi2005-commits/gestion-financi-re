"""
Logging Configuration - Alias pour compatibilité

Ce fichier redirige vers config.logging_config pour éviter de casser les imports existants.
À terme, tous les imports devraient utiliser config.logging_config directement.
"""

# Redirection vers la vraie configuration
from config.logging_config import setup_logging, get_logger

__all__ = ['setup_logging', 'get_logger']
