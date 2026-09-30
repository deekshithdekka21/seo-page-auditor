from main import find_issues, suggest_improvements

# Invented test pages. Each one has at least one SEO problem.
TEST_CASES = [
    {
        "name": "Missing meta description",
        "title": "Handmade Leather Wallets | Oak & Hide",
        "meta_description": None,
        "h1": ["Handmade Leather Wallets"],
    },
    {
        "name": "Title far too long",
        "title": "Best Running Shoes for Beginners in 2026 - Complete Buying Guide With Reviews, Prices and Tips",
        "meta_description": "Find the right running shoes for your first 5K.",
        "h1": ["Best Running Shoes for Beginners"],
    },
    {
        "name": "No H1 at all",
        "title": "Contact Us | Green Leaf Bakery",
        "meta_description": "Get in touch with Green Leaf Bakery for custom cake orders.",
        "h1": [],
    },
    {
        "name": "Multiple H1s",
        "title": "Home | Summit Yoga Studio",
        "meta_description": "Yoga classes for all levels in a calm, friendly studio.",
        "h1": ["Welcome", "Our Classes", "Meet the Teachers", "Book Now"],
    },
    {
        "name": "Meta description too long",
        "title": "Eco-Friendly Cleaning Products | GreenClean",
        "meta_description": "laundry detergents, multi-surface sprays, and reusable microfiber cloths that are safe for your family, pets, and the entire planet. Free shipping on all orders over fifty dollars today!",
        "h1": ["Eco-Friendly Cleaning Products"],
    },
    {
        "name": "Duplicate H1 text",
        "title": None,
        "meta_description": "Professional web design and development services tailored for small businesses.",
        "h1": ["Affordable Web Design Services", "Affordable Web Design Services"],
    },

]


def run_eval():
    errors = 0
    passed = 0

    for case in TEST_CASES:
        issues = find_issues(case["title"], case["meta_description"], case["h1"])
        try:
            result = suggest_improvements(case["title"], case["meta_description"], case["h1"], issues)
        except Exception as error:
            print(f"[ERROR] {case['name']}: {error}\n")
            errors += 1
            continue
        remaining = find_issues(
            result.suggested_title,
            result.suggested_meta_description,
            [result.suggested_h1],
        )

        status = "PASS" if not remaining else "FAIL"
        if not remaining:
            passed += 1

        print(f"[{status}] {case['name']}")
        print(f"   title ({len(result.suggested_title)}): {result.suggested_title}")
        print(f"   meta  ({len(result.suggested_meta_description)}): {result.suggested_meta_description}")
        print(f"   h1: {result.suggested_h1}")
        if remaining:
            print(f"   remaining issues: {remaining}")
        print()

    print(f"Score: {passed}/{len(TEST_CASES) - errors}  (errors: {errors})")


if __name__ == "__main__":
    run_eval()