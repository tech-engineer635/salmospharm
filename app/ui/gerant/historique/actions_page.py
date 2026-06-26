"""Journal des actions systeme pour le gerant."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import JournalActionItem, RapportService
from app.ui.components.icons import ui_icon


class HistoriqueActionsPage(QWidget):
    """Ecran de consultation du journal systeme."""

    def __init__(self, session_utilisateur: SessionUtilisateur, rapport_service: RapportService | None = None, autoload: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionHistoryPage")
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._items: list[JournalActionItem] = []
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Historique des actions")
        title.setObjectName("reportsTitle")
        subtitle = QLabel("Consultez toutes les actions effectuees dans le systeme")
        subtitle.setObjectName("reportsSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("reportsSearch")
        self.search_input.setPlaceholderText("Rechercher utilisateur, action, module...")
        self.search_input.addAction(ui_icon("search", "#506b92", 18), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._charger)
        header.addLayout(title_box, 1)
        header.addWidget(self.search_input)
        layout.addLayout(header)

        filter_panel = QFrame()
        filter_panel.setObjectName("reportsPanel")
        filters = QHBoxLayout(filter_panel)
        filters.setContentsMargins(18, 14, 18, 14)
        filters.setSpacing(14)
        for label, value in (("Date", "Toutes les dates"), ("Utilisateur", "Tous les utilisateurs"), ("Type d'action", "Tous les types")):
            box = QVBoxLayout()
            title_label = QLabel(label)
            title_label.setObjectName("reportMetricTitle")
            value_label = QLabel(value)
            value_label.setObjectName("filterPill")
            box.addWidget(title_label)
            box.addWidget(value_label)
            filters.addLayout(box, 1)
        reset = QPushButton("Reinitialiser")
        reset.setObjectName("outlineButton")
        reset.setIcon(ui_icon("refresh", "#0b3567", 16))
        reset.clicked.connect(lambda: self.search_input.clear())
        filters.addWidget(reset)
        layout.addWidget(filter_panel)

        body = QHBoxLayout()
        body.setSpacing(16)
        panel = QFrame()
        panel.setObjectName("reportsPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_title = QLabel("Journal des actions")
        panel_title.setObjectName("reportsPanelTitle")
        panel_title.setContentsMargins(18, 16, 18, 12)
        panel_layout.addWidget(panel_title)
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("reportsTable")
        self.table.setHorizontalHeaderLabels(["Heure", "Utilisateur", "Action", "Details", "Module", "Statut"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(470)
        panel_layout.addWidget(self.table)
        body.addWidget(panel, 1)

        side = QFrame()
        side.setObjectName("reportsPanel")
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(14)
        side_title = QLabel("Resume d'aujourd'hui")
        side_title.setObjectName("reportsPanelTitle")
        self.total_actions_label = QLabel("0")
        self.total_actions_label.setObjectName("reportMetricValue")
        side_layout.addWidget(side_title)
        for text in ("Connexions", "Ventes enregistrees", "Produits modifies", "Stock ajuste", "Factures imprimees"):
            row = QLabel(text)
            row.setObjectName("actionSummaryRow")
            side_layout.addWidget(row)
        side_layout.addStretch(1)
        side_layout.addWidget(QLabel("Total des actions"))
        side_layout.addWidget(self.total_actions_label)
        body.addWidget(side, 0)
        layout.addLayout(body, 1)

    def _charger(self) -> None:
        try:
            self._items = self._rapport_service.lister_actions(self.session_utilisateur, terme=self.search_input.text())
            self._remplir()
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _remplir(self) -> None:
        self.table.setRowCount(0)
        for item in self._items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [item.date_action, item.utilisateur_nom, _label_action(item.action), item.details, item.module, "Succes"]
            for column, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, column, table_item)
        self.total_actions_label.setText(str(len(self._items)))


def _label_action(action: str) -> str:
    return action.replace("_", " ").capitalize()
