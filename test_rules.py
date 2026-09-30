from main import find_issues, is_public_host
GOOD_META = "Handmade leather wallets and card holders, crafted in small batches and shipped worldwide."

def test_good_page_has_no_issues():
    issues = find_issues(
        "Handmade Leather Wallets | Oak & Hide",
        GOOD_META,
        ["Handmade Leather Wallets"],
    )
    assert issues == []


def test_missing_meta_description():
    issues = find_issues("A Good Title", None, ["One Heading"])
    assert issues == ["Meta description is missing."]

def test_meta_description_too_short():
    issues = find_issues(title="A Good Title", meta_description="A" * 69, h1=["Main Heading"])
    assert issues == ["Meta description is too short (69 characters). Aim for 70 or more."]


def test_missing_title():
    issues = find_issues(None, GOOD_META, ["This is heading too"])
    assert issues == ["Title is missing."]


def test_title_too_long():
    issues = find_issues("A" * 61, GOOD_META, ["One Heading"])
    assert issues == ["Title is too long (61 characters). Aim for 60 or fewer."]


def test_no_h1():
    issues = find_issues("Wonderful Vacations @LA", GOOD_META, [])
    assert issues == ["No H1 heading found."]


def test_multiple_h1s():
    issues = find_issues(
        "Wonderful Vacations @LA",
        GOOD_META,
        ["Get your Passport", "Cheap Tickets", "Getting Phones"],
    )
    assert issues == ["Multiple H1 headings found (3). Use one main H1."]


def test_loopback_is_blocked():
    assert is_public_host("127.0.0.1") is False


def test_private_network_is_blocked():
    assert is_public_host("10.0.0.5") is False


def test_cloud_metadata_is_blocked():
    assert is_public_host("169.254.169.254") is False


def test_public_address_is_allowed():
    assert is_public_host("8.8.8.8") is True
