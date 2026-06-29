"""Composants visuels partages par les tableaux de bord."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ui.components.icons import ui_icon


class DashboardMetricCard(QFrame):
    """Carte KPI compacte avec icone, valeur et tendance."""

    def __init__(self, title: str, icon: str, tone: str) -> None:
        super().__init__()
        self.setObjectName("dashboardMetricCard")
        self.setMinimumWidth(0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(10)
        bubble = QLabel()
        bubble.setObjectName(f"dashboardMetricIcon_{tone}")
        bubble.setFixedSize(46, 46)
        bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble.setPixmap(ui_icon(icon, "#ffffff", 22).pixmap(22, 22))
        layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("dashboardMetricTitle")
        title_label.setWordWrap(True)
        self.value_label = QLabel("0")
        self.value_label.setObjectName("dashboardMetricValue")
        self.trend_label = QLabel("—")
        self.trend_label.setObjectName("dashboardMetricTrend")
        self.trend_label.setWordWrap(True)
        texts.addWidget(title_label)
        texts.addWidget(self.value_label)
        texts.addWidget(self.trend_label)
        layout.addLayout(texts, 1)

    def set_data(self, value: str, trend: float | None = None, text: str = "") -> None:
        self.value_label.setText(value)
        if trend is None:
            self.trend_label.setText(text or "Données du jour")
            self.trend_label.setProperty("trend", "neutral")
        else:
            arrow = "↗" if trend > 0 else ("↘" if trend < 0 else "—")
            self.trend_label.setText(f"{arrow} {trend:+.1f}% vs période précédente")
            self.trend_label.setProperty(
                "trend", "positive" if trend > 0 else ("negative" if trend < 0 else "neutral")
            )
        self.trend_label.style().unpolish(self.trend_label)
        self.trend_label.style().polish(self.trend_label)


def panel_header(title: str, action: str = "") -> tuple[QHBoxLayout, QPushButton | None]:
    row = QHBoxLayout()
    label = QLabel(title)
    label.setObjectName("dashboardPanelTitle")
    row.addWidget(label)
    row.addStretch(1)
    button = None
    if action:
        button = QPushButton(action)
        button.setObjectName("dashboardLinkButton")
        row.addWidget(button)
    return row, button


def empty_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("dashboardEmpty")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label
