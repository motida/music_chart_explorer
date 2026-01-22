import logging
import sys
from artwork_client import get_artwork_url

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def test_artwork():
    print("Testing Artwork Extraction...")

    # Test Case 1: Queen - Bohemian Rhapsody
    artist = "Queen"
    title = "Bohemian Rhapsody"
    print(f"\nSearching for: {artist} - {title}")
    url = get_artwork_url(artist, title)
    print(f"Result URL: {url}")

    # Test Case 2: Michael Jackson - Thriller
    artist = "Michael Jackson"
    title = "Thriller"
    print(f"\nSearching for: {artist} - {title}")
    url = get_artwork_url(artist, title)
    print(f"Result URL: {url}")


if __name__ == "__main__":
    test_artwork()
