"""Dashboard gerant placeholder visuel conforme a la maquette Phase 10."""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.components.icons import ui_icon


class GerantDashboardPage(QWidget):
    """Dashboard gerant en donnees fictives, sans requete ni logique metier."""

    voir_tout_demande = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(22)

        cards = QGridLayout()
        cards.setHorizontalSpacing(16)
        cards.addWidget(StatCard("Ventes du jour", "1 247 500 CDF", "+12,5% vs hier", "green", "cart"), 0, 0)
        cards.addWidget(StatCard("Transactions", "86", "+8,4% vs hier", "blue", "transactions"), 0, 1)
        cards.addWidget(StatCard("Produits en stock", "2 856", "0% vs hier", "green", "product"), 0, 2)
        cards.addWidget(StatCard("Stock faible", "43", "+5 vs hier", "orange", "warning"), 0, 3)
        cards.addWidget(StatCard("Expirations proches", "18", "+3 vs hier", "red", "calendar"), 0, 4)
        layout.addLayout(cards)

        middle = QHBoxLayout()
        middle.setSpacing(18)
        middle.addWidget(ChartPanel("Evolution des ventes (CDF)", "Aujourd'hui", ["18 mai", "19 mai", "20 mai", "21 mai", "22 mai", "23 mai", "24 mai"], [0.25, 0.42, 0.34, 0.66, 0.48, 0.82, 0.74]), 3)
        products_panel = ProductsPanel("Top produits vendus", [("Paracetamol 500mg (CP)", "152", "91 200"), ("Amoxicilline 500mg (CP)", "98", "78 400"), ("Vitamine C 500mg (CP)", "76", "53 200"), ("Ibuprofene 400mg (CP)", "64", "44 800"), ("Omeprazole 20mg (CP)", "45", "31 500")])
        products_panel.voir_tout_demande.connect(self.voir_tout_demande.emit)
        middle.addWidget(products_panel, 2)
        layout.addLayout(middle)

        bottom = QHBoxLayout()
        bottom.setSpacing(18)
        vendor_panel = VendorSummaryPanel()
        activity_panel = ActivityPanel()
        alert_panel = AlertPanel()
        vendor_panel.voir_tout_demande.connect(self.voir_tout_demande.emit)
        activity_panel.voir_tout_demande.connect(self.voir_tout_demande.emit)
        alert_panel.voir_tout_demande.connect(self.voir_tout_demande.emit)
        bottom.addWidget(vendor_panel, 1)
        bottom.addWidget(activity_panel, 1)
        bottom.addWidget(alert_panel, 1)
        layout.addLayout(bottom)


class StatCard(QFrame):
    def __init__(self, title: str, value: str, trend: str, color: str, icon: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(132)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(16)
        bubble = QLabel()
        bubble.setObjectName(f"iconBubble_{color}")
        bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble.setFixedSize(54, 54)
        bubble.setPixmap(ui_icon(icon, "#ffffff", 28).pixmap(28, 28))
        layout.addWidget(bubble)
        texts = QVBoxLayout()
        texts.setSpacing(7)
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        trend_label = QLabel(trend)
        trend_label.setObjectName("statTrend")
        texts.addWidget(title_label)
        texts.addWidget(value_label)
        texts.addWidget(trend_label)
        layout.addLayout(texts, 1)


class ChartPanel(QFrame):
    def __init__(self, title: str, period: str, labels: list[str], values: list[float]) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        period_button = QPushButton(period + "   v")
        period_button.setObjectName("smallButton")
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(period_button)
        layout.addLayout(header)
        layout.addWidget(LineChart(labels, values), 1)


class LineChart(QWidget):
    def __init__(self, labels: list[str], values: list[float]) -> None:
        super().__init__()
        self.labels = labels
        self.values = values
        self.setMinimumHeight(260)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 48, 18, self.width() - 24, self.height() - 38
        grid_pen = QPen(QColor("#e8eef2"), 1)
        painter.setPen(grid_pen)
        for i in range(5):
            y = top + (bottom - top) * i / 4
            painter.drawLine(left, int(y), right, int(y))
        for i, label in enumerate(self.labels):
            x = left + (right - left) * i / max(1, len(self.labels) - 1)
            painter.drawLine(int(x), top, int(x), bottom)
            painter.setPen(QColor("#65758b"))
            painter.drawText(int(x) - 18, bottom + 24, label)
            painter.setPen(grid_pen)
        points = [QPointF(left + (right - left) * i / (len(self.values) - 1), bottom - (bottom - top) * value) for i, value in enumerate(self.values)]
        fill = QPainterPath(points[0])
        for point in points[1:]:
            fill.lineTo(point)
        fill.lineTo(points[-1].x(), bottom)
        fill.lineTo(points[0].x(), bottom)
        fill.closeSubpath()
        painter.fillPath(fill, QColor(40, 167, 69, 35))
        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        painter.setPen(QPen(QColor("#18a345"), 3))
        painter.drawPath(path)
        painter.setBrush(QColor("#18a345"))
        painter.setPen(Qt.PenStyle.NoPen)
        for point in points:
            painter.drawEllipse(point, 5, 5)


class ProductsPanel(QFrame):
    voir_tout_demande = Signal(str)

    def __init__(self, title: str, rows: Iterable[tuple[str, str, str]]) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        view_all = QPushButton("Voir tout")
        view_all.setObjectName("smallButton")
        view_all.clicked.connect(lambda: self.voir_tout_demande.emit("details_top_produits"))
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(view_all)
        layout.addLayout(header)
        table = QGridLayout()
        table.setHorizontalSpacing(12)
        table.setVerticalSpacing(12)
        for col, text in enumerate(("Produit", "Quantite", "CA (CDF)")):
            label = QLabel(text)
            label.setObjectName("tableHeader")
            table.addWidget(label, 0, col)
        for index, (product, qty, ca) in enumerate(rows, start=1):
            table.addWidget(QLabel(f"{index}   {product}"), index, 0)
            table.addWidget(QLabel(qty), index, 1)
            table.addWidget(QLabel(ca), index, 2)
        layout.addLayout(table)


class VendorSummaryPanel(QFrame):
    voir_tout_demande = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        header = QHBoxLayout()
        title = QLabel("Synthese par vendeur")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch(1)
        view_all = QPushButton("Voir tout")
        view_all.setObjectName("smallButton")
        view_all.clicked.connect(lambda: self.voir_tout_demande.emit("details_vendeurs"))
        header.addWidget(view_all)
        layout.addLayout(header)
        for row in ("Jean K.        562 300        38        14 797", "Alice M.       358 900        25        14 356", "Paul B.        214 600        16        13 413", "Sophie L.      111 700         7        15 957"):
            label = QLabel(row)
            label.setObjectName("panelRow")
            layout.addWidget(label)
        total = QLabel("Total          1 247 500      86        14 506")
        total.setObjectName("greenRow")
        layout.addWidget(total)


class ActivityPanel(QFrame):
    voir_tout_demande = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        title = QLabel("Activites recentes")
        title.setObjectName("panelTitle")
        header = QHBoxLayout()
        view_all = QPushButton("Voir tout")
        view_all.setObjectName("smallButton")
        view_all.clicked.connect(lambda: self.voir_tout_demande.emit("details_activites"))
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(view_all)
        layout.addLayout(header)
        for row in ("Vente #VTE-00085 enregistree\n24 mai 2024 a 10:42", "Reception de stock - 32 produits\n24 mai 2024 a 09:15", "Facture #FAC-00045 creee\n24 mai 2024 a 08:47", "Produit Amoxicilline 500mg ajoute au stock\n24 mai 2024 a 08:20", "Alerte stock faible : Diclofenac 75mg\n24 mai 2024 a 07:58"):
            label = QLabel(row)
            label.setObjectName("activityRow")
            layout.addWidget(label)


class AlertPanel(QFrame):
    voir_tout_demande = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        title = QLabel("Alertes rapides")
        title.setObjectName("panelTitle")
        header = QHBoxLayout()
        view_all = QPushButton("Voir tout")
        view_all.setObjectName("smallButton")
        view_all.clicked.connect(lambda: self.voir_tout_demande.emit("details_alertes"))
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(view_all)
        layout.addLayout(header)
        layout.addWidget(QLabel("Stock faible"))
        for row in ("Diclofenac 75mg (CP)                         8", "Salbutamol sirop                              6", "Cotrimoxazole 480mg (CP)                      5"):
            label = QLabel(row)
            label.setObjectName("warningRow")
            layout.addWidget(label)
        layout.addSpacing(12)
        layout.addWidget(QLabel("Expirations proches"))
        for row in ("Amoxicilline 500mg (CP)              12/06/2024", "Metronidazole 250mg (CP)             18/06/2024", "Vitamine C 500mg (CP)                22/06/2024"):
            label = QLabel(row)
            label.setObjectName("dangerRow")
            layout.addWidget(label)
