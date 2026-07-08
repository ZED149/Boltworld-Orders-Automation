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
    
    # messge for the failed invoices and slips
    def build_failure_email(self, user_name: str, failed_invoices: list, failed_slips: list) -> str:
        """
        Builds an enterprise-style HTML email summarizing failed invoice/packing slip downloads.
        """

        def stat_card(label: str, count: int) -> str:
            color = "#c8322a" if count else "#1a8a4a"
            return f"""
            <td width="50%" style="padding:16px; background-color:#fafafb; border:1px solid #eef0f3; border-radius:10px;">
                <p style="margin:0 0 4px 0; font-size:12px; color:#9295a0;">{label}</p>
                <p style="margin:0; font-size:24px; font-weight:600; color:{color};">{count}</p>
            </td>
            """

        def order_rows(items: list) -> str:
            if not items:
                return """
                <tr>
                    <td style="padding:12px 16px; font-size:14px; color:#33353d;">None</td>
                    <td align="right" style="padding:12px 16px;">
                        <span style="font-size:12px; font-weight:600; color:#1a8a4a; background-color:#e9f7ee; padding:3px 10px; border-radius:20px;">Success</span>
                    </td>
                </tr>
                """
            rows = ""
            for i, item in enumerate(items):
                border = "" if i == len(items) - 1 else "border-bottom:1px solid #f2f3f5;"
                rows += f"""
                <tr>
                    <td style="padding:12px 16px; font-size:14px; color:#33353d; {border}">Order #{item}</td>
                    <td align="right" style="padding:12px 16px; {border}">
                        <span style="font-size:12px; font-weight:600; color:#c8322a; background-color:#fdeceb; padding:3px 10px; border-radius:20px;">Failed</span>
                    </td>
                </tr>
                """
            return rows

        invoices_html = order_rows(failed_invoices)
        slips_html = order_rows(failed_slips)

        html = f"""
        <html>
        <body style="margin:0; padding:0; background-color:#f3f4f6; font-family:-apple-system, Segoe UI, Roboto, Arial, sans-serif;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6; padding:32px 0;">
                <tr>
                    <td align="center">
                        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
                            style="background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">

                            <!-- Brand bar -->
                            <tr>
                                <td style="padding:32px 40px 24px 40px; border-bottom:1px solid #eef0f3;">
                                    <table role="presentation" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="width:28px; height:28px; border-radius:6px; background-color:#1a1a2e; text-align:center; vertical-align:middle;">
                                                <span style="color:#ffffff; font-size:13px; font-weight:600;">Z</span>
                                            </td>
                                            <td style="padding-left:10px;">
                                                <span style="font-size:14px; font-weight:600; color:#1a1a2e; letter-spacing:0.3px;">ZED Order Automation</span>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- Header + stat cards -->
                            <tr>
                                <td style="padding:32px 40px 8px 40px;">
                                    <p style="margin:0 0 4px 0; font-size:13px; color:#9295a0; text-transform:uppercase; letter-spacing:0.6px;">Order processing report</p>
                                    <h1 style="margin:0 0 20px 0; font-size:22px; font-weight:600; color:#1a1a2e;">Hi {user_name}, here's today's run</h1>
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            {stat_card("Failed invoices", len(failed_invoices))}
                                            <td width="12"></td>
                                            {stat_card("Failed packing slips", len(failed_slips))}
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- Invoices -->
                            <tr>
                                <td style="padding:24px 40px 0 40px;">
                                    <p style="margin:0 0 10px 0; font-size:13px; font-weight:600; color:#1a1a2e; text-transform:uppercase; letter-spacing:0.4px;">Invoices</p>
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eef0f3; border-radius:10px;">
                                        {invoices_html}
                                    </table>
                                </td>
                            </tr>

                            <!-- Packing slips -->
                            <tr>
                                <td style="padding:20px 40px 8px 40px;">
                                    <p style="margin:0 0 10px 0; font-size:13px; font-weight:600; color:#1a1a2e; text-transform:uppercase; letter-spacing:0.4px;">Packing slips</p>
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eef0f3; border-radius:10px;">
                                        {slips_html}
                                    </table>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="padding:20px 40px 32px 40px; border-top:1px solid #eef0f3;">
                                    <p style="margin:0; font-size:12px; color:#b0b2ba;">This is an automated message from ZED Order Automation. No action needed unless failures persist.</p>
                                </td>
                            </tr>

                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html