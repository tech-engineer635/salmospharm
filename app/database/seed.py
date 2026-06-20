"""Donnees initiales officielles de la base SALMOSPHARM."""

from __future__ import annotations

from sqlalchemy import Connection, func, insert, select

from app.database.models import Categorie, Parametre


DEFAULT_CATEGORIES = (
    ("Antalgiques", "Medicaments contre la douleur"),
    ("Antibiotiques", "Medicaments contre les infections bacteriennes"),
    ("Antipaludeens", "Medicaments contre le paludisme"),
    ("Vitamines", "Complements vitaminiques"),
    ("Antiseptiques", "Produits de desinfection"),
)

DEFAULT_PARAMETRES = {
    "nom_pharmacie": "SALMOSPHARM 133",
    "telephone": None,
    "adresse": None,
    "devise": "CDF",
    "seuil_expiration_jours": 30,
    "largeur_ticket": 80,
    "impression_auto": 1,
    "sauvegarde_auto": 1,
    "frequence_sauvegarde": "QUOTIDIENNE",
}


def seed_initial_data(connection: Connection) -> None:
    """Insere les donnees initiales sans creer de compte utilisateur."""
    parametres_count = connection.execute(select(func.count()).select_from(Parametre)).scalar_one()
    if parametres_count == 0:
        connection.execute(insert(Parametre).values(**DEFAULT_PARAMETRES))

    existing_category_names = set(connection.execute(select(Categorie.nom)).scalars())
    missing_categories = [
        {"nom": nom, "description": description}
        for nom, description in DEFAULT_CATEGORIES
        if nom not in existing_category_names
    ]
    if missing_categories:
        connection.execute(insert(Categorie), missing_categories)
