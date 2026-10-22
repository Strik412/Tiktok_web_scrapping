# TikTok Web Scraping — Profile & Recent Posts

A Python project that uses **Selenium** and **Beautiful Soup** to collect publicly accessible TikTok profile information and metadata from a limited set of visible posts, then exports the results to **JSON** and **CSV** for further analysis.

## Features

- Accept a TikTok username interactively or through a command-line argument.
- Open the public profile in Google Chrome using Selenium.
- Try to extract profile details from embedded page JSON and HTML metadata.
- Collect visible links to public **video** and **photo** posts, with optional scrolling.
- Visit a configurable number of candidate post pages and try to extract descriptions, timestamps, engagement metrics, hashtags, music, and cover images.
- Sort posts with available publication timestamps in descending order and export up to the requested number of posts (10 by default).
- Save the extracted profile and post records in UTF-8-compatible JSON and CSV files.

**Important:** The scraper can return incomplete data. TikTok may change its page structure, require verification, withhold fields, or limit publicly accessible content. The tool does **not** guarantee that the exported posts are the account's absolute latest 10 posts. See [Limitations](#limitations).

## Tech Stack

| Tool | Purpose |
| --- | --- |
| Python 3 | Application logic, parsing, validation, and export |
| Selenium | Browser automation with Chrome |
| Google Chrome | Browser used to load TikTok pages |
| Beautiful Soup 4 | HTML parsing and metadata extraction |
| Python standard library | `argparse`, `csv`, `json`, `re`, `time`, `datetime`, `pathlib`, `urllib.parse` |

**No TikTok API credentials are required.** The application reads what is available through the web page, not through the official TikTok API.

## Project Structure

```text
Tiktok - web scraping/
├── app.py                     # Main scraper
├── README.md                  # Project documentation
├── .gitignore                 # Recommended (see below)
├── .venv/                     # Local Python environment (not committed)
└── resultados/                # Created at runtime
    └── <username>/
        ├── perfil_completo.json
        ├── perfil.csv
        ├── ultimos_10_posts.json
        └── ultimos_10_posts.csv
```

## Prerequisites

- Windows, macOS, or Linux with **Python 3** installed (Python 3.10+ recommended).
- **Google Chrome** installed.
- A working Internet connection.
- VS Code or another editor (optional).

Recent Selenium versions normally use Selenium Manager to resolve an appropriate ChromeDriver automatically. Driver installation can still fail in restricted environments or when Chrome and the driver cannot be matched.

## Setup (Windows PowerShell / VS Code)

1. Open the project folder in VS Code (**File → Open Folder**).
2. Open a terminal (**Terminal → New Terminal**).
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Activate the environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

5. Install the dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install selenium beautifulsoup4
   ```

6. Ensure the main script is named **`app.py`** and is located in the project root.

If PowerShell prevents activation, use the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install selenium beautifulsoup4
.\.venv\Scripts\python.exe app.py --username tiktok
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install selenium beautifulsoup4
python app.py --username tiktok
```

## Usage

### Interactive mode

```powershell
python app.py
```

When prompted, enter a username with or without the leading `@`:

```text
Username de TikTok: tiktok
```

### Command-line mode

```powershell
python app.py --username tiktok
```

### Request up to 10 posts

```powershell
python app.py --username tiktok --posts 10 --scrolls 6 --candidatos 25
```

### Inspect more candidate posts

```powershell
python app.py --username tiktok --posts 10 --scrolls 8 --candidatos 30
```

### CLI arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--username` | Interactive prompt | TikTok username (`@` is optional). |
| `--posts` | `10` | Maximum number of post records saved. Must be at least 1. |
| `--scrolls` | `6` | Number of downward scrolling actions on the profile. Must be 0 or greater. |
| `--candidatos` | `25` | Maximum number of discovered post links to inspect individually. Must be at least 1. |

The username is checked against the script's accepted pattern: 1–24 characters consisting of letters, digits, periods, or underscores.

## How It Works

1. **Input validation:** `main()` reads and validates the username and numeric options.
2. **Browser startup:** Selenium launches Chrome with a 1280 × 900 window.
3. **Profile loading:** `recopilar_enlaces()` opens `https://www.tiktok.com/@<username>` and waits for the document's main load to finish.
4. **Profile parsing:** `obtener_perfil()` looks for user data in embedded JSON scripts named `__UNIVERSAL_DATA_FOR_REHYDRATION__` and `SIGI_STATE`, with HTML Open Graph metadata as a fallback for selected fields.
5. **Post discovery:** `obtener_enlaces()` finds links matching the profile's `/video/<id>` or `/photo/<id>` paths. Additional scrolls may expose more links.
6. **Candidate inspection:** The discovered links are **sorted lexicographically**, and only the first `--candidatos` links are visited. This selection is **not chronological**.
7. **Post parsing:** `extraer_post()` looks for post details in embedded JSON (`webapp.video-detail` or legacy `ItemModule`) and uses page metadata for a description fallback.
8. **Ordering:** Posts with valid publication timestamps are sorted newest first. Records with missing timestamps are placed afterward.
9. **Export:** `guardar_resultados()` writes the profile and the selected post records into a username-specific directory under `resultados/`.
10. **Cleanup:** Selenium closes Chrome in a `finally` block.

### Main Functions

| Function | Responsibility |
| --- | --- |
| `leer_json()` | Parse supported embedded JSON scripts. |
| `leer_meta()` | Read HTML meta tags. |
| `obtener_perfil()` | Extract account fields and aggregate statistics. |
| `obtener_enlaces()` | Discover matching public post links in HTML. |
| `esperar_pagina()` | Wait for `document.readyState == "complete"`. |
| `recopilar_enlaces()` | Load profile and collect additional links through scrolling. |
| `encontrar_item()` | Search supported JSON structures for a post ID. |
| `fecha_utc()` | Convert Unix timestamps to UTC ISO 8601 strings. |
| `extraer_post()` | Extract an individual post's metadata and metrics. |
| `guardar_csv()` | Write rows to a CSV file. |
| `guardar_resultados()` | Save profile and post JSON/CSV output. |
| `main()` | Coordinate command-line input, scraping, ordering, and output. |

## Exported Data

The output directory is created automatically:

```text
resultados/<username>/
```

### Profile files

- **`perfil_completo.json`** — one JSON object with profile fields.
- **`perfil.csv`** — one-row CSV with the same fields.

Potential profile fields:

| Field | Meaning |
| --- | --- |
| `username` | TikTok username |
| `nombre` | Display name |
| `biografia` | Profile biography / description |
| `avatar` | Profile image URL |
| `verificado` | Verification flag, if available |
| `privado` | Private-account flag, if available |
| `seguidores` | Followers count |
| `siguiendo` | Following count |
| `likes` | Total profile likes |
| `videos` | Profile video count |
| `url` | Public profile URL |

### Post files

- **`ultimos_10_posts.json`** — list of up to `--posts` records.
- **`ultimos_10_posts.csv`** — tabular version of the selected posts.

The filenames contain “10” for compatibility with the current implementation, **even if `--posts` is set to a different number**.

| Field | Meaning |
| --- | --- |
| `id` | Post identifier from its URL |
| `tipo` | `video` or `photo` |
| `url` | Post URL |
| `descripcion` | Post description or available fallback metadata |
| `fecha_publicacion_utc` | Publication time in UTC, when available |
| `visualizaciones` | Play/view count, when available |
| `likes` | Likes count |
| `comentarios` | Comment count |
| `compartidos` | Share count |
| `guardados` | Save/collect count |
| `duracion_segundos` | Video duration in seconds, when provided |
| `hashtags` | Comma-separated hashtags |
| `musica` | Music or sound title |
| `portada` | Cover image URL |

**Missing values:** JSON may contain `null`, and CSV cells may be blank. Missing metrics must not be interpreted as zero.


## Troubleshooting

**`python: can't open file '.../app.py'`**  
Check that the terminal is open in the correct project folder and the file is actually named `app.py`:

```powershell
Get-Location
Get-ChildItem -Name
python .\app.py --username tiktok
```

**`ModuleNotFoundError: No module named 'selenium'`**  
Install packages into the same interpreter used to run the script:

```powershell
python -m pip install selenium beautifulsoup4
```

**Chrome / ChromeDriver cannot start**  
Confirm that Chrome is installed, update Selenium, and verify that your environment can download or locate the appropriate driver:

```powershell
python -m pip install --upgrade selenium
```

**Zero posts or empty fields**  
TikTok may not have exposed post links or embedded metadata in the page response. Inspect the visible page in Chrome. Do not interpret missing values as valid zero counts and do not attempt to bypass verification challenges.

**Fewer than 10 posts saved**  
Only discovered and inspected posts can be exported. Try a modestly larger `--scrolls` or `--candidatos` value when access is permitted, and remember that the script cannot guarantee a complete chronology.

## Recommended `.gitignore`

Create `.gitignore` in the repository root:

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
resultados/
analisis/resultados/
*.npy
.DS_Store
```

This avoids committing local dependencies, potentially sensitive extracted data, and future generated artifacts.
