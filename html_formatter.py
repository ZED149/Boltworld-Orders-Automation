from message_formatter import MessageFormatter
import unicodedata
from os import getenv
from dotenv import load_dotenv

# loading enviornmental variables into our scope
load_dotenv(dotenv_path=".env")
site_url = getenv("WEBSITE_URI")

# HTML Formatter
class HtmlFormatter(MessageFormatter):
    """Creates a html representation of a message

    Args:
        MessageFormatter (_type_): Abstract class for the formatting
    """

    # format
    def format(self, data: any, user_name: str):
        """Creates an html represntation of the message from the data

        Args:
            data (any): message that contain data
        """
        rows = ""

        for order in data:
            rows += f"""
            <tr>
                <td style="padding:12px; border-bottom:1px solid #eeeeee;">{order.get('order_number', '—')}</td>
                <td style="padding:12px; border-bottom:1px solid #eeeeee;">{order.get('customer_name', '—')}</td>
                <td style="padding:12px; border-bottom:1px solid #eeeeee;">{order.get('date', '—')}</td>
                <td style="padding:12px; border-bottom:1px solid #eeeeee;">£{order.get('price', '0.00')}</td>
            </tr>
            """

        if not data:
            rows = """
            <tr>
                <td colspan="4" style="padding:20px; text-align:center; color:#888888;">
                    No failed orders 🎉
                </td>
            </tr>
            """

        message = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, sans-serif;">

            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f4f4; padding:20px 0;">
                <tr>
                    <td align="center">

                        <!-- Main Container -->
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff; border-radius:8px; overflow:hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="padding:24px; font-size:20px; font-weight:bold; color:#222222;">
                                    Failed Orders
                                </td>
                            </tr>

                            <!-- Greeting -->
                            <tr>
                                <td style="padding:0 24px 16px 24px; font-size:14px; color:#555555;">
                                    Hello {user_name},<br><br>
                                    Here’s a summary of unsuccessful transactions.
                                </td>
                            </tr>

                            <!-- Table -->
                            <tr>
                                <td style="padding:0 24px 24px 24px;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
                                        
                                        <!-- Head -->
                                        <tr style="background-color:#f0f0f0;">
                                            <th align="left" style="padding:12px; font-size:12px; color:#666666;">Order</th>
                                            <th align="left" style="padding:12px; font-size:12px; color:#666666;">Customer</th>
                                            <th align="left" style="padding:12px; font-size:12px; color:#666666;">Date</th>
                                            <th align="left" style="padding:12px; font-size:12px; color:#666666;">Amount</th>
                                        </tr>

                                        {rows}

                                    </table>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="padding:16px 24px; font-size:12px; color:#999999; text-align:right;">
                                    Generated automatically • {site_url}
                                </td>
                            </tr>

                        </table>

                    </td>
                </tr>
            </table>

        </body>
        </html>
        """

        return message