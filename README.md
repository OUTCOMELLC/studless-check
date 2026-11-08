# Studless Check Japan

Do you need studless (winter) tires on your Japan rental car? Enter a pickup postal code or city name, an optional destination and your dates. The page checks the season for that area plus the live 16-day forecast and shows a red, amber or green verdict, with a map of snow risk across Hokkaido, Honshu, Shikoku and Kyushu.

No server, no build step, no API keys. It runs entirely in the browser on GitHub Pages.

## Publish on GitHub Pages
1. Create a public repository (for example `studless-check`).
2. Upload `index.html`, `stores.json`, `.nojekyll` and this README to the root.
3. In the repository settings, turn on Pages and serve from the `main` branch, root folder.
4. The site appears at `https://<your-account>.github.io/studless-check/` within a minute or two.

## How the verdict works
- **Season:** each area is classed as snow country, mountain, occasional snow or low snow, using about 80 reference points (prefecture capitals plus ski areas and mountain passes). Places above 600 m are treated as mountain at minimum.
- **Forecast (Open-Meteo):** any day with snowfall, or a low at or below 1 °C with rain or snow, is red. A low at or below 0 °C is amber.
- The trip gets the worst result across pickup, destination and every day.

## Adding rental stores
`stores.json` starts empty. Add stores in this shape and they appear on the map with a "Use as pickup" button:

```json
[
  {"name": "Example Store", "address": "...", "postal": "060-0806",
   "lat": 43.068, "lon": 141.350, "studless": "standard in winter"}
]
```

Fill it from the rental company's published store list (check their terms first) or from a data feed they provide.

## Data sources
- Weather: Open-Meteo (free for non-commercial use; a commercial plan is needed if this is sold or used commercially)
- Postal codes: zipcloud
- Place-name search: Open-Meteo geocoding, then GSI address search (Japanese names)
- Map tiles and address geocoding: Geospatial Information Authority of Japan (国土地理院)

Advice only, not a guarantee. Outcome LLC · outcometn.com
