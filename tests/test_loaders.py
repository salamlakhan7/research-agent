from app.services.loaders import load_many

urls = [
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://arxiv.org/pdf/1706.03762",
    "https://www.youtube.com/watch?v=zjkBMFhNj_g",
    "https://this-site-does-not-exist-12345.com",
]

sources, failed = load_many(urls)

for s in sources:
    print("OK  ", s.url, "|", s.title[:50], "|", len(s.text), "chars")
for u, reason in failed.items():
    print("FAIL", u, "->", reason)