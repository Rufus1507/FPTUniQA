# FPTUniQA raw-only crawler

Install: `pip install -r requirements.txt`

Pilot:
`python scripts/crawl_raw.py --config data/seeds.json --max-depth 1 --max-pages 30 --delay 2`

Expanded run:
`python scripts/crawl_raw.py --config data/seeds.json --max-depth 2 --max-pages 150 --delay 1.5`

Outputs:
- `data/raw/fpt_admission/html/` — original HTML response bytes
- `data/raw/fpt_admission/files/` — original PDF response bytes
- `data/raw/crawl_manifest.jsonl` — one record per attempted URL

Only links under domains in `data/seeds.json` are followed. Add approved SyllaBase URLs/domains there after verifying them. The crawler does not clean, normalize, parse page content into text, or chunk it. It checks robots.txt and skips URLs when robots.txt cannot be retrieved; do not bypass login, CAPTCHA, or access controls. Review applicable site terms and permissions before large-scale crawling.
