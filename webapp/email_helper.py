"""Resend email integration."""
import os
import base64
import resend

CONTACT_EMAIL = "contact@tracksoftsolutions.com"
SUPPORT_LINE = (
    "For queries reply to this email or write to "
    f"{CONTACT_EMAIL}"
)


def _init():
    key = os.environ.get("RESEND_KEY", "")
    if not key:
        raise RuntimeError("RESEND_KEY is not set in environment.")
    resend.api_key = key


def send_otp(to_email: str, otp: str):
    _init()
    resend.Emails.send({
        "from": os.environ.get("RESEND_FROM", f"noreply@tracksoftsolutions.com"),
        "to": [to_email],
        "subject": "Your Tracksoft Lead Processor OTP",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto">
          <img src="https://leads.tracksoftsolutions.com/static/tracksoft-logo.png"
               alt="Tracksoft" style="width:80px;margin-bottom:16px">
          <h2 style="color:#1a5fa8">Verify your identity</h2>
          <p>Use this OTP to receive your processed lead file:</p>
          <div style="font-size:36px;font-weight:bold;letter-spacing:8px;
                      color:#1a5fa8;padding:16px 0">{otp}</div>
          <p style="color:#888;font-size:13px">
            This OTP expires in 10 minutes. Do not share it.<br>{SUPPORT_LINE}
          </p>
        </div>
        """
    })


def send_result(to_email: str, file_name: str, file_bytes: bytes):
    _init()
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    resend.Emails.send({
        "from": os.environ.get("RESEND_FROM", f"noreply@tracksoftsolutions.com"),
                "to": [to_email],
                "cc": [CONTACT_EMAIL],
        "subject": "Your Tracksoft Lead file is ready",
                "html": f"""
                <div style="font-family:Arial,sans-serif;max-width:680px;margin:auto;line-height:1.55;color:#1b1b1b">
          <img src="https://leads.tracksoftsolutions.com/static/tracksoft-logo.png"
               alt="Tracksoft" style="width:80px;margin-bottom:16px">
          <h2 style="color:#1a5fa8">Your file is ready!</h2>
                    <p>Thank you for using the Tracksoft Lead Processor utility. Your processed file is attached here:
                    <strong>{file_name}</strong>.</p>

                    <p>
                        <strong>Tracksoft Solutions Pvt. Ltd.</strong> is an EdTech company focused on innovative,
                        cutting-edge solutions for everyday challenges in the education domain. We build intuitive
                        software that makes life easier for education providers and seekers.
                    </p>

                    <p>
                        Our team follows agile product development (including Agile and Kanban) to deliver value quickly,
                        gather customer feedback, and improve products iteratively at lower cost.
                        Our products include <strong>Enrol-Me</strong> and <strong>Track-Me</strong>, with strong expertise
                        across web and mobile platforms.
                    </p>

                    <p>
                        We also offer:
                        high-quality software development,
                        process consulting,
                        staff training and upskilling,
                        and staff augmentation.
                    </p>

                    <p style="background:#eef6ff;border:1px solid #d7e9ff;padding:12px;border-radius:8px">
                        <strong>Try our AI Bot for your website.</strong>
                        Visit <a href="https://tracksoftsolutions.com">tracksoftsolutions.com</a>
                    </p>

                    <p>
                        Explore more:
                        <a href="https://www.tracksoftsolutions.com">www.tracksoftsolutions.com</a>,
                        <a href="https://www.enrol-me.com">www.enrol-me.com</a>,
                        <a href="https://www.findmymoney.in">www.findmymoney.in</a>
                    </p>

                    <p>
                        Google Play Store:
                        <a href="https://play.google.com/store/apps/details?id=com.ionicframework.enroleme838025">
                            Download Enrol-Me
                        </a>
                    </p>

                    <p style="font-size:13px;color:#555">
                        <strong>Tracksoft Solutions Pvt. Ltd.</strong><br>
                        2nd Floor, Priyali Apartment, Sr. No. 84/2, Baner Road, Sakal Nagar, Pune<br>
                        Contact: +91 96041 88726, +91 96041 88725
                    </p>

          <p style="color:#888;font-size:13px">{SUPPORT_LINE}</p>
        </div>
        """,
        "attachments": [{
            "filename": file_name,
            "content": encoded,
        }]
    })
