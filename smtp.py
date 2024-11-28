import enum
import smtplib
import ssl
import sys
from io import StringIO
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SMTPSecurityMode(enum.Enum):
    """Enumeration for SMTP security modes."""

    NONE = "None/Plain (Common Port 25)"
    SSL = "SSL/TLS (Common Port 465)"
    STARTTLS = "STARTTLS (Common Port 587)"


class SMTPEmailSender:
    """Class responsible for sending emails via SMTP."""

    @staticmethod
    def send_email(
        smtp_server: str,
        smtp_port: int,
        smtp_timeout_s: int,
        smtp_user: str,
        smtp_password: str,
        security_mode: SMTPSecurityMode,
        email_sender: str,
        email_receive: str,
        email_title: str,
        email_body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None,
    ) -> dict:
        """
        Send an email using the specified SMTP configuration.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            smtp_timeout_s: SMTP timeout
            smtp_user: SMTP authentication username
            smtp_password: SMTP authentication password
            security_mode: Security mode for SMTP connection
            email_sender: Sender's email address
            email_receive: Recipient's email address
            email_title: Email subject
            email_body: Plain text email body
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            html_body: Optional HTML body content

        Returns:
        A dictionary with send status and details.
        """
        result = {
            "success": False,
            "message": "",
            "error_details": None,
            "debug_msg": None,
        }

        try:
            # Create message container
            msg = MIMEMultipart()
            msg["From"] = email_sender
            msg["To"] = email_receive
            msg["Subject"] = email_title

            # Add CC recipients if provided
            if cc:
                msg["Cc"] = ", ".join(cc)
                recipients = [email_receive] + cc
            else:
                recipients = [email_receive]

            # Add BCC recipients if provided
            if bcc:
                recipients.extend(bcc)

            # Attach plain text body
            msg.attach(MIMEText(email_body, "plain"))

            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # redirect output begin
            stdout_bak = sys.stdout
            stderr_bak = sys.stderr
            sys.stdout = sys.stderr = stdouterr_temp = StringIO()

            # Establish SMTP connection based on security mode
            try:
                match security_mode:
                    case SMTPSecurityMode.NONE:
                        smtp = smtplib.SMTP(
                            smtp_server, smtp_port, timeout=smtp_timeout_s
                        )
                    case SMTPSecurityMode.SSL:
                        smtp = smtplib.SMTP_SSL(
                            smtp_server, smtp_port, timeout=smtp_timeout_s
                        )
                    case SMTPSecurityMode.STARTTLS:
                        smtp = smtplib.SMTP(
                            smtp_server, smtp_port, timeout=smtp_timeout_s
                        )

                smtp.set_debuglevel(2)

                if security_mode == SMTPSecurityMode.STARTTLS:
                    smtp.starttls()

                # Login to SMTP server
                smtp.login(smtp_user, smtp_password)

                # Send email
                smtp.sendmail(email_sender, recipients, msg.as_string())

                # Close connection
                smtp.quit()

                result["success"] = True
                result["message"] = "Email sent successfully!"

            except smtplib.SMTPAuthenticationError as auth_err:
                result["message"] = "Authentication Failed"
                result["error_details"] = str(auth_err)

            except smtplib.SMTPException as smtp_err:
                result["message"] = "SMTP Error"
                result["error_details"] = str(smtp_err)

            except Exception as e:
                result["message"] = "Unexpected Error"
                result["error_details"] = str(e)

        except Exception as e:
            result["message"] = "Message Preparation Error"
            result["error_details"] = str(e)

        result["debug_msg"] = stdouterr_temp.getvalue().splitlines()

        # redirect output end
        sys.stdout = stdout_bak
        sys.stderr = stderr_bak

        return result
