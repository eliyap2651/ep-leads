from app.services.contact_extraction import extract_emails, extract_phones, looks_like_business_whatsapp


def test_extract_emails_finds_valid_addresses():
    text = "לפרטים ניתן לפנות ל: rechesh@example.co.il או לחילופין office@company.com."
    emails = extract_emails(text)
    assert "rechesh@example.co.il" in emails
    assert "office@company.com" in emails


def test_extract_emails_empty_when_none_found():
    assert extract_emails("אין כאן שום כתובת מייל") == []


def test_extract_phones_finds_israeli_landline_and_mobile():
    text = "משרד הרכש: 03-1234567, נייד מנהל הרכש: 050-1234567"
    phones = extract_phones(text)
    assert len(phones) == 2


def test_extract_phones_empty_when_none_found():
    assert extract_phones("אין כאן מספר טלפון") == []


def test_looks_like_business_whatsapp_mobile_only():
    assert looks_like_business_whatsapp("050-123-4567") is True
    assert looks_like_business_whatsapp("03-1234567") is False
