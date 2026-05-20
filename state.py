from collections import defaultdict
from typing import Dict, Set

# chat_id → {'country': uz_name}
active_country_games: Dict[str, dict] = {}

# chat_id → {'country': uz_name, 'capital': str, 'job': job|None}
active_capital_games: Dict[str, dict] = {}

# chat_id → set of uz country names already used
used_capital_countries: Dict[str, Set[str]] = defaultdict(set)
used_country_countries: Dict[str, Set[str]] = defaultdict(set)


def cancel_capital_job(chat_id: str) -> None:
    game = active_capital_games.get(chat_id)
    if game:
        job = game.get('job')
        if job is not None:
            try:
                job.schedule_removal()
            except Exception:
                pass
