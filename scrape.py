import requests
from pathlib import Path
from tqdm import tqdm

series_to_readable = {"w": "OctNov", "m": "FebMar", "s": "MayJun"}


def download_paper(subject, year, series, code):
    if subject == "0500" or (subject == "0450" and code.startswith("2")):
        download_file(subject, year, series, code, "in", "pdf")
    if subject == "0549" and code == "02":
        download_file(subject, year, series, code, "sf", "mp3")
    if subject == "0417":
        download_file(subject, year, series, code, "sf", "zip")
    download_file(subject, year, series, code, "qp", "pdf")
    download_file(subject, year, series, code, "ms", "pdf")


def download_file(subject, year, series, code, qp_or_ms, ext):
    url = f"https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{subject}_{series}{year}_{qp_or_ms}_{code}.{ext}"
    r = requests.get(
        url,
        stream=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        },
    )
    path = Path(f"Papers/{subject}/20{year}_{series_to_readable[series]}")
    path.mkdir(parents=True, exist_ok=True)
    with open(path / f"{qp_or_ms}_{code}.{ext}", "wb") as h:
        h.write(r.content)


subjects = ["0450"]
codes = ["21", "22", "23"]
serieses = ["w", "m", "s"]
with tqdm(total=len(subjects) * len(codes) * len(serieses) * 4) as pbar:
    for subject in subjects:
        for year in range(20, 24):
            for series in serieses:
                for code in codes:
                    download_paper(subject, year, series, code)
                    pbar.update()
