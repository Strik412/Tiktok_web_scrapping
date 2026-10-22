# TikTok Web Scraping — Profile & Recent Posts

A Python project that uses **Selenium** and **Beautiful Soup** to collect publicly accessible TikTok profile information and metadata from a limited set of visible posts, then exports the results to **JSON** and **CSV** for further analysis. 

This project now also features an **Advanced NLP Semantic Analysis** pipeline and a **Generative AI Integration (Google Gemini)** to extract insights, keywords, semantic clusters, and a psychological profile (Digital Phenotyping) from the downloaded posts.

## Features

- Accept a TikTok username interactively or through a command-line argument.
- Open the public profile in Google Chrome using Selenium.
- Try to extract profile details from embedded page JSON and HTML metadata.
- Collect visible links to public **video** and **photo** posts, with optional scrolling.
- Visit a configurable number of candidate post pages and try to extract descriptions, timestamps, engagement metrics, hashtags, music, and cover images.
- Sort posts with available publication timestamps in descending order and export up to the requested number of posts (10 by default).
- Save the extracted profile and post records in UTF-8-compatible JSON and CSV files.
- **[NEW] Anti-Bot Scraping:** Uses `undetected-chromedriver` and persistent browser profiles to safely bypass TikTok's firewall (Error 403), with a human-in-the-loop fallback to solve CAPTCHAs manually.
- **[NEW] NLP Text Processing:** Cleans post descriptions by removing URLs, mentions, and special characters, and extracts the most relevant keywords using **TF-IDF**.
- **[NEW] Semantic Embeddings:** Uses HuggingFace's `Sentence-Transformers` (Multilingual MiniLM) to convert text into 384-dimensional semantic vectors.
- **[NEW] Visual Analytics:** Generates interactive dashboards featuring Top Keywords (Bar Chart), Semantic Cosine Similarity (Heatmap), and 2D Semantic Clustering (PCA Scatter Plot).
- **[NEW] AI Personality Profiling (Big Five):** Integrates the Google Gemini API to analyze the unstructured extracted text and evaluate the creator's digital phenotype based on the OCEAN psychological model.

**Important:** The scraper can return incomplete data. TikTok may change its page structure, require verification, withhold fields, or limit publicly accessible content. The tool does **not** guarantee that the exported posts are the account's absolute latest 10 posts. See [Limitations](#limitations).

## Tech Stack

| Tool | Purpose |
| --- | --- |
| Python 3 | Application logic, parsing, validation, and export |
| Selenium | Browser automation with Chrome |
| Google Chrome | Browser used to load TikTok pages |
| Beautiful Soup 4 | HTML parsing and metadata extraction |
| Undetected-Chromedriver | Advanced browser automation bypassing bot detection |
| Pandas & NumPy | Data manipulation and structuring |
| Scikit-learn | TF-IDF, Cosine Similarity, and PCA reduction |
| Sentence-Transformers | HuggingFace multilingual semantic embeddings |
| NLTK | Natural Language Toolkit for stopwords |
| Matplotlib & Seaborn | Data visualization and plotting |
| Google GenAI SDK | Gemini API connection for Zero-Shot Text Classification |
| Python standard library | `argparse`, `csv`, `json`, `re`, `time`, `datetime`, `pathlib`, `urllib.parse`, `random` |

**No TikTok API credentials are required.** The application reads what is available through the web page, not through the official TikTok API.

## Project Structure

```text
Tiktok - web scraping/
├── app.py                     # Main scraper
├── analisis/
│   ├── nlp.py                 # NLP, Embeddings, and Visualization script
│   └── analisis_big_five.py   # Google Gemini API integration script
├── assets/                    # Project screenshots and images
├── README.md                  # Project documentation
├── .gitignore                 # Recommended (see below)
├── .venv/                     # Local Python environment (not committed)
├── Perfil_TikTok/             # Persistent Chrome profile data (auto-generated)
└── resultados/                # Created at runtime
    └── <username>/
        ├── perfil_completo.json
        ├── perfil.csv
        ├── ultimos_10_posts.json
        ├── ultimos_10_posts.csv
        └── reporte_big_five.txt

```

## Prerequisites

* Windows, macOS, or Linux with **Python 3** installed (Python 3.10+ recommended).
* **Google Chrome** installed.
* A working Internet connection.
* VS Code or another editor (optional).
* A free **Google Gemini API Key** (from Google AI Studio) for the Big Five analysis.

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
python -m pip install selenium undetected-chromedriver beautifulsoup4 pandas scikit-learn sentence-transformers matplotlib seaborn nltk google-genai

```


6. Ensure the main script is named **`app.py`** and is located in the project root.

If PowerShell prevents activation, use the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install selenium undetected-chromedriver beautifulsoup4 pandas scikit-learn sentence-transformers matplotlib seaborn nltk google-genai
.\.venv\Scripts\python.exe app.py --username tiktok

```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install selenium undetected-chromedriver beautifulsoup4 pandas scikit-learn sentence-transformers matplotlib seaborn nltk google-genai
python app.py --username tiktok

```

## Usage

### Step 1: Data Extraction

Run the scraper by passing the target TikTok username and the number of posts you want to extract.

```powershell
python app.py --username _rl9 --posts 10

```

*Note: A Chrome window will open. The bot uses random sleep intervals and silent navigation. If TikTok hides the data, the script triggers a manual fallback allowing you to solve CAPTCHAs.*

<p align="center">
  <img src="images/Captura%20de%20pantalla%202026-10-22%20054517.png" width="800" alt="Scraping Log 1"><br>
  <em>Manual fallback intervention during extraction.</em>
</p>
<p align="center">
  <img src="images/Captura%20de%20pantalla%202026-10-22%20054529.png" width="800" alt="Scraping Log 2"><br>
  <em>Humanized browsing successfully evading the 403 firewall.</em>
</p>

### Step 2: Semantic Analysis (NLP)

After successfully extracting data into the `resultados/` folder, run the NLP script to generate the data science visualizations. Make sure you update the `username` variable inside `nlp.py` to match the extracted account.

```powershell
python analisis/nlp.py

```

<p align="center">
  <img src="images/Captura%20de%20pantalla%202026-10-22%20055256.png" width="1000" alt="NLP Dashboard"><br>
  <em>Interactive Dashboard showing TF-IDF Keywords, Semantic Cosine Similarity, and PCA Clustering.</em>
</p>

### Step 3: Generative AI Profiling (Big Five)

To generate the psychological profile based on the linguistic choices of the user, run the AI integration script. Remember to insert your Google AI Studio API Key inside the script.

```powershell
python analisis/analisis_big_five.py

```
<p align="center">
  <img src="images/Captura%20de%20pantalla%202026-10-22%20140413.png" width="800" alt="Big Five Analysis 1"><br>
  <img src="images/Captura%20de%20pantalla%202026-10-22%20140427.png" width="800" alt="Big Five Analysis 2"><br>
  <em>Zero-Shot Digital Phenotyping results leveraging Google's Gemini SDK.</em>
</p>

## How It Works

1. **Input validation:** `main()` reads and validates the username and numeric options.
2. **Browser startup:** Selenium launches Chrome with a 1280 × 900 window using `undetected-chromedriver` and a persistent profile (`Perfil_TikTok/`).
3. **Profile loading:** The bot opens `https://www.tiktok.com/@<username>` and pauses. *A human-in-the-loop manual intervention is required here to solve CAPTCHAs and scroll down to load post thumbnails.*
4. **Profile parsing:** `obtener_perfil()` looks for user data in embedded JSON scripts named `__UNIVERSAL_DATA_FOR_REHYDRATION__` and `SIGI_STATE`, with HTML Open Graph metadata as a fallback for selected fields.
5. **Post discovery:** `obtener_enlaces()` finds links matching the profile's `/video/<id>` or `/photo/<id>` paths. Additional scrolls may expose more links.
6. **Candidate inspection:** The discovered links are **sorted lexicographically**, and only the first `--candidatos` links are visited. This selection is **not chronological**.
7. **Post parsing (Silent Navigation):** `extraer_post()` uses JavaScript navigation (`window.location.href`) and random time sleeps to evade 403 Forbidden errors, looking for post details in embedded JSON.
8. **Ordering:** Posts with valid publication timestamps are sorted newest first. Records with missing timestamps are placed afterward.
9. **Export:** `guardar_resultados()` writes the profile and the selected post records into a username-specific directory under `resultados/`.
10. **Cleanup:** Selenium closes Chrome in a `finally` block.

### NLP & Semantic Analysis Pipeline (`nlp.py`)

1. **Cleaning:** The script reads the generated CSV, removes URLs, mentions, and special characters from post descriptions.
2. **TF-IDF Extraction:** NLTK filters out English/Spanish stopwords and Scikit-learn calculates the top keywords defining the account's content.
3. **Semantic Embeddings:** A pre-trained HuggingFace model (`paraphrase-multilingual-MiniLM-L12-v2`) converts text into mathematical vectors.
4. **Visualization:** Matplotlib plots a Bar Chart (Keywords), a Cosine Similarity Heatmap (to find duplicate or related content), and a PCA 2D Scatter Plot (to visually cluster posts talking about similar topics).

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

* **`perfil_completo.json`** — one JSON object with profile fields.
* **`perfil.csv`** — one-row CSV with the same fields.

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

* **`ultimos_10_posts.json`** — list of up to `--posts` records.
* **`ultimos_10_posts.csv`** — tabular version of the selected posts.
* **`reporte_big_five.txt`** — Generative AI diagnostic text.

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

**`ModuleNotFoundError: No module named 'selenium'` (or other libraries)**

Install packages into the same interpreter used to run the script:

```powershell
python -m pip install selenium undetected-chromedriver beautifulsoup4 pandas scikit-learn sentence-transformers matplotlib seaborn nltk google-genai

```

**Chrome / ChromeDriver cannot start**

Confirm that Chrome is installed, update Selenium, and verify that your environment can download or locate the appropriate driver:

```powershell
python -m pip install --upgrade selenium undetected-chromedriver

```

**HTTP Error 403 or "Access Denied"**

TikTok's firewall has temporarily blacklisted your IP address. Switch your connection to a mobile hotspot or restart your router to obtain a new IP address, then run the script again.

**Zero posts or empty fields**

TikTok may not have exposed post links or embedded metadata in the page response. The script pauses intentionally to allow you to manually solve CAPTCHAs or scroll the page before pressing ENTER.

**Fewer than 10 posts saved**

Only discovered and inspected posts can be exported. Try a modestly larger `--scrolls` or `--candidatos` value when access is permitted, and remember that the script cannot guarantee a complete chronology.

**`google.genai.errors.ClientError: 404 NOT_FOUND`**

Ensure your Google AI API key is correctly inserted in `analisis_big_five.py` and that the requested model name (e.g., `gemini-3.8-flash`) is supported in your region.

## Recommended `.gitignore`

Create `.gitignore` in the repository root:

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
resultados/
analisis/resultados/
Perfil_TikTok/
*.npy
.DS_Store

```

This avoids committing local dependencies, potentially sensitive extracted data, browser cookies, and future generated artifacts.
