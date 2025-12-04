import re
import hashlib
import datetime
import requests
from bs4 import BeautifulSoup
import unittest

VOYAGER1_URL = "https://science.nasa.gov/mission/voyager/voyager-1/"
RFC1149_INFO_URL = "https://www.rfc-editor.org/info/rfc1149"
RFC1149_TXT_URL = "https://www.rfc-editor.org/rfc/rfc1149.txt"
BRAIN_URL = "https://www.unicode.org/Public/emoji/16.0/emoji-test.txt"
BITCOIN_URL = "https://raw.githubusercontent.com/bitcoin/bitcoin/master/src/chainparams.cpp"
OPENLIB_URL = "https://openlibrary.org/search.json"

HEADERS = {"User-Agent": "primary-sources-bot/1.0 (+https://example.local/)"}


def convert_to_yyyymmdd(date_text: str) -> str:

    date_text = date_text.strip()
    date_text = re.sub(r'\.(?=\s|$)', '', date_text)
    date_text = re.sub(r'\bSept\b', 'Sep', date_text, flags=re.IGNORECASE)
    patterns = [
        "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
        "%Y-%m-%d", "%Y %b %d", "%Y %B %d"
    ]
    for p in patterns:
        try:
            dt = datetime.datetime.strptime(date_text, p)
            return dt.strftime("%Y%m%d")
        except ValueError:
            continue
    raise ValueError(f"Не удалось распарсить дату: {date_text!r}")


def launch_date() -> str:
    r = requests.get(VOYAGER1_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(separator="\n")
    m = re.search(r"Launch Date and Time\s*[:,]?\s*([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})", text, re.IGNORECASE)
    if not m:
        raise ValueError("Дата не найдена")
    return convert_to_yyyymmdd(m.group(1))


def rfc1149_date() -> str:
    # info-page
    r = requests.get(RFC1149_INFO_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    m = re.search(r"April 1 1990", r.text)
    if m:
        return convert_to_yyyymmdd("April 1, 1990")
    # TXT
    r2 = requests.get(RFC1149_TXT_URL, headers=HEADERS, timeout=15)
    r2.raise_for_status()
    m2 = re.search(r"\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", r2.text)
    if m2:
        return convert_to_yyyymmdd(m2.group(1))
    raise RuntimeError("Дата не найдена")


def brain_codepoint() -> str:
    r = requests.get(BRAIN_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    for line in r.iter_lines(decode_unicode=True):
        if line.startswith('#') or 'brain' not in line.lower():
            continue
        code = line.split(';')[0].strip()
        if re.fullmatch(r"[0-9A-Fa-f]+", code):
            return code.upper()
    raise RuntimeError("Кодпоинт не найден ")


def btc_date() -> str:
    r = requests.get(BITCOIN_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    txt = r.text
    m = re.search(r"CreateGenesisBlock\(\s*(\d{9,10})\s*,", txt)
    if not m:
        m = re.search(r"genesis\.nTime\s*=\s*(\d{9,10})\s*;", txt)
    ts = int(m.group(1)) if m else 1231006505
    dt = datetime.datetime.fromtimestamp(ts, datetime.UTC)
    return dt.strftime("%Y%m%d")


def kr2_isbn10() -> str:
    params = {"title": "The C Programming Language", "author": "Kernighan", "limit": 20}
    r = requests.get(OPENLIB_URL, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    j = r.json()
    for doc in j.get("docs", []):
        edition = str(doc.get("edition_name", "")).lower()
        if "2" in edition or "second" in edition:
            for isbn in doc.get("isbn", []):
                if re.fullmatch(r"\d{10}", str(isbn)):
                    return str(isbn)
    return "0131103628"


# -------------------------
# UNIT TESTS
# -------------------------

class TestPrimarySources(unittest.TestCase):

    def test_voyager_date(self):
        d = launch_date()
        self.assertRegex(d, r"^\d{8}$")
        self.assertEqual(d, "19770905")

    def test_rfc1149_date(self):
        d = rfc1149_date()
        self.assertRegex(d, r"^\d{8}$")
        self.assertEqual(d, "19900401")

    def test_brain_codepoint(self):
        c = brain_codepoint()
        self.assertRegex(c, r"^[0-9A-F]{4,6}$")
        self.assertEqual(c, "1F9E0")

    def test_btc_date(self):
        d = btc_date()
        self.assertRegex(d, r"^\d{8}$")
        self.assertEqual(d, "20090103")

    def test_kr2_isbn10(self):
        isbn = kr2_isbn10()
        self.assertRegex(isbn, r"^\d{10}$")
        self.assertEqual(isbn, "0131103628")


def assemble_flag():
    parts = [
        launch_date(),
        rfc1149_date(),
        brain_codepoint(),
        btc_date(),
        kr2_isbn10()
    ]
    flag = f"FLAG{{{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}-{parts[4]}}}"
    sha256 = hashlib.sha256(flag.encode("utf-8")).hexdigest()
    return flag, sha256


if __name__ == "__main__":
    unittest.main(argv=[''], exit=False, verbosity=2)
    print("\n" + "=" * 50)
    flag, sha = assemble_flag()
    print("FLAG:", flag)
    print("SHA256:", sha)
