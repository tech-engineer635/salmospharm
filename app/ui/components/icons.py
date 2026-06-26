"""Petites icones vectorielles dessinees en PySide pour l'UI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def ui_icon(name: str, color: str = "#526173", size: int = 24) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), max(1.8, size * 0.085), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    s = size / 24

    if name in {"dashboard", "grid"}:
        for x, y in ((4, 4), (14, 4), (4, 14), (14, 14)):
            painter.drawRoundedRect(x * s, y * s, 6 * s, 6 * s, 1.4 * s, 1.4 * s)
    elif name in {"produits", "product", "stock"}:
        painter.drawPolygon([
            _p(12, 3, s), _p(20, 8, s), _p(12, 13, s), _p(4, 8, s)
        ])
        painter.drawLine(4 * s, 8 * s, 4 * s, 16 * s)
        painter.drawLine(20 * s, 8 * s, 20 * s, 16 * s)
        painter.drawLine(12 * s, 13 * s, 12 * s, 21 * s)
        painter.drawPolygon([
            _p(4, 16, s), _p(12, 21, s), _p(20, 16, s), _p(20, 8, s), _p(12, 13, s), _p(4, 8, s)
        ])
    elif name in {"ventes", "cart"}:
        painter.drawPolyline([_p(3, 5, s), _p(6, 5, s), _p(8, 15, s), _p(18, 15, s), _p(21, 8, s), _p(7, 8, s)])
        painter.drawEllipse(8 * s, 18 * s, 2.4 * s, 2.4 * s)
        painter.drawEllipse(17 * s, 18 * s, 2.4 * s, 2.4 * s)
    elif name in {"factures", "ticket"}:
        painter.drawRoundedRect(6 * s, 3 * s, 12 * s, 18 * s, 2 * s, 2 * s)
        painter.drawLine(9 * s, 8 * s, 15 * s, 8 * s)
        painter.drawLine(9 * s, 12 * s, 15 * s, 12 * s)
        painter.drawLine(9 * s, 16 * s, 13 * s, 16 * s)
    elif name in {"rapports", "report"}:
        painter.drawRoundedRect(4 * s, 13 * s, 4 * s, 7 * s, 1 * s, 1 * s)
        painter.drawRoundedRect(10 * s, 9 * s, 4 * s, 11 * s, 1 * s, 1 * s)
        painter.drawRoundedRect(16 * s, 5 * s, 4 * s, 15 * s, 1 * s, 1 * s)
    elif name in {"vendeurs", "users"}:
        painter.drawEllipse(8 * s, 4 * s, 6 * s, 6 * s)
        painter.drawArc(5 * s, 12 * s, 12 * s, 8 * s, 0, 180 * 16)
        painter.drawEllipse(16 * s, 8 * s, 4 * s, 4 * s)
        painter.drawArc(14 * s, 14 * s, 8 * s, 5 * s, 0, 180 * 16)
    elif name in {"historique", "history"}:
        painter.drawArc(4 * s, 5 * s, 15 * s, 15 * s, 40 * 16, 285 * 16)
        painter.drawLine(5 * s, 6 * s, 5 * s, 11 * s)
        painter.drawLine(5 * s, 6 * s, 10 * s, 6 * s)
        painter.drawLine(12 * s, 9 * s, 12 * s, 13 * s)
        painter.drawLine(12 * s, 13 * s, 15 * s, 15 * s)
    elif name in {"alertes", "bell"}:
        painter.drawArc(7 * s, 5 * s, 10 * s, 10 * s, 0, 180 * 16)
        painter.drawLine(7 * s, 10 * s, 5 * s, 17 * s)
        painter.drawLine(17 * s, 10 * s, 19 * s, 17 * s)
        painter.drawLine(5 * s, 17 * s, 19 * s, 17 * s)
        painter.drawArc(10 * s, 18 * s, 4 * s, 3 * s, 180 * 16, 180 * 16)
    elif name in {"parametres", "settings"}:
        painter.drawEllipse(9 * s, 9 * s, 6 * s, 6 * s)
        for x1, y1, x2, y2 in ((12, 3, 12, 6), (12, 18, 12, 21), (3, 12, 6, 12), (18, 12, 21, 12), (5, 5, 7, 7), (17, 17, 19, 19), (19, 5, 17, 7), (7, 17, 5, 19)):
            painter.drawLine(x1 * s, y1 * s, x2 * s, y2 * s)
    elif name in {"search"}:
        painter.drawEllipse(5 * s, 5 * s, 10 * s, 10 * s)
        painter.drawLine(14 * s, 14 * s, 20 * s, 20 * s)
    elif name in {"calendar"}:
        painter.drawRoundedRect(4 * s, 5 * s, 16 * s, 15 * s, 2 * s, 2 * s)
        painter.drawLine(4 * s, 9 * s, 20 * s, 9 * s)
        painter.drawLine(8 * s, 3 * s, 8 * s, 7 * s)
        painter.drawLine(16 * s, 3 * s, 16 * s, 7 * s)
    elif name in {"menu"}:
        painter.drawLine(6 * s, 7 * s, 18 * s, 7 * s)
        painter.drawLine(6 * s, 12 * s, 18 * s, 12 * s)
        painter.drawLine(6 * s, 17 * s, 18 * s, 17 * s)
    elif name in {"money", "wallet"}:
        painter.drawRoundedRect(4 * s, 7 * s, 16 * s, 11 * s, 2 * s, 2 * s)
        painter.drawRoundedRect(13 * s, 10 * s, 7 * s, 5 * s, 2 * s, 2 * s)
        painter.drawEllipse(16 * s, 12 * s, 1.2 * s, 1.2 * s)
    elif name in {"transactions", "receipt"}:
        painter.drawRoundedRect(6 * s, 4 * s, 12 * s, 16 * s, 2 * s, 2 * s)
        painter.drawLine(9 * s, 8 * s, 15 * s, 8 * s)
        painter.drawLine(9 * s, 12 * s, 15 * s, 12 * s)
        painter.drawLine(9 * s, 16 * s, 14 * s, 16 * s)
    elif name in {"warning"}:
        path = QPainterPath()
        path.moveTo(12 * s, 4 * s)
        path.lineTo(21 * s, 20 * s)
        path.lineTo(3 * s, 20 * s)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(12 * s, 9 * s, 12 * s, 14 * s)
        painter.drawPoint(12 * s, 17 * s)
    elif name in {"plus", "add"}:
        painter.drawLine(12 * s, 5 * s, 12 * s, 19 * s)
        painter.drawLine(5 * s, 12 * s, 19 * s, 12 * s)
    elif name in {"upload", "import"}:
        painter.drawLine(12 * s, 16 * s, 12 * s, 4 * s)
        painter.drawLine(8 * s, 8 * s, 12 * s, 4 * s)
        painter.drawLine(16 * s, 8 * s, 12 * s, 4 * s)
        painter.drawRoundedRect(5 * s, 16 * s, 14 * s, 4 * s, 1.5 * s, 1.5 * s)
    elif name in {"download"}:
        painter.drawLine(12 * s, 4 * s, 12 * s, 16 * s)
        painter.drawLine(8 * s, 12 * s, 12 * s, 16 * s)
        painter.drawLine(16 * s, 12 * s, 12 * s, 16 * s)
        painter.drawRoundedRect(5 * s, 18 * s, 14 * s, 3 * s, 1.5 * s, 1.5 * s)
    elif name in {"print", "printer"}:
        painter.drawRoundedRect(6 * s, 3 * s, 12 * s, 6 * s, 1.5 * s, 1.5 * s)
        painter.drawRoundedRect(4 * s, 9 * s, 16 * s, 8 * s, 2 * s, 2 * s)
        painter.drawRoundedRect(7 * s, 14 * s, 10 * s, 7 * s, 1.5 * s, 1.5 * s)
        painter.drawPoint(17 * s, 12 * s)
    elif name in {"close", "x"}:
        painter.drawLine(6 * s, 6 * s, 18 * s, 18 * s)
        painter.drawLine(18 * s, 6 * s, 6 * s, 18 * s)
    elif name in {"filter"}:
        painter.drawPolygon([_p(4, 5, s), _p(20, 5, s), _p(14, 12, s), _p(14, 19, s), _p(10, 21, s), _p(10, 12, s)])
    elif name in {"tag"}:
        painter.drawRoundedRect(5 * s, 5 * s, 14 * s, 14 * s, 2 * s, 2 * s)
        painter.drawLine(5 * s, 12 * s, 12 * s, 19 * s)
        painter.drawEllipse(14 * s, 8 * s, 2 * s, 2 * s)
    elif name in {"edit", "pen"}:
        painter.drawLine(6 * s, 18 * s, 17 * s, 7 * s)
        painter.drawLine(15 * s, 5 * s, 19 * s, 9 * s)
        painter.drawLine(6 * s, 18 * s, 5 * s, 21 * s)
        painter.drawLine(5 * s, 21 * s, 8 * s, 20 * s)
    elif name in {"refresh", "reload"}:
        painter.drawArc(5 * s, 5 * s, 14 * s, 14 * s, 35 * 16, 270 * 16)
        painter.drawLine(17 * s, 5 * s, 20 * s, 5 * s)
        painter.drawLine(20 * s, 5 * s, 20 * s, 8 * s)
    else:
        painter.drawEllipse(5 * s, 5 * s, 14 * s, 14 * s)

    painter.end()
    return QIcon(pixmap)


def _p(x: float, y: float, scale: float):
    from PySide6.QtCore import QPointF

    return QPointF(x * scale, y * scale)
