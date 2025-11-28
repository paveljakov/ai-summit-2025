"""QR code generation tools for terminal display."""

import io

import qrcode


def generate_qr_code(data: str, border: int = 1) -> str:
    """Generate a QR code as Unicode text for terminal display.

    Uses the qrcode library's built-in print_ascii method which renders
    using half-block Unicode characters for optimal terminal display.

    Args:
        data: The data to encode in the QR code (URL, text, etc.)
        border: Border size around the QR code (default: 1)

    Returns:
        String with QR code rendered using Unicode block characters
    """
    qr = qrcode.QRCode(
        version=None,  # Auto-determine size
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=border,
    )

    qr.add_data(data)
    qr.make(fit=True)

    # Use built-in print_ascii with StringIO to capture output
    output = io.StringIO()
    qr.print_ascii(out=output)
    output.seek(0)

    return output.read().rstrip()


def format_qr_result(qr_text: str, data: str) -> str:
    """Format QR code result with metadata.

    Args:
        qr_text: The rendered QR code text
        data: The original data encoded

    Returns:
        Formatted string with QR code and info
    """
    display_data = data if len(data) <= 60 else data[:57] + "..."
    return f"QR Code for: {display_data}\n\n{qr_text}"
