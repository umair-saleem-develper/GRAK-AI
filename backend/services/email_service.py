import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email: str, otp: str):
    """
    Sends an OTP email using Brevo's REST API.
    """
    brevo_api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")

    if not brevo_api_key or not sender_email:
        logger.warning(f"[DEV FALLBACK] Generated OTP for {email}: {otp}. Brevo is not configured.")
        return True

    html_content = f"""
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #050505; color: #ffffff;">
        <div style="background-color: #050505; width: 100%; padding: 60px 0;">
          <div style="max-width: 500px; margin: 0 auto; background-color: #121214; border: 1px solid rgba(138, 43, 226, 0.2); border-radius: 24px; overflow: hidden; box-shadow: 0 10px 40px rgba(138, 43, 226, 0.1);">
            
            <!-- Header -->
            <div style="padding: 40px 40px 20px; text-align: center;">
              <h1 style="margin: 0; font-size: 32px; font-weight: 800; letter-spacing: -1px; background: linear-gradient(135deg, #ffffff, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Grak AI
              </h1>
            </div>

            <!-- Body -->
            <div style="padding: 20px 40px 40px;">
              <h2 style="margin: 0 0 24px; font-size: 20px; font-weight: 600; color: #ffffff; text-align: center;">
                Hello, welcome to Grak AI!
              </h2>
              
              <p style="margin: 0 0 30px; font-size: 15px; line-height: 1.6; color: #a1a1aa; text-align: center;">
                Please use the verification code below to securely sign in to your account.
              </p>
              
              <!-- Styled Dark-Purple Container Box -->
              <div style="background: linear-gradient(145deg, #1f1033, #2d164d); border: 1px solid rgba(168, 85, 247, 0.4); border-radius: 16px; padding: 32px; text-align: center; margin: 0 0 30px; box-shadow: inset 0 0 20px rgba(168, 85, 247, 0.1);">
                <span style="font-size: 44px; font-weight: 800; letter-spacing: 12px; color: #ffffff; display: inline-block; margin-left: 12px; text-shadow: 0 2px 10px rgba(168, 85, 247, 0.5);">
                  {otp}
                </span>
              </div>

              <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #71717a; text-align: center;">
                This code will expire in <strong>10 minutes</strong>. If you did not request this, please ignore this email.
              </p>
            </div>
            
            <!-- Footer -->
            <div style="padding: 24px 40px; background-color: #0a0a0c; border-top: 1px solid rgba(168, 85, 247, 0.1); text-align: center;">
              <p style="margin: 0; font-size: 13px; font-weight: 500; color: #52525b; letter-spacing: 0.5px;">
                Securely powered by Grak AI
              </p>
            </div>

          </div>
        </div>
      </body>
      </html>
    """

    payload = {
        "sender": {
            "name": "Grak AI",
            "email": sender_email
        },
        "to": [{"email": email}],
        "subject": "Your Grak AI Verification Code",
        "htmlContent": html_content
    }

    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'accept': 'application/json',
                'api-key': brevo_api_key,
                'content-type': 'application/json'
            },
            json=payload,
            timeout=10
        )
        
        if not response.ok:
            logger.error(f"Failed to send email via Brevo. Status: {response.status_code}, Body: {response.text}")
            raise Exception("Failed to send OTP email via Brevo API")
            
        logger.info(f"OTP email successfully sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise e
