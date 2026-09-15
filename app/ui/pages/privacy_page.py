from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from app.core.privacy_manager import PrivacyManager


class PrivacyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("Privacy")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        statement = QLabel(PrivacyManager.get_privacy_statement())
        statement.setWordWrap(True)
        card_layout.addWidget(statement)
        root.addWidget(card)

        disclaimer_card = QFrame()
        disclaimer_card.setObjectName("Card")
        disclaimer_layout = QVBoxLayout(disclaimer_card)
        disclaimer_layout.setContentsMargins(20, 18, 20, 18)
        disclaimer_title = QLabel("Health Disclaimer")
        disclaimer_title.setStyleSheet("font-weight: 700;")
        disclaimer_layout.addWidget(disclaimer_title)
        disclaimer = QLabel(PrivacyManager.get_medical_disclaimer())
        disclaimer.setWordWrap(True)
        disclaimer_layout.addWidget(disclaimer)
        root.addWidget(disclaimer_card)

        root.addStretch()
