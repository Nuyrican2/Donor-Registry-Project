"""Dev entry point: python run.py

Prints the address to use on this PC and the one to type on a phone that is
on the same Wi-Fi network.
"""
import socket

from app import create_app

app = create_app()


def lan_ip():
    """This PC's address on the local network (what a phone must type)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no traffic sent; just picks the interface
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


if __name__ == "__main__":
    ip = lan_ip()
    print()
    print("  On this PC:              http://localhost:5000")
    if ip:
        print(f"  On your phone (same Wi-Fi): http://{ip}:5000")
    print()
    app.run(debug=True, host="0.0.0.0")
