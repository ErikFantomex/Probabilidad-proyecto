"""Download the pinned research data and verify its SHA-256 digest."""
import hashlib
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/nlbair/ufc-data/a9c6543/data/ufc_all_fights_wide.csv"
SHA256 = "d63add2ae5c5bafafab56c5cddde9620ec7501cca48ca912d35565f73e31dd61"
DESTINATION = Path(__file__).resolve().parent / "data/raw/ufc_all_fights_wide.csv"


def main():
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists() and hashlib.sha256(DESTINATION.read_bytes()).hexdigest() == SHA256:
        print(f"Datos verificados: {DESTINATION}")
        return
    temporary = DESTINATION.with_suffix(".download")
    urllib.request.urlretrieve(URL, temporary)
    actual = hashlib.sha256(temporary.read_bytes()).hexdigest()
    if actual != SHA256:
        temporary.unlink()
        raise ValueError(f"SHA-256 inesperado: {actual}")
    temporary.replace(DESTINATION)
    print(f"Datos descargados y verificados: {DESTINATION}")


if __name__ == "__main__":
    main()
