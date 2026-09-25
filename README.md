# honest-gios-air-mcp

Local MCP server for the **GIOŚ (Główny Inspektorat Ochrony Środowiska) air-quality public API** — the official Polish state environmental monitoring feed for PM2.5, PM10, NO2, SO2, O3, CO, C6H6, and the composite air-quality index.

Part of the [honest-mcp family](https://github.com/bartosz-kuc?tab=repositories) of small, auditable, local-first MCP servers.

## Why

If you live in a Polish city — especially over winter — the difference between "moderate" and "very poor" air-quality index matters (indoor training vs opening the window). GIOŚ runs close to 300 stations and a public API, but only in Polish JSON-LD. This server maps the main fields to English keys (see [Output keys](#output-keys)) and hands the data to your AI so you can ask "how's the air in Kraków this afternoon?"

## Features

Four tools:

- `list_stations` — search the station network by city or voivodeship
- `get_station_sensors` — list the sensors installed at a station
- `get_sensor_readings` — recent measurements (~24h) from one sensor
- `get_air_index` — composite index for a station (very good / good / moderate / poor / very poor / hazardous; category names are returned in Polish) with the critical pollutant code

## Output keys

Only some upstream Polish keys are mapped to English; the rest pass through unchanged, and values are never translated.

- `list_stations`, `get_sensor_readings` — all fields use English keys.
- `get_station_sensors` — English keys except the numeric indicator ID, which stays `Id wskaźnika`.
- `get_air_index` — only `station_id`, `index_calculated_at`, `index_category` and `critical_pollutant_code` are English; all other fields — overall index value, source-data timestamp, per-pollutant fields (e.g. `Wartość indeksu dla wskaźnika PM10`) and the status flag — keep their Polish keys.
- Text values stay in Polish, e.g. `index_category: "Bardzo dobry"` (very good) or `indicator_name: "tlenek węgla"` (carbon monoxide).

## Data source

- Endpoint: [api.gios.gov.pl/pjp-api/v1](https://api.gios.gov.pl/pjp-api/v1/) — GIOŚ public JSON-LD API
- No API key
- Refresh: hourly per sensor

## Requirements

- Python 3.10+

## Setup

```bash
git clone https://github.com/bartosz-kuc/honest-gios-air-mcp.git
cd honest-gios-air-mcp
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

On Windows use `venv\Scripts\pip` and `venv\Scripts\python.exe` instead of the `venv/bin/...` paths shown here and below.

Register with Claude Code:

```bash
claude mcp add gios-air /absolute/path/to/venv/bin/python /absolute/path/to/server.py
```

Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gios-air": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

## Example usage

> "How's the air in Kraków right now?"

Two-step: `list_stations(city="Kraków", limit=5)` → pick a station ID → `get_air_index(station_id=...)` → category name (in Polish) and the critical pollutant code.

> "PM2.5 readings for the last 24h from station 400."

`get_station_sensors(station_id=400)` → find the PM2.5 sensor ID → `get_sensor_readings(sensor_id=...)`.

## Data flow

```
Your AI client
     ↕  MCP stdio
This server (Python, on your machine)
     ↕  HTTPS
api.gios.gov.pl (GIOŚ)
```

No cloud middle. No telemetry.

## Author

**Bartosz Kuć** — Warsaw-based developer, JDG owner running [skanfirmy.pl](https://skanfirmy.pl).

- GitHub: https://github.com/bartosz-kuc

- Email: firma@bartosza.pl

## Consulting

Available for consulting on Polish tax and business integrations (KSeF, GUS/NFZ/GIOŚ APIs, mBank data), MCP server design, and AI-assisted tooling for JDGs and small teams. See **[skanfirmy.pl/uslugi](https://skanfirmy.pl/uslugi)** for productized packages (audit 3k PLN, setup 8-15k PLN, retainer 2-4k PLN/mo), or reach out via email.

## License

MIT — see [LICENSE](LICENSE).

## Related

- Part of the honest-mcp family — see the [family index](https://github.com/bartosz-kuc?tab=repositories).
