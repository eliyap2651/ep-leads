from app.services.dedup import (
    build_dedup_key,
    extract_domain,
    is_probable_duplicate,
    normalize_email,
    normalize_phone,
)


def test_extract_domain_strips_www_and_scheme():
    assert extract_domain("https://www.example.co.il/path?x=1") == "example.co.il"
    assert extract_domain("example.co.il") == "example.co.il"
    assert extract_domain(None) is None


def test_normalize_phone_handles_international_prefix():
    assert normalize_phone("+972-50-1234567") == "0501234567"
    assert normalize_phone(None) is None


def test_normalize_email_lowercases():
    assert normalize_email("Someone@Example.COM") == "someone@example.com"


def test_dedup_key_priority_tender_number_first():
    key = build_dedup_key(tender_number="2026/12", domain_website="https://x.com", phone="0500000000")
    assert key == "tender:2026/12"


def test_dedup_key_falls_back_to_company_and_city():
    key = build_dedup_key(company_name='חברת דוגמה בע"מ', city="חיפה")
    assert key == "company:חברת דוגמה:חיפה"


def test_is_probable_duplicate_by_tender_number():
    assert is_probable_duplicate({"tender_number": "TND-1"}, {"tender_number": "tnd-1"})


def test_is_probable_duplicate_by_domain():
    a = {"domain_website": "https://www.acme.co.il"}
    b = {"domain_website": "http://acme.co.il/about"}
    assert is_probable_duplicate(a, b)


def test_not_duplicate_when_nothing_matches():
    assert not is_probable_duplicate({"company_name": "אלפא"}, {"company_name": "בטא"})


def test_fuzzy_company_name_match_same_city():
    a = {"company_name": "עיריית תל אביב יפו", "city": "תל אביב"}
    b = {"company_name": "עיריית תל אביב-יפו", "city": "תל אביב"}
    assert is_probable_duplicate(a, b)
