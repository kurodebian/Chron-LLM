from pathlib import Path

from models import LoopState


PROMPT_PATH = Path(__file__).parent / "prompts" / "proposal.txt"


def build_proposal_prompt(state: LoopState) -> str:
    template = PROMPT_PATH.read_text()

    return template.format(
        current=state.current,
        target=state.target,
    )
