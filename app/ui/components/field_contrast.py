"""Contraste stable des champs, independant du theme Windows."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QWidget,
)


TEXT_COLOR = QColor("#17324d")
PLACEHOLDER_COLOR = QColor("#66788a")
DISABLED_TEXT_COLOR = QColor("#526579")
BASE_COLOR = QColor("#ffffff")
DISABLED_BASE_COLOR = QColor("#f1f5f8")
SELECTION_COLOR = QColor("#0b5fa5")


def appliquer_contraste_champs(root: QWidget) -> None:
    """Force des roles de palette lisibles pour tous les champs du widget."""

    widgets: list[QWidget] = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        if isinstance(widget, (QLabel, QCheckBox, QRadioButton)):
            palette = widget.palette()
            for group in (
                QPalette.ColorGroup.Active,
                QPalette.ColorGroup.Inactive,
            ):
                palette.setColor(
                    group, QPalette.ColorRole.WindowText, TEXT_COLOR
                )
                palette.setColor(
                    group, QPalette.ColorRole.ButtonText, TEXT_COLOR
                )
            palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.WindowText,
                DISABLED_TEXT_COLOR,
            )
            palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.ButtonText,
                DISABLED_TEXT_COLOR,
            )
            widget.setPalette(palette)
            continue
        if not isinstance(widget, (QLineEdit, QComboBox, QAbstractSpinBox)):
            continue
        palette = widget.palette()
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            palette.setColor(group, QPalette.ColorRole.Text, TEXT_COLOR)
            palette.setColor(group, QPalette.ColorRole.ButtonText, TEXT_COLOR)
            palette.setColor(group, QPalette.ColorRole.PlaceholderText, PLACEHOLDER_COLOR)
            palette.setColor(group, QPalette.ColorRole.Base, BASE_COLOR)
            palette.setColor(group, QPalette.ColorRole.Highlight, SELECTION_COLOR)
            palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            DISABLED_TEXT_COLOR,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            DISABLED_TEXT_COLOR,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.PlaceholderText,
            DISABLED_TEXT_COLOR,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Base,
            DISABLED_BASE_COLOR,
        )
        widget.setPalette(palette)

        if isinstance(widget, QComboBox):
            # Le popup est une vue native séparée : sous certains thèmes Windows,
            # il n'hérite pas de la couleur de texte définie sur le QComboBox.
            popup_palette = widget.view().palette()
            for group in (
                QPalette.ColorGroup.Active,
                QPalette.ColorGroup.Inactive,
            ):
                popup_palette.setColor(group, QPalette.ColorRole.Text, TEXT_COLOR)
                popup_palette.setColor(group, QPalette.ColorRole.WindowText, TEXT_COLOR)
                popup_palette.setColor(group, QPalette.ColorRole.Base, BASE_COLOR)
                popup_palette.setColor(group, QPalette.ColorRole.Window, BASE_COLOR)
                popup_palette.setColor(group, QPalette.ColorRole.Highlight, SELECTION_COLOR)
                popup_palette.setColor(
                    group,
                    QPalette.ColorRole.HighlightedText,
                    QColor("#ffffff"),
                )
            widget.view().setPalette(popup_palette)
