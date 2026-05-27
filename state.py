from collections import defaultdict
from typing import Dict, Set

# chat_id → {'country': uz_name, 'attempts': int, 'hint_data': dict, 'job': job|None, 'challenge': bool}
active_country_games: Dict[str, dict] = {}

# chat_id → {'country': uz_name, 'capital': str, 'job': job|None}
active_capital_games: Dict[str, dict] = {}

# chat_id → {'country': uz_name, 'attempts': int, 'hint_data': dict, 'job': job|None}
active_flag_games: Dict[str, dict] = {}

# chat_id → {'country': uz_name, 'attempts': int, 'hint_data': dict, 'job': job|None}
active_currency_games: Dict[str, dict] = {}

# chat_id → set of uz country names already used
used_capital_countries: Dict[str, Set[str]] = defaultdict(set)
used_country_countries: Dict[str, Set[str]] = defaultdict(set)


def _cancel_job(game: dict | None) -> None:
    if game:
        job = game.get('job')
        if job is not None:
            try:
                job.schedule_removal()
            except Exception:
                pass


def cancel_capital_job(chat_id: str) -> None:
    _cancel_job(active_capital_games.get(chat_id))


def cancel_country_job(chat_id: str) -> None:
    _cancel_job(active_country_games.get(chat_id))


def cancel_flag_job(chat_id: str) -> None:
    _cancel_job(active_flag_games.get(chat_id))


def cancel_currency_job(chat_id: str) -> None:
    _cancel_job(active_currency_games.get(chat_id))


def new_hint_data() -> dict:
    """Fresh hint-progress tracker for a new game."""
    return {'fetched': False, 'wiki_sentences': [], 'idx': 0}
