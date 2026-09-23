import html
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime

EMDB_SEARCH_URL = "https://www.ebi.ac.uk/emdb/api/search/"


def get_emdb_image_url(accession):
    """Constructs static image path from accession string."""
    num_str = accession.upper().replace("EMD-", "").replace("EMD_", "").strip()
    if not num_str.isdigit():
        return "https://www.ebi.ac.uk/emdb/static/images/emdb_placeholder.png"

    padded = num_str.zfill(3)
    dir1 = padded[0:2]
    dir2 = padded[2]

    return f"https://www.ebi.ac.uk/emdb/static/em/{dir1}/{dir2}/{num_str}/images/400_{num_str}.gif"


def fetch_emdb_released_entries(target_date):
    """
    Queries EMDB API for entries released on target_date (YYYY-MM-DD).
    Uses Lucene query format matching API parameters.
    """
    # Formats target_date for ISO timestamp query range (or exact release date string)
    query = f'release_date:"{target_date}T00:00:00Z" AND database:EMDB'
    encoded_query = urllib.parse.quote(query, safe="")

    results = []
    rows = 100
    page = 1
    headers = {"User-Agent": "Structure-Intelligence/1.0"}

    while True:
        url = f"{EMDB_SEARCH_URL}{encoded_query}?rows={rows}&page={page}"
        request = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                entries = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"[ERROR] Failed fetching release date {target_date} page {page}: {e}")
            break

        if not entries:
            break

        for elem in entries:
            admin = elem.get("admin", {})
            title = str(admin.get("title", "") or "").strip()

            author_list = admin.get("authors_list", {}).get("author", [])
            if isinstance(author_list, dict):
                author_list = [author_list]

            authors = ", ".join(
                str(author.get("valueOf_", "") or "").strip()
                for author in author_list
                if str(author.get("valueOf_", "") or "").strip()
            )

            if "SUPPRESSED" in authors and title == "SUPPRESSED":
                continue

            status = (
                admin.get("current_status", {})
                .get("code", {})
                .get("valueOf_", "REL")
            )

            accession = str(elem.get("emdb_id", "") or "").strip().upper()

            results.append({
                "accession": accession,
                "title": title or "No Title Available",
                "authors": authors or "Unknown Authors",
                "status": str(status or "REL").strip(),
                "date": target_date,
            })

        page += 1

    return results


def generate_tsv(entries, output_file):
    """Saves entry summary into TSV format."""
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(
                f"{entry['accession']}\t{entry['title']}\t{entry['authors']}\t{entry['status']}\t{entry['date']}\n"
            )


def generate_html_from_tsv(tsv_file, template_file, modal_block_file, output_file, target_date):
    """Parses TSV and constructs the HTML site for GitHub Pages."""
    entries = []
    if os.path.exists(tsv_file):
        with open(tsv_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 5:
                    entries.append({
                        "accession": parts[0],
                        "title": parts[1],
                        "authors": parts[2],
                        "status": parts[3],
                        "date": parts[4],
                    })

    entries = sorted(entries, key=lambda x: x["accession"])
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    thumbnail_html = ""
    js_entries = []

    for i, entry in enumerate(entries):
        acc = entry["accession"]
        safe_title = html.escape(entry["title"])
        safe_authors = html.escape(entry["authors"])

        thumb_url = get_emdb_image_url(acc)
        emdb_page = f"https://www.ebi.ac.uk/emdb/{acc}"

        thumbnail_html += f"""
<div class="card" onclick="openModal({i})">
  <div class="img-container">
    <img src="{thumb_url}" alt="{acc}" onerror="this.onerror=null;this.src='https://www.ebi.ac.uk/emdb/static/images/emdb_placeholder.png';">
  </div>
  <div class="entry-id">{acc}</div>
  <div class="entry-title">
    <a href="{emdb_page}" target="_blank" onclick="event.stopPropagation()">{safe_title}</a>
  </div>
  <div class="entry-status"><span class="badge">{entry['status']}</span> &bull; Released: {entry['date']}</div>
</div>
"""

        escaped_acc = html.escape(acc)
        escaped_title = html.escape(entry["title"]).replace('"', '\\"')

        js_entries.append(
            f'{{id: "{escaped_acc}", '
            f'title: "{escaped_title}", '
            f'authors: "{safe_authors}", '
            f'status: "{entry["status"]}", '
            f'date: "{entry["date"]}", '
            f'img_url: "{thumb_url}", '
            f'link: "{emdb_page}"}}'
        )

    image_data_js = ",\n".join(js_entries)

    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    with open(modal_block_file, "r", encoding="utf-8") as f:
        modal_block = f.read().replace("{{IMAGE_DATA}}", image_data_js)

    final_html = (
        template.replace("{{TIMESTAMP}}", f"{now} (Release Date: {target_date})")
        .replace("{{THUMBNAILS}}", thumbnail_html)
        .replace("{{MODAL_JS}}", modal_block)
    )

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)


if __name__ == "__main__":
    template_path = sys.argv[1] if len(sys.argv) > 1 else ".github/scripts/emdb_template.html"
    modal_path = sys.argv[2] if len(sys.argv) > 2 else ".github/scripts/emdb_modal_block.js"
    fetch_flag = sys.argv[3] if len(sys.argv) > 3 else "yes"

    # Target date passed as 4th arg, defaults to current UTC date (YYYY-MM-DD)
    release_date = sys.argv[4] if len(sys.argv) > 4 else datetime.utcnow().strftime("%Y-%m-%d")

    tsv_path = "emdb_entries.tsv"

    if fetch_flag.lower() == "yes":
        print(f"Fetching EMDB releases for date: {release_date}...")
        records = fetch_emdb_released_entries(release_date)
        print(f"Fetched {len(records)} entries. Writing TSV...")
        generate_tsv(records, tsv_path)

    generate_html_from_tsv(
        tsv_file=tsv_path,
        template_file=template_path,
        modal_block_file=modal_path,
        output_file="docs/index.html",
        target_date=release_date,
    )
    print("EMDB summary page built successfully at docs/index.html.")