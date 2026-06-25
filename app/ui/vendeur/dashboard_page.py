"""Dashboard vendeur placeholder visuel conforme a la maquette Phase 10."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.services.auth_service import SessionUtilisateur
from app.ui.components.icons import ui_icon


class VendeurDashboardPage(QWidget):
    """Dashboard vendeur en donnees fictives, sans acces base."""

    voir_tout_demande = Signal(str)

    def __init__(self, session_utilisateur: SessionUtilisateur, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self.setObjectName("dashboardPage")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(22)

        cards = QGridLayout()
        cards.setHorizontalSpacing(16)
        cards.addWidget(StatCard("Ventes du jour", "285 500 CDF", "+12% vs hier", "green", "cart"), 0, 0)
        cards.addWidget(StatCard("Transactions", "28", "+4 vs hier", "blue", "transactions"), 0, 1)
        cards.addWidget(StatCard("Total encaisse (CDF)", "285 500", "+12% vs hier", "green", "wallet"), 0, 2)
        cards.addWidget(StatCard("Articles vendus", "86", "+9 vs hier", "blue", "product"), 0, 3)
        layout.addLayout(cards)

        middle = QHBoxLayout()
        middle.setSpacing(18)
        middle.addWidget(ChartPanel(), 3)
        recent_sales = RecentSalesPanel()
        recent_sales.voir_tout_demande.connect(self.voir_tout_demande.emit)
        middle.addWidget(recent_sales, 2)
        layout.addLayout(middle)

        bottom = QHBoxLayout()
        bottom.setSpacing(18)
        bottom.addWidget(ProductsPanel(), 3)
        bottom.addWidget(PerformancePanel(), 2)
        layout.addLayout(bottom)


class StatCard(QFrame):
    def __init__(self, title: str, value: str, trend: str, color: str, icon: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(126)
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
        for object_name, text in (("statTitle", title), ("statValue", value), ("statTrend", trend)):
            label = QLabel(text)
            label.setObjectName(object_name)
            texts.addWidget(label)
        layout.addLayout(texts, 1)


class ChartPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        header = QHBoxLayout()
        title = QLabel("Evolution des ventes (CDF)")
        title.setObjectName("panelTitle")
        period = QPushButton("Aujourd'hui   v")
        period.setObjectName("smallButton")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(period)
        layout.addLayout(header)
        layout.addWidget(LineChart(["08h", "10h", "12h", "14h", "16h", "18h", "20h"], [0.05, 0.14, 0.34, 0.46, 0.58, 0.72, 0.84]), 1)


class LineChart(QWidget):
    def __init__(self, labels: list[str], values: list[float]) -> None:
        super().__init__()
        self.labels = labels
        self.values = values
        self.setMinimumHeight(260)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 56, 18, self.width() - 24, self.height() - 38
        painter.setPen(QPen(QColor("#e8eef2"), 1))
        for i in range(5):
            y = top + (bottom - top) * i / 4
            painter.drawLine(left, int(y), right, int(y))
        for i, label in enumerate(self.labels):
            x = left + (right - left) * i / max(1, len(self.labels) - 1)
            painter.drawLine(int(x), top, int(x), bottom)
            painter.setPen(QColor("#65758b"))
            painter.drawText(int(x) - 14, bottom + 24, label)
            painter.setPen(QPen(QColor("#e8eef2"), 1))
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
        painter.setPen(QPen(QColor("#15a348"), 3))
        painter.drawPath(path)
        painter.setBrush(QColor("#15a348"))
        painter.setPen(Qt.PenStyle.NoPen)
        for point in points:
            painter.drawEllipse(point, 5, 5)


class RecentSalesPanel(QFrame):
    voir_tout_demande = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        header = QHBoxLayout()
        title = QLabel("Ventes recentes")
        title.setObjectName("panelTitle")
        link = QPushButton("Voir tout")
        link.setObjectName("smallButton")
        link.clicked.connect(lambda: self.voir_tout_demande.emit("details_ventes_recentes"))
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(link)
        layout.addLayout(header)
        rows = [("VTE-2024-0058", "24 mai 2024 - 14:32\nEspeces", "32 000 CDF"), ("VTE-2024-0057", "24 mai 2024 - 13:45\nEspeces", "18 500 CDF"), ("VTE-2024-0056", "24 mai 2024 - 12:26\nEspeces", "25 000 CDF"), ("VTE-2024-0055", "24 mai 2024 - 11:18\nEspeces", "47 000 CDF"), ("VTE-2024-0054", "24 mai 2024 - 10:05\nEspeces", "21 000 CDF")]
        for ref, meta, amount in rows:
            row = QHBoxLayout()
            icon = QLabel()
            icon.setObjectName("saleIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setPixmap(ui_icon("ticket", "#516276", 20).pixmap(20, 20))
            row.addWidget(icon)
            text = QLabel(f"{ref}\n{meta}")
            text.setObjectName("saleText")
            row.addWidget(text, 1)
            price = QLabel(amount)
            price.setObjectName("saleAmount")
            row.addWidget(price)
            layout.addLayout(row)


class ProductsPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        title = QLabel("Produits les plus vendus aujourd'hui")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        for col, header in enumerate(("Produit", "Quantite vendue", "Chiffre d'affaires (CDF)")):
            label = QLabel(header)
            label.setObjectName("tableHeader")
            grid.addWidget(label, 0, col)
        rows = [("Paracetamol 500mg (CP)", "18", "18 000"), ("Amoxicilline 500mg (CP)", "14", "14 000"), ("Vitamine C 500mg (CP)", "10", "7 500"), ("Ibuprofene 400mg (CP)", "9", "5 400"), ("Omeprazole 20mg (CP)", "7", "4 900")]
        for index, (product, qty, ca) in enumerate(rows, start=1):
            grid.addWidget(QLabel(f"{index}   {product}"), index, 0)
            grid.addWidget(QLabel(qty), index, 1)
            grid.addWidget(QLabel(ca), index, 2)
        layout.addLayout(grid)


class PerformancePanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("contentPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        title = QLabel("Objectifs & performance")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Objectif quotidien                                      500 000 CDF"))
        row = QHBoxLayout()
        row.addWidget(DonutProgress(), 1)
        details = QVBoxLayout()
        details.addWidget(QLabel("Realise                                      285 500 CDF"))
        details.addWidget(QLabel("Reste a atteindre                         214 500 CDF"))
        row.addLayout(details, 2)
        layout.addLayout(row)
        layout.addWidget(QLabel("Progression                                      57%"))


class DonutProgress(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(126, 126)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(14, 14, -14, -14)
        painter.setPen(QPen(QColor("#e8edf1"), 12))
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(QPen(QColor("#16a33a"), 12))
        painter.drawArc(rect, 90 * 16, -205 * 16)
        painter.setPen(QColor("#16a33a"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "57%")
