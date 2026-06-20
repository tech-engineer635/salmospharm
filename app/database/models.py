"""Modeles SQLAlchemy officiels de SALMOSPHARM."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    __table_args__ = (
        CheckConstraint("doit_changer_mot_de_passe IN (0, 1)", name="ck_utilisateurs_doit_changer_mot_de_passe"),
        CheckConstraint("role IN ('GERANT', 'VENDEUR')", name="ck_utilisateurs_role"),
        CheckConstraint("actif IN (0, 1)", name="ck_utilisateurs_actif"),
        Index("idx_utilisateurs_role", "role"),
        Index("idx_utilisateurs_actif", "actif"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(Text, nullable=False)
    code_recuperation_hash: Mapped[str | None] = mapped_column(Text)
    doit_changer_mot_de_passe: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    role: Mapped[str] = mapped_column(Text, nullable=False)
    actif: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modifie_le: Mapped[str | None] = mapped_column(Text)

    mouvements_stock: Mapped[list[MouvementStock]] = relationship(back_populates="utilisateur")
    ventes: Mapped[list[Vente]] = relationship(back_populates="vendeur")
    journaux_activite: Mapped[list[JournalActivite]] = relationship(back_populates="utilisateur")


class Categorie(Base):
    __tablename__ = "categories"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modifie_le: Mapped[str | None] = mapped_column(Text)

    produits: Mapped[list[Produit]] = relationship(back_populates="categorie")


class Produit(Base):
    __tablename__ = "produits"
    __table_args__ = (
        CheckConstraint("prix_vente >= 0", name="ck_produits_prix_vente"),
        CheckConstraint("stock_minimum >= 0", name="ck_produits_stock_minimum"),
        CheckConstraint("actif IN (0, 1)", name="ck_produits_actif"),
        Index("idx_produits_nom", "nom"),
        Index("idx_produits_code_barres", "code_barres"),
        Index("idx_produits_categorie", "categorie_id"),
        Index("idx_produits_actif", "actif"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categorie_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    code_barres: Mapped[str | None] = mapped_column(Text, unique=True)
    prix_vente: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_minimum: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    description: Mapped[str | None] = mapped_column(Text)
    actif: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modifie_le: Mapped[str | None] = mapped_column(Text)

    categorie: Mapped[Categorie | None] = relationship(back_populates="produits")
    lots: Mapped[list[LotProduit]] = relationship(back_populates="produit")
    mouvements_stock: Mapped[list[MouvementStock]] = relationship(back_populates="produit")
    lignes_vente: Mapped[list[LigneVente]] = relationship(back_populates="produit")
    alertes: Mapped[list[Alerte]] = relationship(back_populates="produit")


class LotProduit(Base):
    __tablename__ = "lots_produits"
    __table_args__ = (
        UniqueConstraint("produit_id", "numero_lot", name="uq_lots_produits_produit_numero_lot"),
        CheckConstraint("quantite >= 0", name="ck_lots_produits_quantite"),
        CheckConstraint("prix_achat >= 0", name="ck_lots_produits_prix_achat"),
        Index("idx_lots_produits_produit", "produit_id"),
        Index("idx_lots_produits_expiration", "date_expiration"),
        Index("idx_lots_produits_quantite", "quantite"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produit_id: Mapped[int] = mapped_column(
        ForeignKey("produits.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
    )
    numero_lot: Mapped[str | None] = mapped_column(Text)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    prix_achat: Mapped[int] = mapped_column(Integer, nullable=False)
    date_expiration: Mapped[str | None] = mapped_column(Text)
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modifie_le: Mapped[str | None] = mapped_column(Text)

    produit: Mapped[Produit] = relationship(back_populates="lots")
    mouvements_stock: Mapped[list[MouvementStock]] = relationship(back_populates="lot")
    lignes_vente: Mapped[list[LigneVente]] = relationship(back_populates="lot")
    alertes: Mapped[list[Alerte]] = relationship(back_populates="lot")


class MouvementStock(Base):
    __tablename__ = "mouvements_stock"
    __table_args__ = (
        CheckConstraint(
            "type_mouvement IN ('ENTREE','SORTIE','AJUSTEMENT','PERTE','EXPIRATION')",
            name="ck_mouvements_stock_type",
        ),
        CheckConstraint("quantite > 0", name="ck_mouvements_stock_quantite"),
        Index("idx_mouvements_stock_produit", "produit_id"),
        Index("idx_mouvements_stock_lot", "lot_id"),
        Index("idx_mouvements_stock_utilisateur", "utilisateur_id"),
        Index("idx_mouvements_stock_date", "cree_le"),
        Index("idx_mouvements_stock_type", "type_mouvement"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produit_id: Mapped[int] = mapped_column(
        ForeignKey("produits.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots_produits.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    utilisateur_id: Mapped[int | None] = mapped_column(
        ForeignKey("utilisateurs.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    type_mouvement: Mapped[str] = mapped_column(Text, nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    motif: Mapped[str | None] = mapped_column(Text)
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    produit: Mapped[Produit] = relationship(back_populates="mouvements_stock")
    lot: Mapped[LotProduit | None] = relationship(back_populates="mouvements_stock")
    utilisateur: Mapped[Utilisateur | None] = relationship(back_populates="mouvements_stock")


class Vente(Base):
    __tablename__ = "ventes"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_ventes_total"),
        CheckConstraint("montant_recu >= total", name="ck_ventes_montant_recu"),
        CheckConstraint("statut = 'VALIDEE'", name="ck_ventes_statut"),
        Index("idx_ventes_vendeur", "vendeur_id"),
        Index("idx_ventes_date", "cree_le"),
        Index("idx_ventes_numero", "numero_vente"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_vente: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    vendeur_id: Mapped[int | None] = mapped_column(
        ForeignKey("utilisateurs.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    montant_recu: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'VALIDEE'"))
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    vendeur: Mapped[Utilisateur | None] = relationship(back_populates="ventes")
    lignes: Mapped[list[LigneVente]] = relationship(back_populates="vente")


class LigneVente(Base):
    __tablename__ = "lignes_vente"
    __table_args__ = (
        CheckConstraint("quantite > 0", name="ck_lignes_vente_quantite"),
        CheckConstraint("prix_unitaire >= 0", name="ck_lignes_vente_prix_unitaire"),
        CheckConstraint("sous_total >= 0", name="ck_lignes_vente_sous_total"),
        Index("idx_lignes_vente_vente", "vente_id"),
        Index("idx_lignes_vente_produit", "produit_id"),
        Index("idx_lignes_vente_lot", "lot_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vente_id: Mapped[int] = mapped_column(
        ForeignKey("ventes.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
    )
    produit_id: Mapped[int] = mapped_column(
        ForeignKey("produits.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots_produits.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    prix_unitaire: Mapped[int] = mapped_column(Integer, nullable=False)
    sous_total: Mapped[int] = mapped_column(Integer, nullable=False)

    vente: Mapped[Vente] = relationship(back_populates="lignes")
    produit: Mapped[Produit] = relationship(back_populates="lignes_vente")
    lot: Mapped[LotProduit | None] = relationship(back_populates="lignes_vente")


class Alerte(Base):
    __tablename__ = "alertes"
    __table_args__ = (
        CheckConstraint(
            "type_alerte IN ('STOCK_FAIBLE','EXPIRATION_PROCHE','PRODUIT_EXPIRE')",
            name="ck_alertes_type",
        ),
        CheckConstraint("est_lue IN (0, 1)", name="ck_alertes_est_lue"),
        Index("idx_alertes_produit", "produit_id"),
        Index("idx_alertes_lot", "lot_id"),
        Index("idx_alertes_est_lue", "est_lue"),
        Index("idx_alertes_date", "cree_le"),
        Index("idx_alertes_type", "type_alerte"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produit_id: Mapped[int] = mapped_column(
        ForeignKey("produits.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots_produits.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    type_alerte: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    est_lue: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    produit: Mapped[Produit] = relationship(back_populates="alertes")
    lot: Mapped[LotProduit | None] = relationship(back_populates="alertes")


class JournalActivite(Base):
    __tablename__ = "journaux_activite"
    __table_args__ = (
        Index("idx_journaux_utilisateur", "utilisateur_id"),
        Index("idx_journaux_date", "cree_le"),
        Index("idx_journaux_table_cible", "table_cible"),
        Index("idx_journaux_action", "action"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utilisateur_id: Mapped[int | None] = mapped_column(
        ForeignKey("utilisateurs.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    table_cible: Mapped[str | None] = mapped_column(Text)
    element_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str | None] = mapped_column(Text)
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    utilisateur: Mapped[Utilisateur | None] = relationship(back_populates="journaux_activite")


class Parametre(Base):
    __tablename__ = "parametres"
    __table_args__ = (
        CheckConstraint("devise = 'CDF'", name="ck_parametres_devise"),
        CheckConstraint("seuil_expiration_jours > 0", name="ck_parametres_seuil_expiration_jours"),
        CheckConstraint("largeur_ticket IN (58, 80)", name="ck_parametres_largeur_ticket"),
        CheckConstraint("impression_auto IN (0, 1)", name="ck_parametres_impression_auto"),
        CheckConstraint("sauvegarde_auto IN (0, 1)", name="ck_parametres_sauvegarde_auto"),
        CheckConstraint(
            "frequence_sauvegarde IN ('FERMETURE','QUOTIDIENNE','MANUELLE')",
            name="ck_parametres_frequence_sauvegarde",
        ),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_pharmacie: Mapped[str] = mapped_column(Text, nullable=False)
    telephone: Mapped[str | None] = mapped_column(Text)
    adresse: Mapped[str | None] = mapped_column(Text)
    chemin_logo: Mapped[str | None] = mapped_column(Text)
    devise: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'CDF'"))
    seuil_expiration_jours: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("30"))
    nom_imprimante: Mapped[str | None] = mapped_column(Text)
    largeur_ticket: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("80"))
    impression_auto: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    sauvegarde_auto: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    frequence_sauvegarde: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'QUOTIDIENNE'"))
    derniere_sauvegarde: Mapped[str | None] = mapped_column(Text)
    cree_le: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modifie_le: Mapped[str | None] = mapped_column(Text)
