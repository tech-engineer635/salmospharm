import pytest

from app.core.constants import (
    ACTION_CONNEXION_REUSSIE,
    ACTION_VENTE_VALIDEE,
    ACTIONS_JOURNAL,
    DEVISE_UNIQUE,
    LARGEURS_TICKET,
    MODE_PAIEMENT_UNIQUE,
    ROLE_GERANT,
    ROLE_VENDEUR,
    ROLES_VALIDES,
    TYPE_ALERTE_PRODUIT_EXPIRE,
    TYPE_MOUVEMENT_SORTIE,
    TYPES_ALERTES,
    TYPES_MOUVEMENT_STOCK,
)
from app.core.exceptions import PermissionRefuseeError
from app.core.permissions import (
    PERMISSION_AJUSTER_STOCK,
    PERMISSION_CONSULTER_PARAMETRES,
    PERMISSION_CREER_PRODUIT,
    PERMISSION_CREER_VENDEUR,
    PERMISSION_CREER_VENTE,
    PERMISSION_EXPORTER_DONNEES,
    PERMISSION_IMPORTER_DONNEES,
    PERMISSION_RECHERCHER_PRODUITS,
    a_permission,
    exiger_permission,
    exiger_role_valide,
    permissions_pour_role,
    role_valide,
)


def test_constantes_metier_officielles():
    assert ROLE_GERANT in ROLES_VALIDES
    assert ROLE_VENDEUR in ROLES_VALIDES
    assert DEVISE_UNIQUE == "CDF"
    assert MODE_PAIEMENT_UNIQUE == "ESPECES"
    assert TYPE_MOUVEMENT_SORTIE in TYPES_MOUVEMENT_STOCK
    assert TYPE_ALERTE_PRODUIT_EXPIRE in TYPES_ALERTES
    assert ACTION_CONNEXION_REUSSIE in ACTIONS_JOURNAL
    assert ACTION_VENTE_VALIDEE in ACTIONS_JOURNAL
    assert LARGEURS_TICKET == (58, 80)


def test_gerant_autorise_sur_actions_sensibles():
    assert a_permission(ROLE_GERANT, PERMISSION_CREER_VENDEUR)
    assert a_permission(ROLE_GERANT, PERMISSION_CREER_PRODUIT)
    assert a_permission(ROLE_GERANT, PERMISSION_AJUSTER_STOCK)
    assert a_permission(ROLE_GERANT, PERMISSION_CONSULTER_PARAMETRES)
    assert a_permission(ROLE_GERANT, PERMISSION_EXPORTER_DONNEES)
    assert a_permission(ROLE_GERANT, PERMISSION_IMPORTER_DONNEES)
    exiger_permission(ROLE_GERANT, PERMISSION_CREER_VENDEUR)


def test_vendeur_autorise_uniquement_sur_actions_limitees():
    assert a_permission(ROLE_VENDEUR, PERMISSION_CREER_VENTE)
    assert a_permission(ROLE_VENDEUR, PERMISSION_RECHERCHER_PRODUITS)

    assert not a_permission(ROLE_VENDEUR, PERMISSION_CREER_VENDEUR)
    assert not a_permission(ROLE_VENDEUR, PERMISSION_CREER_PRODUIT)
    assert not a_permission(ROLE_VENDEUR, PERMISSION_AJUSTER_STOCK)
    assert not a_permission(ROLE_VENDEUR, PERMISSION_CONSULTER_PARAMETRES)
    assert not a_permission(ROLE_VENDEUR, PERMISSION_EXPORTER_DONNEES)
    assert not a_permission(ROLE_VENDEUR, PERMISSION_IMPORTER_DONNEES)

    with pytest.raises(PermissionRefuseeError):
        exiger_permission(ROLE_VENDEUR, PERMISSION_CREER_PRODUIT)


def test_role_inconnu_refuse():
    assert not role_valide("ADMIN")
    assert permissions_pour_role("ADMIN") == frozenset()
    assert not a_permission("ADMIN", PERMISSION_CREER_VENTE)

    with pytest.raises(PermissionRefuseeError):
        exiger_role_valide("ADMIN")

    with pytest.raises(PermissionRefuseeError):
        exiger_permission("ADMIN", PERMISSION_CREER_VENTE)
