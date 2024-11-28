import sys
import os
import json
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QPushButton,
    QWidget,
    QFormLayout,
    QMessageBox,
)
from smtp import SMTPEmailSender, SMTPSecurityMode

# version
script_version = "0.1"

# file path config
config_path = "config.json"
log_path = "log.txt"

# default config, only used if there is no config file presents
smtp_server = "smtp.gmail.com"
smtp_timeout_s = 5
smtp_port_plain = 25
smtp_port_TLS = 587
smtp_port_SSL = 465
smtp_user = "printer@example.com"
smtp_password = "123456"
email_sender = smtp_user
email_recive = smtp_user
email_cc = None
email_bcc = None
email_title = "Test Email Title"
email_body = "Test Email Body"


class LogFormarterQtHelper(logging.Formatter):

    span_black = '<span style="color:#000000;" >'
    span_gray = '<span style="color:#4a4a4a;" >'
    span_yellow = '<span style="color:#d1c217;" >'
    span_red = '<span style="color:#d11717;" >'
    span_blue = '<span style="color:#1d17d1;" >'
    span_green = '<span style="color:#2ad117;" >'
    span_purple = '<span style="color:#d117b8;" >'
    span_end = "</span>"

    format_p1 = "[%(asctime)s]["
    level_text = "%(levelname)s"
    format_p2 = "] %(message)s"

    FORMATS = {
        logging.DEBUG: format_p1 + span_blue + level_text + span_end + format_p2,
        logging.INFO: format_p1 + span_green + level_text + span_end + format_p2,
        logging.WARNING: format_p1 + span_yellow + level_text + span_end + format_p2,
        logging.ERROR: format_p1 + span_red + level_text + span_end + format_p2,
        logging.CRITICAL: format_p1 + span_purple + level_text + span_end + format_p2,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class LogHandlerQtHelper(logging.Handler):
    def __init__(self, ui_obj):
        super().__init__()
        self.setFormatter(LogFormarterQtHelper())
        self.log_area: QTextEdit = ui_obj._get_log_area()

    def emit(self, record):
        msg = self.format(record)
        self.log_area.append(msg)


class SMTPTesterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"SMTP Tester [Ver {script_version}]")
        self.resize(600, 700)

        # Configuration file path
        self.config_path = config_path

        # Configuration data
        self.config_data = {
            "smtp_server": smtp_server,
            "smtp_timeout_s": smtp_timeout_s,
            "smtp_port": smtp_port_plain,
            "smtp_user": smtp_user,
            "smtp_password": smtp_password,
            "security_mode": SMTPSecurityMode.NONE.value,
            "email_sender": email_sender,
            "email_recive": email_recive,
            "email_cc": email_cc,
            "email_bcc": email_bcc,
            "email_title": email_title,
            "email_body": email_body,
        }

        # Setup UI
        self._setup_ui()

        # Setup logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # -- file
        log_handler_file = logging.FileHandler(log_path)
        log_handler_file.setFormatter(
            logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        )
        logger.addHandler(log_handler_file)

        # -- UI
        log_handler_ui = LogHandlerQtHelper(self)
        logger.addHandler(log_handler_ui)

        # Load or create default configuration
        if not self.load_config():
            # load failed, created new
            with open(self.config_path, "w") as f:
                json.dump(self.config_data, f, indent=4)
            # reload
            if not self.load_config():
                QMessageBox.critical(
                    self, "Error", f"Could not create config: {self.config_path}"
                )
                quit()

    def _get_log_area(self):
        return self.log_area

    def _setup_ui(self):
        """Create the main user interface."""
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # SMTP Config
        layout.addWidget(QLabel("SMTP Configs:"))
        layout_smtp = QHBoxLayout()
        layout.addLayout(layout_smtp)

        # -- Server Configuration
        layout_server = QFormLayout()
        layout_smtp.addLayout(layout_server)

        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("SMTP Server (e.g., smtp.gmail.com)")
        layout_server.addRow("Server:", self.server_input)

        self.port_input = QSpinBox()
        self.port_input.setRange(0, 65535)
        layout_server.addRow("Port:", self.port_input)

        self.security_mode = QComboBox()
        self.security_mode.addItems([mode.value for mode in SMTPSecurityMode])
        layout_server.addRow("Encryption:", self.security_mode)

        self.timeout_s_input = QSpinBox()
        self.timeout_s_input.setRange(1, 65535)
        layout_server.addRow("Timeout (ms):", self.timeout_s_input)

        # -- Credential
        layout_credential = QFormLayout()
        layout_smtp.addLayout(layout_credential)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username/Email")
        layout_credential.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        # self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        self.password_input.setPlaceholderText("Password")
        layout_credential.addRow("Password:", self.password_input)

        # Email Details
        layout.addWidget(QLabel("Email Details:"))
        layout_email = QFormLayout()
        layout.addLayout(layout_email)

        self.sender_input = QLineEdit()
        self.sender_input.setPlaceholderText("Sender Email")
        layout_email.addRow("From:", self.sender_input)

        self.receiver_input = QLineEdit()
        self.receiver_input.setPlaceholderText("Receiver Email")
        layout_email.addRow("To:", self.receiver_input)

        # CC and BCC
        self.cc_input = QLineEdit()
        self.cc_input.setPlaceholderText("Comma-separated CC emails")
        layout_email.addRow("CC:", self.cc_input)

        self.bcc_input = QLineEdit()
        self.bcc_input.setPlaceholderText("Comma-separated BCC emails")
        layout_email.addRow("BCC:", self.bcc_input)

        # Email Subject and Body
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Email Subject")
        layout.addWidget(QLabel("Subject:"))
        layout.addWidget(self.subject_input)

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Plain Text Email Body")
        layout.addWidget(QLabel("Body (Plain Text):"))
        layout.addWidget(self.body_input)

        self.html_body_input = QTextEdit()
        self.html_body_input.setPlaceholderText("Optional HTML Email Body")
        layout.addWidget(QLabel("Body (HTML - Optional):"))
        layout.addWidget(self.html_body_input)

        # Action Buttons
        button_layout = QHBoxLayout()

        save_config_button = QPushButton("Save Config")
        save_config_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_config_button)

        load_config_button = QPushButton("Load Config")
        load_config_button.clicked.connect(self.load_config)
        button_layout.addWidget(load_config_button)

        send_button = QPushButton("Send Email")
        send_button.clicked.connect(self._send_email)
        button_layout.addWidget(send_button)

        layout.addLayout(button_layout)

        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.log_area)

    def _send_email(self):
        """Send email and log results."""
        # Prepare arguments
        try:
            cc = (
                [email.strip() for email in self.cc_input.text().split(",")]
                if self.cc_input.text()
                else None
            )
            bcc = (
                [email.strip() for email in self.bcc_input.text().split(",")]
                if self.bcc_input.text()
                else None
            )

            result = SMTPEmailSender.send_email(
                smtp_server=self.server_input.text(),
                smtp_port=self.port_input.value(),
                smtp_timeout_s=self.timeout_s_input.value(),
                smtp_user=self.username_input.text(),
                smtp_password=self.password_input.text(),
                security_mode=SMTPSecurityMode(self.security_mode.currentText()),
                email_sender=self.sender_input.text(),
                email_receive=self.receiver_input.text(),
                email_title=self.subject_input.text(),
                email_body=self.body_input.toPlainText(),
                cc=cc,
                bcc=bcc,
                html_body=self.html_body_input.toPlainText() or None,
            )

            # Log result

            logging.info(
                f"Send Result: {'Success' if result['success'] else 'Failed'}"
            )
            logging.info(f"Result Detail: {result['message']}")
            if result.get("error_details"):
                logging.info(f"Error Detail: {result['error_details']}")
            if result.get("debug_msg"):
                for line in result["debug_msg"]:
                    logging.debug(line)

        except Exception as e:
            logging.error(f"Unexpected Error: {str(e)}")

    def save_config(self) -> bool:
        """Save current configuration to a JSON file."""

        try:
            self.config_data = {
                "smtp_server": self.server_input.text(),
                "smtp_port": self.port_input.value(),
                "smtp_timeout_s": self.timeout_s_input.value(),
                "smtp_user": self.username_input.text(),
                "smtp_password": self.password_input.text(),
                "security_mode": self.security_mode.currentText(),
                "email_sender": self.sender_input.text(),
                "email_recive": self.receiver_input.text(),
                "email_cc": self.cc_input.text(),
                "email_bcc": self.bcc_input.text(),
                "email_title": self.subject_input.text(),
                "email_body": self.body_input.toPlainText(),
            }

            with open(self.config_path, "w") as f:
                json.dump(self.config_data, f, indent=4)

        except Exception as e:
            logging.error(f"Save config failed: {e}")
            return False

        logging.info(f"Save config success")
        return True

    def load_config(self) -> bool:
        """Load configuration from JSON file."""

        if not os.path.exists(self.config_path):
            return False

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)

            # Restore UI values
            self.server_input.setText(config.get("smtp_server", ""))
            self.port_input.setValue(config.get("smtp_port", ""))
            self.timeout_s_input.setValue(config.get("smtp_timeout_s", ""))
            self.username_input.setText(config.get("smtp_user", ""))
            self.password_input.setText(config.get("smtp_password", ""))
            self.security_mode.setCurrentText(config.get("security_mode", ""))

            self.sender_input.setText(config.get("email_sender", ""))
            self.receiver_input.setText(config.get("email_recive", ""))
            self.cc_input.setText(config.get("email_cc", ""))
            self.bcc_input.setText(config.get("email_bcc", ""))
            self.subject_input.setText(config.get("email_title", ""))
            self.body_input.setText(config.get("email_body", ""))

        except Exception as e:
            logging.error(f"Load config failed: {e}")
            return False

        logging.info(f"Load config success")
        return True

    def closeEvent(self, event):
        """Auto-save configuration on exit."""

        self.save_config()
        event.accept()


def main():
    app = QApplication([])
    window = SMTPTesterGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
