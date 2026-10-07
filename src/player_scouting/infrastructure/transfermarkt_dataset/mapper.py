from __future__ import annotations

from datetime import date, datetime

from player_scouting.application.ports import DatasetProfile
from player_scouting.domain.competitions import CompetitionKind
from player_scouting.domain.market_value import MarketValuePoint

# Dataset position -> the vocabulary the rest of the app uses.
POSITIONS = {
    "Attack": "Forward",
    "Midfield": "Midfielder",
    "Defender": "Defender",
    "Goalkeeper": "Goalkeeper",
}
DEFAULT_PHOTO = "/portrait/header/default.jpg"

# Domestic leagues outside the big five (those come from FBref), verified in
# competitions.csv (Sept 2026).
OTHER_LEAGUES = {
    "A1": "Austrian Bundesliga",
    "ARG1": "Liga Profesional Argentina",
    "AUS1": "A-League",
    "BE1": "Jupiler Pro League",
    "BRA1": "Brasileirão",
    "C1": "Swiss Super League",
    "DK1": "Danish Superliga",
    "GR1": "Greek Super League",
    "JAP1": "J1 League",
    "KR1": "Croatian HNL",
    "MEX1": "Liga MX",
    "MLS1": "MLS",
    "NL1": "Eredivisie",
    "NO1": "Eliteserien",
    "PL1": "Ekstraklasa",
    "PO1": "Liga Portugal",
    "RO1": "Romanian Superliga",
    "RSK1": "K League 1",
    "RU1": "Russian Premier League",
    "SA1": "Saudi Pro League",
    "SC1": "Scottish Premiership",
    "SE1": "Allsvenskan",
    "SER1": "Serbian SuperLiga",
    "TR1": "Süper Lig",
    "TS1": "Czech First League",
    "UKR1": "Ukrainian Premier League",
}


def _optional_int(value: str) -> int | None:
    return int(float(value)) if value else None


def _date(value: str) -> date | None:
    return datetime.strptime(value[:10], "%Y-%m-%d").date() if value else None


def to_valuation(row: dict[str, str]) -> MarketValuePoint | None:
    parsed = _date(row["date"])
    amount = _optional_int(row["market_value_in_eur"])
    if parsed is None or amount is None:
        return None
    return MarketValuePoint(parsed, amount, row.get("current_club_name") or "")


def to_profile(
    row: dict[str, str], valuations: tuple[MarketValuePoint, ...]
) -> DatasetProfile | None:
    position = POSITIONS.get(row["position"])
    if position is None:
        return None
    photo = row.get("image_url") or None
    return DatasetProfile(
        transfermarkt_id=int(row["player_id"]),
        name=row["name"],
        date_of_birth=_date(row["date_of_birth"]),
        position=position,
        detailed_position=row.get("sub_position") or None,
        foot=row.get("foot") or None,
        height_cm=_optional_int(row.get("height_in_cm", "")),
        photo_url=None if photo is None or DEFAULT_PHOTO in photo else photo,
        club=row.get("current_club_name") or None,
        valuations=valuations,
    )


# Competitions shown on a player's page, by dataset code (competitions.csv, Oct 2026).
# Calendar-year leagues are left out, as everywhere else in the app.
_LEAGUES = {
    "GB1": "Premier League",
    "ES1": "La Liga",
    "L1": "Bundesliga",
    "IT1": "Serie A",
    "FR1": "Ligue 1",
    **{
        code: name
        for code, name in OTHER_LEAGUES.items()
        if code not in {"ARG1", "BRA1", "JAP1", "MLS1", "NO1", "RSK1", "SE1"}
    },
}
DATASET_COMPETITIONS: dict[str, tuple[str, CompetitionKind]] = {
    **{code: (name, "league") for code, name in _LEAGUES.items()},
    "CL": ("Champions League", "continental"),
    "CLQ": ("Champions League (previa)", "continental"),
    "EL": ("Europa League", "continental"),
    "ELQ": ("Europa League (previa)", "continental"),
    "UCOL": ("Conference League", "continental"),
    "ECLQ": ("Conference League (previa)", "continental"),
    "CDR": ("Copa del Rey", "cup"),
    "FAC": ("FA Cup", "cup"),
    "DFB": ("DFB-Pokal", "cup"),
    "CIT": ("Coppa Italia", "cup"),
    "NLP": ("KNVB Beker", "cup"),
    "SFA": ("Scottish Cup", "cup"),
    "DKP": ("Copa de Dinamarca", "cup"),
    "GRP": ("Copa de Grecia", "cup"),
    "RUP": ("Copa de Rusia", "cup"),
    "UKRP": ("Copa de Ucrania", "cup"),
    "USC": ("Supercopa de Europa", "supercup"),
    "SUC": ("Supercopa de España", "supercup"),
    "GBCS": ("Community Shield", "supercup"),
    "DFL": ("Supercopa de Alemania", "supercup"),
    "SCI": ("Supercopa de Italia", "supercup"),
    "FRCH": ("Trophée des Champions", "supercup"),
    "NLSC": ("Johan Cruijff Schaal", "supercup"),
    "POSU": ("Supercopa de Portugal", "supercup"),
    "BESC": ("Supercopa de Bélgica", "supercup"),
    "RUSS": ("Supercopa de Rusia", "supercup"),
    "FIWC": ("Mundial", "national"),
    "EURO": ("Eurocopa", "national"),
    "COPA": ("Copa América", "national"),
    "AFCN": ("Copa África", "national"),
    "AFAC": ("Copa Asia", "national"),
}
