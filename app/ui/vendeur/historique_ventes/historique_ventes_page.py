"""Historique personnel des ventes vendeur."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from app.ui.gerant.historique.historique_page import HistoriqueVentesGerantPage


class HistoriqueVentesVendeurPage(HistoriqueVentesGerantPage):
    """Meme presentation que le gerant, limitee par le service aux ventes du vendeur."""

    def _build_ui(self) -> None:
        super()._build_ui()
        self.export_button.hide()
        for label in self.findChildren(QLabel):
            if label.objectName() == "reportsTitle":
                label.setText("Historique des ventes")
            elif label.objectName() == "reportsSubtitle":
                label.setText("Consultez vos ventes validees et reimprimez vos propres recus.")
