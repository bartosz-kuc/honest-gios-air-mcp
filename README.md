# gios-air-mcp

Local MCP server for the **GIOŚ (Główny Inspektorat Ochrony Środowiska) air-quality public API** — the official Polish state environmental monitoring feed for PM2.5, PM10, NO2, SO2, O3, CO, C6H6, and the composite air-quality index.

Part of the [honest-mcp family](https://github.com/bartosz-kuc?tab=repositories) of small, auditable, local-first MCP servers.

## Why

If you live in a Polish city — especially over winter — the difference between "moderate" and "very poor" air-quality index matters (indoor training vs opening the window). GIOŚ has ~200 stations and a public API but only in Polish JSON-LD. This server translates it to English keys and hands it to your AI so you can ask "how's the air in Kraków this afternoon?"

## Features

Four tools:

- `list_stations` — search the ~200-station network by city or voivodeship
- `get_station_sensors` — list the sensors installed at a station
- `get_sensor_readings` — recent measurements (~24h) from one sensor
- `get_air_index` — composite index for a station (very good / good / moderate / poor / very poor / hazardous) with the critical pollutant identified

## Data source

- Endpoint: [api.gios.gov.pl/pjp-api/v1](https://api.gios.gov.pl/pjp-api/v1/) — GIOŚ public JSON-LD API
- No API key
- Refresh: hourly per sensor

## Requirements

- Python 3.10+

## Setup

```bash
git clone https://github.com/bartosz-kuc/gios-air-mcp.git
cd gios-air-mcp
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

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

Two-step: `list_stations(city="Kraków", limit=5)` → pick a station ID → `get_air_index(station_id=...)` → text category and the critical pollutant.

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
