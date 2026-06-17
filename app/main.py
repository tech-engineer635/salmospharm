"""Point d'entree minimal de SALMOSPHARM 133."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.paths import ensure_app_directories
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


APP_TITLE = "SALMOSPHARM 133"


class MainWindow(QMainWindow):
    """Fenetre principale minimale pour verifier PySide6."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(480, 260)

        title_label = QLabel(APP_TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("titleLabel")

        message_label = QLabel("Application lancée avec succès")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setObjectName("messageLabel")

        quit_button = QPushButton("Quitter")
        quit_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(18)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addWidget(quit_button, alignment=Qt.AlignmentFlag.AlignCenter)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


def apply_style(app: QApplication) -> None:
    app.setStyleSheet(
        """
        QMainWindow {
            background-color: #f5f7f8;
        }
        QLabel#titleLabel {
            color: #102a43;
            font-size: 26px;
            font-weight: 700;
        }
        QLabel#messageLabel {
            color: #334e68;
            font-size: 15px;
        }
        QPushButton {
            background-color: #15803d;
            border: none;
            border-radius: 6px;
            color: white;
            font-size: 14px;
            padding: 10px 24px;
        }
        QPushButton:hover {
            background-color: #166534;
        }
        QPushButton:pressed {
            background-color: #14532d;
        }
        """
    )


def main() -> int:
    ensure_app_directories()

    app = QApplication(sys.argv)
    apply_style(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
