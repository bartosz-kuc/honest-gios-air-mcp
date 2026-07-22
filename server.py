"""gios-air-mcp — MCP server for GIOŚ air quality public API (v1).

Wraps https://api.gios.gov.pl/pjp-api/v1/ — the Polish Chief Inspectorate
for Environmental Protection's public API for the State Environmental
Monitoring air-quality network (Państwowy Monitoring Środowiska / Jakość
Powietrza). No auth.

The upstream API responds in JSON-LD with Polish key names; this server
normalizes to English for LLM consumption.

Tools: list_stations, get_station_sensors, get_sensor_readings, get_air_index.

Author: Bartosz Kuć <firma@bartosza.pl>
Repo:   https://github.com/bartosz-kuc/gios-air-mcp
License: MIT
"""

import asyncio
import json
from typing import Any

import requests

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

GIOS_BASE = "https://api.gios.gov.pl/pjp-api/v1/rest"

# Polish → English key normalization for common fields
STATION_KEYS = {
    "Identyfikator stacji": "station_id",
    "Kod stacji": "station_code",
    "Nazwa stacji": "station_name",
    "WGS84 φ N": "latitude",
    "WGS84 λ E": "longitude",
    "Identyfikator miasta": "city_id",
    "Nazwa miasta": "city",
    "Gmina": "commune",
    "Powiat": "county",
    "Województwo": "voivodeship",
    "Ulica": "street",
}
SENSOR_KEYS = {
    "Identyfikator stanowiska": "sensor_id",
    "Identyfikator stacji": "station_id",
    "Wskaźnik": "indicator_name",
    "Wskaźnik - kod": "indicator_code",
    "Wskaźnik - id": "indicator_id",
    "Wskaźnik - wzór": "indicator_formula",
}
READING_KEYS = {
    "Kod stanowiska": "sensor_code",
    "Data": "measured_at",
    "Wartość": "value",
}
INDEX_KEYS = {
    "Identyfikator stacji pomiarowej": "station_id",
    "Data wykonania obliczeń indeksu": "index_calculated_at",
    "Data źródłowych danych pomiarowych": "index_source_data_at",
    "Nazwa kategorii indeksu": "index_category",
    "Kod zanieczyszczenia krytycznego": "critical_pollutant_code",
}


def _translate(item: dict, mapping: dict[str, str]) -> dict:
    out = {}
    for k, v in item.items():
        if k.startswith("@"):
            continue
        out[mapping.get(k, k)] = v
    return out


def _get(path: str, params: dict | None = None) -> dict:
    resp = requests.get(f"{GIOS_BASE}/{path}", params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


server = Server("gios-air")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_stations",
            description=(
                "List GIOŚ air-quality monitoring stations. Optional filters: city, voivodeship — both case-insensitive "
                "substring match. The full network is ~200 stations; use filters or `limit` to keep responses small."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Filter by city (substring)"},
                    "voivodeship": {"type": "string", "description": "Filter by voivodeship (substring)"},
                    "limit": {"type": "integer", "default": 25, "description": "Max results (default 25)"},
                },
            },
        ),
        Tool(
            name="get_station_sensors",
            description="List the sensors installed at a station (each sensor measures one pollutant/indicator such as PM10, PM2.5, NO2, SO2, O3, C6H6).",
            inputSchema={
                "type": "object",
                "properties": {"station_id": {"type": "integer", "description": "Numeric station ID from list_stations"}},
                "required": ["station_id"],
            },
        ),
        Tool(
            name="get_sensor_readings",
            description="Get recent measurement readings from a sensor. Each reading is a (measured_at, value) pair. Returns latest ~24 hours.",
            inputSchema={
                "type": "object",
                "properties": {"sensor_id": {"type": "integer", "description": "Numeric sensor ID from get_station_sensors"}},
                "required": ["sensor_id"],
            },
        ),
        Tool(
            name="get_air_index",
            description="Get the composite air-quality index for a station (aggregates all pollutants into a single category: very good / good / moderate / poor / very poor / hazardous).",
            inputSchema={
                "type": "object",
                "properties": {"station_id": {"type": "integer", "description": "Numeric station ID"}},
                "required": ["station_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "list_stations":
        city_sub = (arguments.get("city") or "").strip().lower()
        voiv_sub = (arguments.get("voivodeship") or "").strip().lower()
        limit = int(arguments.get("limit", 25))

        collected: list[dict] = []
        page = 0
        # Fetch pages until we've filled the limit or exhausted the source
        while len(collected) < limit and page < 200:
            data = _get("station/findAll", {"page": page, "size": 50})
            stations_raw = data.get("Lista stacji pomiarowych", [])
            if not stations_raw:
                break
            for s in stations_raw:
                translated = _translate(s, STATION_KEYS)
                if city_sub and city_sub not in (translated.get("city") or "").lower():
                    continue
                if voiv_sub and voiv_sub not in (translated.get("voivodeship") or "").lower():
                    continue
                collected.append(translated)
                if len(collected) >= limit:
                    break
            total_pages = data.get("totalPages", 1)
            page += 1
            if page >= total_pages:
                break

        return [TextContent(type="text", text=json.dumps({"count": len(collected), "stations": collected}, ensure_ascii=False, indent=2))]

    if name == "get_station_sensors":
        station_id = int(arguments["station_id"])
        data = _get(f"station/sensors/{station_id}")
        sensors_raw = data.get("Lista stanowisk pomiarowych dla podanej stacji", [])
        sensors = [_translate(s, SENSOR_KEYS) for s in sensors_raw]
        return [TextContent(type="text", text=json.dumps({"count": len(sensors), "sensors": sensors}, ensure_ascii=False, indent=2))]

    if name == "get_sensor_readings":
        sensor_id = int(arguments["sensor_id"])
        data = _get(f"data/getData/{sensor_id}")
        readings_raw = data.get("Lista danych pomiarowych", [])
        readings = [_translate(r, READING_KEYS) for r in readings_raw]
        return [TextContent(type="text", text=json.dumps({"count": len(readings), "readings": readings}, ensure_ascii=False, indent=2))]

    if name == "get_air_index":
        station_id = int(arguments["station_id"])
        data = _get(f"aqindex/getIndex/{station_id}")
        # Response wraps the payload in an "AqIndex" object; unwrap and translate keys.
        payload = data.get("AqIndex", data) if isinstance(data, dict) else data
        if isinstance(payload, dict):
            translated = {}
            for k, v in payload.items():
                if k.startswith("@"):
                    continue
                # Map full Polish key → English; unknown keys pass through
                translated[INDEX_KEYS.get(k, k)] = v
            payload = translated
        return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
