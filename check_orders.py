from time import sleep
import os
import json
import socket
import glob
import subprocess
import requests
from datetime import datetime
from report_generator import generate_failed_report, generate_success_report
from dotenv import load_dotenv

import sys
if getattr(sys, 'frozen', False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(_base_dir, '.env')
load_dotenv(dotenv_path=env_path)

# loading important global variables
PROD_EXCEL_FILE = os.getenv("PROD_EXCEL_FILE")
LOGGER_NAME = os.getenv("LOGGER_NAME")
LOGGER_DIR = os.getenv("LOGGER_DIR")
EMAIL_NAMES_LIST = json.loads(os.environ["EMAIL_NAMES_LIST"])
EMAIL_RECIPIENTS_LIST = json.loads(os.environ["EMAIL_RECIPIENTS_LIST"])
EMAILS_DATA = zip(EMAIL_NAMES_LIST, EMAIL_RECIPIENTS_LIST)

# ── Config — update these before running ──────────────────────────────────
WP_URL          = os.getenv("WP_URL")
CONSUMER_KEY    = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")

PRINTER_CONFIG_PATH = os.path.join(_base_dir, 'printer_config.json')

SUMATRA_PATHS = [
    r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
    r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe"),
    os.path.join(_base_dir, "SumatraPDF.exe"),
]


class CheckOrders:

    # ──────────────────────────────────────────────────────────────────────
    # Internet
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def check_internet(retries=3, timeout=5):
        for attempt in range(1, retries + 1):
            try:
                socket.setdefaulttimeout(timeout)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('8.8.8.8', 53))
                sock.close()
                return True
            except OSError:
                print(f"  Connection attempt {attempt}/{retries} failed, retrying...")
                sleep(2)
        return False

    # ──────────────────────────────────────────────────────────────────────
    # WooCommerce API
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def api_get(endpoint, params=None):
        r = requests.get(
            f'{WP_URL}/wp-json/wc/v3/{endpoint}',
            auth=(CONSUMER_KEY, CONSUMER_SECRET),
            params=params or {},
            timeout=15,
        )
        r.raise_for_status()
        return r

    @staticmethod
    def api_post(endpoint, data):
        """POST request to WooCommerce REST API."""
        r = requests.post(
            f'{WP_URL}/wp-json/wc/v3/{endpoint}',
            auth=(CONSUMER_KEY, CONSUMER_SECRET),
            json=data,
            timeout=15,
        )
        r.raise_for_status()
        return r

    @staticmethod
    def add_printed_note(order_id):
        """Add @ PRINTED note to an order via API."""
        try:
            CheckOrders.api_post(
                f'orders/{order_id}/notes',
                {
                    'note':          '@ PRINTED',
                    'customer_note': False,
                }
            )
            return True
        except Exception as e:
            print(f"    ✗ Could not add note to {order_id}: {e}")
            return False

    @staticmethod
    def has_printed_note(order_id):
        try:
            r     = CheckOrders.api_get(f'orders/{order_id}/notes')
            notes = r.json()
            return any('PRINTED' in n.get('note', '').upper() for n in notes)
        except Exception as e:
            print(f"    ✗ Could not fetch notes for {order_id}: {e}")
            return False

    @staticmethod
    def get_order_number(order):
        """
        Return the display order number matching what shows in WP admin.
        Uses the 'number' field — not 'id' (which is the post ID).
        """
        number = order.get('number', '')
        if number:
            return f"#{number}"
        for meta in order.get('meta_data', []):
            if meta.get('key') == '_order_number':
                return f"#{meta['value']}"
        return f"#{order['id']}"

    @staticmethod
    def fetch_unprinted_processing_orders(max_pages=3):
        """
        Fetch processing orders from the first max_pages pages.
        Skips orders that already have @ PRINTED in their notes.
        """
        orders_to_print = []
        counter         = 0

        print(f"Fetching processing orders via API (first {max_pages} pages)...\n")

        for page in range(1, max_pages + 1):
            print(f"  Page {page}/{max_pages}...")

            r = CheckOrders.api_get('orders', params={
                'status':   'processing',
                'per_page': 100,
                'page':     page,
                'orderby':  'date',
                'order':    'desc',
            })

            total_pages = int(r.headers.get('X-WP-TotalPages', 1))
            batch       = r.json()

            if not batch:
                break

            for order in batch:
                order_id     = order['id']
                order_number = CheckOrders.get_order_number(order)

                if CheckOrders.has_printed_note(order_id):
                    continue

                counter += 1
                orders_to_print.append({
                    'order_number': order_number,
                    'post_id':      str(order_id),
                })
                print(f"  [{counter}] {order_number}  (post-{order_id})")

            if page >= total_pages:
                break

        print(f"\n  ── Total new orders found: {counter} ──")
        return orders_to_print

    # ──────────────────────────────────────────────────────────────────────
    # Sumatra PDF
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def find_sumatra():
        for path in SUMATRA_PATHS:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def print_pdf_with_sumatra(sumatra_path, pdf_path, printer_name,
                               orientation='portrait'):
        cmd = [
            sumatra_path,
            '-print-to', printer_name,
            '-print-settings', orientation,
            '-silent',
            pdf_path,
        ]
        try:
            result = subprocess.run(cmd, timeout=30)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"    ✗ Print timed out: {os.path.basename(pdf_path)}")
            return False
        except Exception as e:
            print(f"    ✗ Print error: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────
    # Network printer helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def is_unc(path):
        r"""Returns True if path is a UNC path like \\server\printer."""
        return path.startswith('\\\\')

    @staticmethod
    def get_display_name(unc_or_name):
        r"""\\192.168.1.103\printer -> printer. Plain name passes through."""
        if CheckOrders.is_unc(unc_or_name):
            return unc_or_name.rstrip('\\').split('\\')[-1]
        return unc_or_name

    @staticmethod
    def map_network_printer(unc_path):
        try:
            import win32print
            win32print.AddPrinterConnection(unc_path)
            print(f"  ✓ Mapped: {unc_path}")
            return True
        except Exception as e:
            print(f"  ✗ Could not map {unc_path}: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────
    # Printer config
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def load_printer_config():
        if os.path.exists(PRINTER_CONFIG_PATH):
            with open(PRINTER_CONFIG_PATH, 'r') as f:
                return json.load(f)
        return None

    @staticmethod
    def save_printer_config(invoice_printer, slip_printer):
        config = {
            'invoice_printer': invoice_printer,
            'slip_printer':    slip_printer,
        }
        with open(PRINTER_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"  Config saved → {PRINTER_CONFIG_PATH}")

    # ──────────────────────────────────────────────────────────────────────
    # Printer selection
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_available_printers():
        import win32print
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return [p[2] for p in printers]

    @staticmethod
    def prompt_printer_selection(printers, doc_type):
        print(f"\n  Available printers for {doc_type}:")
        print(f"  {'─' * 50}")
        for i, name in enumerate(printers, 1):
            print(f"  [{i}] {name}")
        print(f"  {'─' * 50}")
        print(f"  [0] Enter a network printer manually (UNC path)")
        print(f"  {'─' * 50}")

        while True:
            try:
                choice = input(
                    f"  Select printer for {doc_type} (0-{len(printers)}): "
                ).strip()
                idx = int(choice)

                if idx == 0:
                    print()
                    print("  Enter the UNC path of the network printer.")
                    print(r"  Example: \\192.168.1.103\smallslipsprinter")
                    print()
                    unc = input("  UNC path: ").strip()
                    if not unc.startswith('\\\\'):
                        print(r"  Invalid — must start with \\ e.g. \\192.168.1.103\printername")
                        continue
                    print(f"  ✓ Selected: {unc}")
                    return unc

                idx -= 1
                if 0 <= idx < len(printers):
                    print(f"  ✓ Selected: {printers[idx]}")
                    return printers[idx]

                print(f"  Please enter a number between 0 and {len(printers)}")

            except ValueError:
                print("  Invalid input — please enter a number")

    @staticmethod
    def resolve_printers():
        import win32print

        config = CheckOrders.load_printer_config()

        if config:
            inv_stored  = config.get('invoice_printer', '')
            slip_stored = config.get('slip_printer', '')

            if CheckOrders.is_unc(inv_stored):
                print(f"  Mapping invoice printer...")
                CheckOrders.map_network_printer(inv_stored)
            if CheckOrders.is_unc(slip_stored):
                print(f"  Mapping packing slip printer...")
                CheckOrders.map_network_printer(slip_stored)

            printers     = CheckOrders.get_available_printers()
            inv_display  = CheckOrders.get_display_name(inv_stored)
            slip_display = CheckOrders.get_display_name(slip_stored)

            if inv_display in printers and slip_display in printers:
                print(f"  Using saved printers:")
                print(f"    Invoices      → {inv_display}")
                print(f"    Packing Slips → {slip_display}")
                return inv_display, slip_display

            print("  Saved printer(s) not reachable — please re-select.\n")

        printers = CheckOrders.get_available_printers()

        print(f"\n{'=' * 55}")
        print("  PRINTER SETUP  (saved for future runs)")
        print(f"{'=' * 55}")

        invoice_raw = CheckOrders.prompt_printer_selection(printers, 'PDF Invoices')
        slip_raw    = CheckOrders.prompt_printer_selection(printers, 'Packing Slips')

        if CheckOrders.is_unc(invoice_raw):
            CheckOrders.map_network_printer(invoice_raw)
        if CheckOrders.is_unc(slip_raw):
            CheckOrders.map_network_printer(slip_raw)

        CheckOrders.save_printer_config(invoice_raw, slip_raw)

        inv_display  = CheckOrders.get_display_name(invoice_raw)
        slip_display = CheckOrders.get_display_name(slip_raw)

        print(f"\n  Invoices      → {inv_display}")
        print(f"  Packing Slips → {slip_display}")
        print(f"{'─' * 55}")

        return inv_display, slip_display

    # ──────────────────────────────────────────────────────────────────────
    # Print PDFs
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def print_downloaded_orders(success_orders, invoice_dir, slip_dir,
                                invoice_printer, slip_printer):

        sumatra = CheckOrders.find_sumatra()

        if not sumatra:
            print(f"\n{'=' * 55}")
            print("  SUMATRA PDF NOT FOUND — cannot print")
            print(f"{'─' * 55}")
            print("  Download from:")
            print("  https://www.sumatrapdfreader.org/download-free-pdf-viewer")
            print("  OR place SumatraPDF.exe in the same folder as this script.")
            print(f"{'=' * 55}")
            return

        print(f"\n{'=' * 55}")
        print("  PRINTING")
        print(f"{'─' * 55}")
        print(f"  Invoices      → {invoice_printer}")
        print(f"  Packing Slips → {slip_printer}")
        print(f"{'=' * 55}\n")

        printed = []
        failed  = []

        for order in success_orders:
            order_number = order['order_number'].replace('#', '')
            print(f"  Order {order['order_number']}...")

            invoices = glob.glob(
                os.path.join(invoice_dir, f"{order_number}__Invoice*.pdf")
            )
            slips = glob.glob(
                os.path.join(slip_dir, f"{order_number}__PackingSlip*.pdf")
            )

            if invoices:
                print(f"    Sending invoice → {invoice_printer}...")
                ok = CheckOrders.print_pdf_with_sumatra(
                    sumatra, invoices[0], invoice_printer,
                    orientation='portrait',
                )
                if ok:
                    print(f"    Invoice      ✓")
                    printed.append(f"{order['order_number']} — Invoice")
                else:
                    print(f"    Invoice      ✗")
                    failed.append(f"{order['order_number']} — Invoice")
            else:
                print(f"    Invoice      ✗  File not found")
                failed.append(f"{order['order_number']} — Invoice: file not found")

            sleep(3)

            if slips:
                print(f"    Sending packing slip → {slip_printer}...")
                ok = CheckOrders.print_pdf_with_sumatra(
                    sumatra, slips[0], slip_printer,
                    orientation='landscape',
                )
                if ok:
                    print(f"    Packing slip ✓")
                    printed.append(f"{order['order_number']} — Packing Slip")
                else:
                    print(f"    Packing slip ✗")
                    failed.append(f"{order['order_number']} — Packing Slip")
            else:
                print(f"    Packing slip ✗  File not found")
                failed.append(f"{order['order_number']} — Packing Slip: file not found")

            sleep(2)

        print(f"\n{'─' * 55}")
        print(f"  Printed : {len(printed)}")
        for p in printed:
            print(f"    ✓ {p}")
        if failed:
            print(f"\n  Failed  : {len(failed)}")
            for f in failed:
                print(f"    ✗ {f}")
        print(f"{'=' * 55}")

    # ──────────────────────────────────────────────────────────────────────
    # Merge invoices
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def merge_invoices(success_orders, invoice_dir, merged_dir):
        from pypdf import PdfWriter, PdfReader

        os.makedirs(merged_dir, exist_ok=True)

        invoice_paths = []
        for order in success_orders:
            order_number = order['order_number'].replace('#', '')
            matches = glob.glob(
                os.path.join(invoice_dir, f"{order_number}__Invoice*.pdf")
            )
            if matches:
                invoice_paths.append(matches[0])

        if not invoice_paths:
            print("  No invoices to merge.")
            return None

        writer   = PdfWriter()
        included = []

        for path in invoice_paths:
            try:
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
                included.append(os.path.basename(path))
            except Exception as e:
                print(f"  ✗ Could not add {os.path.basename(path)}: {e}")

        if not included:
            print("  No invoices could be merged.")
            return None

        merged_name = "Invoices_Merged.pdf"
        merged_path = os.path.join(merged_dir, merged_name)

        with open(merged_path, 'wb') as f:
            writer.write(f)

        print(f"  Merged {len(included)} invoice(s) → {merged_path}")
        return merged_path

    # ──────────────────────────────────────────────────────────────────────
    # Main entry
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def check_new_orders():

        # 0. Internet check
        print("Checking internet connection...")
        if not CheckOrders.check_internet():
            print("\n  ✗ No internet connection detected.")
            print("  Please check your network and try again.")
            return None
        print("  ✓ Connected!\n")

        # 1. Fetch unprinted processing orders via API
        try:
            orders_to_print = CheckOrders.fetch_unprinted_processing_orders()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("\n  ✗ API authentication failed.")
                print("  Please check CONSUMER_KEY and CONSUMER_SECRET in this file.")
            else:
                print(f"\n  ✗ API error: {e}")
            return None
        except Exception as e:
            print(f"\n  ✗ Failed to fetch orders: {e}")
            return None

        if not orders_to_print:
            print("\n  No unprinted processing orders found.")
            return []

        # 2. Download PDFs and process
        CheckOrders.process_orders(orders_to_print)

        return orders_to_print

    # ──────────────────────────────────────────────────────────────────────
    # Download PDFs via Selenium + report + print + merge
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def extract_access_key(url):
        """
        Extract _wpnonce from a PDF URL like:
        admin-ajax.php?action=generate_wpo_wcpdf&document_type=invoice
                       &bulk&_wpnonce=239862e3fc&order_ids=257889
        Returns the nonce string or None.
        """
        import urllib.parse as _up
        params = _up.parse_qs(_up.urlparse(url).query)
        return params.get('_wpnonce', [None])[0]

    @staticmethod
    def build_pdf_url(post_id, doc_type, wpnonce):
        """
        Build a direct PDF download URL matching the exact pattern:
        admin-ajax.php?action=generate_wpo_wcpdf&document_type=invoice
                       &bulk&_wpnonce=239862e3fc&order_ids=257889
        """
        return (
            f'{WP_URL}/wp-admin/admin-ajax.php'
            f'?action=generate_wpo_wcpdf'
            f'&document_type={doc_type}'
            f'&bulk'
            f'&_wpnonce={wpnonce}'
            f'&order_ids={post_id}'
        )
    
    @staticmethod
    def build_download_pdf_url(post_id, doc_type):
        """
        Build a direct PDF download URL matching the exact pattern:
        https://www.boltworld.co.uk/wp-json/wc/v3/orders/<post_id>/documents?
        type=<doc_type>&generate=True


        Args:
            post_id (_type_): Wo Commerce internally stored post_id for that order
            doc_type (_type_): document type to download e.g., invoice, packing-slip etc

        Returns:
            _type_: URL to make GET request on.
        """
        return (
            "https://www.boltworld.co.uk/wp-json/wc/v3/orders/"
            f"{post_id}/documents?"
            f"type={doc_type}"
            "&generate=True"
        )

    @staticmethod
    def http_download(url, filepath):
        """Download a PDF directly via HTTP. No session needed — key authenticates."""
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and b'%PDF' in r.content[:10]:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                return True
            print(f"    ✗ HTTP {r.status_code}")
        except Exception as e:
            print(f"    ✗ Request error: {e}")
        return False
    
    @staticmethod
    def http_download_pdf_url(url, filepath):
        """
        Download a PDF directly via HTTP. Session is required with authentication and params.

        Args:
            url (_type_): URL to make request on
            filepath (_type_): path to save the pdf

        Returns:
            _type_: True if invoice was downloaded and saved successfully.
        """
        try:
            response = requests.get(url, timeout=20,
                                    params={},
                                    auth=(CONSUMER_KEY, CONSUMER_SECRET))
            if response.status_code == 200:
                # saving the file to specified path
                with open(filepath, 'wb') as file:
                    file.write(response.content)
                return True
            print(f"    ✗ HTTP {response.status_code}")
        except Exception as e:
            print(f"    ✗ Request error: {e}")
        return False

    @staticmethod
    def process_orders(orders_to_print):

        # ── Per-run folder — one timestamped folder per iteration ─────────
        base_dir    = _base_dir
        run_stamp   = datetime.now().strftime('%Y-%m-%d__%I-%M-%S-%p')
        run_dir     = os.path.join(base_dir, 'order_downloads', run_stamp)

        invoice_dir = os.path.join(run_dir, 'invoices')
        slip_dir    = os.path.join(run_dir, 'packing_slips')
        reports_dir = os.path.join(run_dir, 'reports')
        merged_dir  = os.path.join(run_dir, 'merged')

        os.makedirs(invoice_dir, exist_ok=True)
        os.makedirs(slip_dir,    exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(merged_dir,  exist_ok=True)

        print(f"Run folder    → {run_dir}")
        print(f"Invoices      → {invoice_dir}")
        print(f"Packing slips → {slip_dir}\n")

        failed_orders  = []
        success_orders = []
        # Resolve printers once
        print("Resolving printers...")
        invoice_printer, slip_printer = CheckOrders.resolve_printers()
        print()

        # ── Download loop ─────────────────────────────────────────────────
        # we can build the orders invoice and payment-slip using the woo commeerce rest api
        for order in orders_to_print:
            post_id = order['post_id']
            order_numner = order['order_number'].replace("#", '')
            invoice_filename = f'{order_numner}__Invoice.pdf'
            slip_filename = f'{order_numner}__PackingSlip.pdf'
            invoice_path = os.path.join(invoice_dir, invoice_filename)
            slip_path = os.path.join(slip_dir, slip_filename)

            print(f"\n── Order {order['order_number']} (post-{post_id}) ──")

            # ── Invoice ───────────────────────────────────────────────────
            invoice_ok = False

            url = CheckOrders.build_download_pdf_url(post_id, 'invoice')
            invoice_ok = CheckOrders.http_download_pdf_url(url, invoice_path)
            print(f"  Invoice      {'✓ (HTTP)' if invoice_ok else '✗ HTTP failed'}")

            # this check is for, in case if an invoice fails to download, then no need to download its packing slip
            # just move onto the next ordeer and keep record of the order which invoice failed to download
            if not invoice_ok:
                failed_orders.append({
                    'order_number': order['order_number'],
                    'post_id':      post_id,
                    'reason':       'Invoice download failed — packing slip skipped',
                })
                continue


            # ── Packing slip ──────────────────────────────────────────────
            slip_ok = False

            url = CheckOrders.build_download_pdf_url(post_id, 'packing-slip')
            slip_ok = CheckOrders.http_download_pdf_url(url, slip_path)
            print(f"  Packing slip {'✓ (HTTP)' if slip_ok else '✗ HTTP failed'}")

            # this check, in case, if the invoice was downloaded successfully but,
            # its packing-slip failed to downloade, then we need to remove the corresponsing invoice from the system
            if not slip_ok:
                if os.path.exists(invoice_path):
                    os.remove(invoice_path)
                    print(f"  Removed invoice (incomplete pair): {invoice_filename}")
                failed_orders.append({
                    'order_number': order['order_number'],
                    'post_id':      post_id,
                    'reason':       'Packing slip failed — invoice removed',
                })
                continue

            success_orders.append(order['order_number'])
            sleep(0.2)

        # ── Reports ───────────────────────────────────────────────────────

        print(f"\n{'=' * 55}")
        print(f"  Downloaded : {len(success_orders)} orders")
        print(f"  Failed     : {len(failed_orders)} orders")

        success_with_ids = [
            o for o in orders_to_print
            if o['order_number'] in success_orders
        ]


        # ── Mark successful orders as @ PRINTED via API ──────────────────
        if success_with_ids:
            print("\nMarking orders as @ PRINTED...")
            for o in success_with_ids:
                ok = CheckOrders.add_printed_note(o['post_id'])
                print(f"  {'✓' if ok else '✗'} {o['order_number']}")

        print("\nGenerating reports...")
        generate_failed_report(failed_orders,     reports_dir)
        generate_success_report(success_with_ids, reports_dir)
        print(f"  Reports saved → {reports_dir}")
        print(f"{'=' * 55}")

        # ── Email For Failed Orders to Admin ─────────────────────────────────────────────────────────
        # before sending an email, we need to generate a message for the email
        # NOTE! Only send the email if there are failed orders to be notified of
        if failed_orders:    
            from html_formatter import HtmlFormatter
            formatter = HtmlFormatter()

            from mail_handler import MailHandling
            mail_object = MailHandling()
            for name, email in EMAILS_DATA:
                message = formatter.format(data=failed_orders, user_name=name)
                mail_object.send_email(message=message,
                                    receiver_email=email,
                                    sender_email='no-reply@zed149.com',
                                    sender_password='NFAKisAlive@123',
                                    email_subject='Development',
                                    sender_name="ZED Managment Systems")

        # ── Print ─────────────────────────────────────────────────────────

        if success_with_ids and invoice_printer and slip_printer:
            CheckOrders.print_downloaded_orders(
                success_with_ids, invoice_dir, slip_dir,
                invoice_printer, slip_printer,
            )

        # ── Merge invoices ────────────────────────────────────────────────
        merged_pdf_path = ''
        if success_with_ids:
            print(f"\n{'=' * 55}")
            print("  MERGING INVOICES")
            print(f"{'─' * 55}")
            merged_pdf_path = CheckOrders.merge_invoices(success_with_ids, invoice_dir, merged_dir)
            print(f"{'=' * 55}")

        if success_with_ids:
            # ── Processing PDF's from ZED PDF Automation System ────────────────────────────────────────────────
            from excel_handler import ExcelHandler
            from pdf_handler import PDFHandler
            from logs import Logging

            logger = Logging(logger_name=LOGGER_NAME, logger_directory=LOGGER_DIR)
            logger.verbose = False

            excel_handler = ExcelHandler(logger=logger, filename=PROD_EXCEL_FILE)
            pdf_handler = PDFHandler(filename=merged_pdf_path)
            pdf_handler.open()
            order_details = pdf_handler.fetch_order_details(o_type="web")
            wb = excel_handler.open_file(headers=["ORDER_DETAILS", "DATE", "TIME", "USER"], create_file=False)
            excel_handler.write(wb.active, data=order_details, duplication_list=[])
            code = excel_handler.save(wb)


if __name__ == '__main__':
    CheckOrders.check_new_orders()