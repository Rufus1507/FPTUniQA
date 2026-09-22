import argparse, hashlib, json, time, urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "crawl_manifest.jsonl"
AGENT = "FPTUniQA-ResearchCrawler/1.0 (academic data collection)"
MAX_BYTES = 30 * 1024 * 1024

def now():
    return datetime.now(timezone.utc).isoformat()

def normalize(url):
    url, _ = urldefrag(url.strip())
    p = urlsplit(url)
    if p.scheme.lower() not in ("http", "https") or not p.hostname:
        return None
    scheme, host = p.scheme.lower(), p.hostname.lower()
    netloc = host
    if p.port and not ((scheme == "http" and p.port == 80) or (scheme == "https" and p.port == 443)):
        netloc += f":{p.port}"
    return urlunsplit((scheme, netloc, p.path or "/", p.query, ""))

def in_scope(url, domains):
    host = (urlsplit(url).hostname or "").lower()
    return any(host == d.lower().lstrip(".") or host.endswith("." + d.lower().lstrip("."))
               for d in domains)

def robot_allowed(url, cache):
    p = urlsplit(url)
    origin = f"{p.scheme}://{p.netloc}"

    if origin not in cache:
        robots_url = origin + "/robots.txt"
        rp = urllib.robotparser.RobotFileParser(robots_url)

        try:
            req = Request(
                robots_url,
                headers={"User-Agent": AGENT}
            )

            with urlopen(req, timeout=15) as response:
                status = response.status
                content = response.read().decode(
                    "utf-8", errors="replace"
                )

            if status == 200:
                rp.parse(content.splitlines())
                cache[origin] = rp

            else:
                cache[origin] = None

        except HTTPError as e:
            # HTTP 404: robots.txt không tồn tại.
            # Các lỗi khác: giữ cách xử lý thận trọng.
            if e.code == 404:
                cache[origin] = "no_robots_file"
            else:
                cache[origin] = None

        except Exception:
            # Nếu gặp lỗi mạng hoặc không xác định được trạng thái,
            # không tự động bỏ qua quy tắc truy cập.
            cache[origin] = None

    rules = cache[origin]

    if rules == "no_robots_file":
        return True

    if rules is None:
        return False

    return rules.can_fetch(AGENT, url)

def write_record(record):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def fetch(url):
    req = Request(url, headers={"User-Agent": AGENT,
        "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.5"})
    with urlopen(req, timeout=25) as r:
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Response exceeds 30 MiB safety limit")
        return r.status, r.geturl(), r.headers.get_content_type().lower(), data

def store(url, ctype, data):
    if ctype in ("text/html", "application/xhtml+xml"):
        folder, ext = RAW/"fpt_admission/html", ".html"
    elif ctype == "application/pdf":
        folder, ext = RAW/"fpt_admission/files", ".pdf"
    else:
        return None
    folder.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(url.encode()).hexdigest()[:24] + ext
    path = folder/name
    path.write_bytes(data)  # preserve response bytes; no text processing
    return path.relative_to(ROOT).as_posix()

def links(data, base):
    soup = BeautifulSoup(data, "html.parser")
    result = []
    for a in soup.find_all("a", href=True):
        u = normalize(urljoin(base, a["href"]))
        if u:
            result.append((u, " ".join(a.get_text(" ", strip=True).split())[:300]))
    return result

def normalize_text(text: str) -> str:
    """Lowercase and remove Vietnamese diacritics for keyword matching."""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def is_relevant_link(url: str, anchor_text: str) -> bool:
    """
    Decide whether a discovered link is worth crawling for the current
    admissions/tuition/scholarship/major data collection task.
    Seed URLs are still crawled regardless of this filter.
    """
    path = normalize_text(urlsplit(url).path)
    anchor = normalize_text(anchor_text)
    combined = path + " " + anchor

    include_terms = [
        "tuyen-sinh", "tuyen sinh",
        "hoc-phi", "hoc phi",
        "hoc-bong", "hoc bong",
        "uu-dai", "uu dai",
        "tai-chinh", "tai chinh",
        "nhap-hoc", "nhap hoc",
        "phuong-thuc", "phuong thuc",
        "nganh", "chuyen-nganh", "chuyen nganh",
        "chuong-trinh-dao-tao", "chuong trinh dao tao",
        "cong-nghe-thong-tin", "cong nghe thong tin",
        "tri-tue-nhan-tao", "tri tue nhan tao",
        "marketing", "ky-thuat-phan-mem", "ky thuat phan mem",
        "khoa-hoc-du-lieu", "khoa hoc du lieu",
        "an-toan-thong-tin", "an toan thong tin",
        "de-an-tuyen-sinh", "quy-che-tuyen-sinh",
        "hoc-bong-nguyen-van-dao",
    ]

    exclude_terms = [
        "/en/", "/en",
        "facebook.com", "youtube.com", "instagram.com",
        "tiktok.com", "linkedin.com",
        "dang-nhap", "login", "logout",
        "wp-admin", "wp-login",
        "mailto:", "tel:",
    ]

    if any(term in combined for term in exclude_terms):
        return False

    return any(term in combined for term in include_terms)

def run(config_path, max_depth, max_pages, delay):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    domains = cfg.get("allowed_domains", [])
    seeds = [normalize(x) for x in cfg.get("seed_urls", [])]
    seeds = [x for x in seeds if x]
    if not seeds or not domains:
        raise SystemExit("Config requires seed_urls and allowed_domains.")

    q = deque((u, 0, None, None) for u in seeds)
    seen, robots, attempted = set(), {}, 0
    while q and attempted < max_pages:
        url, depth, parent, anchor = q.popleft()
        if url in seen:
            continue
        seen.add(url)
        if not in_scope(url, domains):
            continue
        rec = {"url": url, "final_url": None, "source": "fpt_admission",
               "parent_url": parent, "link_text": anchor, "depth": depth,
               "status_code": None, "content_type": None, "raw_file": None,
               "content_hash": None, "crawled_at": now(), "error": None}
        attempted += 1
        if not robot_allowed(url, robots):
            rec["error"] = "Disallowed by robots.txt or robots.txt unavailable; skipped."
            write_record(rec)
            print("[SKIP robots]", url)
            continue
        try:
            status, final_url, ctype, data = fetch(url)
            rec.update(final_url=final_url, status_code=status, content_type=ctype,
                       content_hash=hashlib.sha256(data).hexdigest(),
                       raw_file=store(url, ctype, data))
            write_record(rec)
            print(f"[{status}] {ctype} depth={depth} {url}")
            if status == 200 and ctype in ("text/html", "application/xhtml+xml") and depth < max_depth:
                for child, label in links(data, final_url):
                    if (
                            child not in seen
                            and in_scope(child, domains)
                            and is_relevant_link(child, label)
                    ):
                        q.append((child, depth + 1, url, label))
        except HTTPError as e:
            rec.update(status_code=e.code, final_url=e.geturl(), error=f"HTTPError: {e.reason}")
            write_record(rec)
            print(f"[HTTP {e.code}]", url)
        except (URLError, TimeoutError, ValueError, OSError, Exception) as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            write_record(rec)
            print("[ERROR]", url, rec["error"])
        time.sleep(delay)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="FPTUniQA raw-only link crawler")
    ap.add_argument("--config", type=Path, default=ROOT/"data/seeds.json")
    ap.add_argument("--max-depth", type=int, default=2)
    ap.add_argument("--max-pages", type=int, default=150)
    ap.add_argument("--delay", type=float, default=1.5)
    args = ap.parse_args()
    if args.max_depth < 0 or args.max_pages < 1 or args.delay < 0:
        ap.error("max-depth >= 0, max-pages >= 1, delay >= 0 required")
    config = args.config if args.config.is_absolute() else ROOT/args.config
    run(config, args.max_depth, args.max_pages, args.delay)
