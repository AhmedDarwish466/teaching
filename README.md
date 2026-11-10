# Teaching website — Dr. Ahmed Darwish

Static site listing every course, with links to lecture slides, problem sheets and projects in Google Drive.

- Content: `data/courses.json`
- Build: `python3 build.py` writes `site/` (styles from `src/style.css`)
- Publishing: every push to `main` rebuilds the site and deploys it to GitHub Pages (`.github/workflows/pages.yml`).

Live site: https://ahmeddarwish466.github.io/teaching/
