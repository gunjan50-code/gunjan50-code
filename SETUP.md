# Setup

A terminal-style GitHub profile README built from three self-hosted animated SVGs:
an ASCII portrait that types itself in, a 3D ASCII wordmark that rocks on its
axis, and a real contribution heatmap that refreshes itself daily.

Nothing here depends on a third-party badge service for the art. The SVGs are
committed to the repo, so they load instantly and cannot rate-limit or go down.

---

## 1. Fill in `profile.json`

Everything specific to you lives in this one file:

| field | what it does |
| --- | --- |
| `username` | your exact GitHub username, which drives the contribution scrape |
| `display_name` | shown after `whoami` in the portrait's status bar |
| `shell_user` | the `you@github` part of every terminal title bar |
| `wordmark_text` | the 3D ASCII word. 1 to 3 characters works best |
| `role_line` | the one-line tagline under the heatmap |
| `links` | shields.io badges: label, value, url, hex color, [simple-icons](https://simpleicons.org) slug |

## 2. Install

```bash
pip install -r scripts/requirements.txt
```

Only needed if you want to regenerate the ASCII portrait from a photo:

```bash
pip install -r scripts/requirements-photo.txt
```

## 3. Build the art

```bash
python scripts/prep_photo.py source-photo.jpg
python scripts/make_ascii_svg.py
python scripts/make_wordmark_svg.py --mode rock
python scripts/fetch_contributions.py
python scripts/render_heatmap_svg.py
python scripts/build_readme.py
```

Or all at once:

```bash
python scripts/build_all.py
```

### Tuning the portrait

If the face comes out as a dark blob or a washed-out ghost, the three knobs at
the top of `scripts/make_ascii_svg.py` are what to reach for:

- `GAMMA` (default `1.18`): raise it to brighten the midtones so the face lands
  in the sparser characters
- `WHITE_FLOOR` (default `0.80`): anything brighter than this becomes a blank
  space. Lower it if the background is bleeding into the portrait
- `CONTRAST` (default `1.05`): global contrast, applied after the local CLAHE pass

Preview a frozen (non-animating) version while you tune:

```bash
STATIC=1 python scripts/make_ascii_svg.py
```

A head-and-shoulders shot with a clear background works far better than a busy
full-body one. The grid is only 100 by 53 characters, so fine detail is lost.

### Wordmark modes

```bash
python scripts/make_wordmark_svg.py --mode rock    # oscillates 11 degrees, forever (default)
python scripts/make_wordmark_svg.py --mode once    # one full turn, then freezes
python scripts/make_wordmark_svg.py --mode spin    # continuous turntable
python scripts/make_wordmark_svg.py --mode static  # frozen, for eyeballing a render
python scripts/make_wordmark_svg.py --preview      # dump ASCII to the terminal
```

The font is auto-detected: Futura on macOS, Arial Bold on Windows, DejaVu Sans
Bold on Linux. Override with `WORDMARK_FONT=/path/to/font.ttf`. Avoid very heavy
faces like Impact or Arial Black, because at this grid resolution the letter
counters collapse into solid blobs.

Keep the wordmark short. More than about four letters and each one gets too few
grid columns to stay readable.

## 4. Publish

The repo name must be **exactly** your username. That is what makes GitHub show
its README on your profile page.

```bash
git init -b main
git add .
git commit -m "feat: terminal-style animated profile README"
git remote add origin https://github.com/<username>/<username>.git
git push -u origin main
```

Then go to the repo's **Settings > Actions > General > Workflow permissions** and
make sure **Read and write permissions** is selected, so the daily job can commit
the refreshed heatmap.

## 5. The daily refresh

`.github/workflows/update-profile-art.yml` runs at about 06:17 UTC daily, also on
every push to `main`, and on demand from the Actions tab. It re-scrapes your
contribution data, re-renders `contrib-heatmap.svg`, and commits the result with
`[skip ci]` so it does not retrigger itself.

The scrape hits `https://github.com/users/<username>/contributions`, which is
public HTML. No token, no API quota.

---

## Why it is built this way

**Self-hosted SVGs, not third-party services.** Services like github-readme-stats
rate-limit, go down, and put your profile's appearance on someone else's uptime.
Committed SVGs load from your own repo.

**Animation lives inside the SVG.** GitHub strips `<script>` and sanitizes inline
CSS in READMEs, but it does render SVGs in `<img>` and runs their SMIL and CSS
keyframe animations. That is the entire trick.

**Markdown gotchas this layout works around:**

- `<h1>` and `<h2>` get an underline rule from GitHub's stylesheet, so use `<h3>`
- vertical spacing needs literal `<br>` tags, because blank lines collapse
- the hero is a `<table>` because it is the only reliable side-by-side layout
- 370 plus 490 equals 860, which is why the heatmap lines up under both columns
