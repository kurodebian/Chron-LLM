import json

from llm import LLMClient
from models import LoopState
from prompt_builder import build_proposal_prompt
from schema_validator import validate_proposal_schema
from controller import LoopController


def run_llm_step(controller: LoopController):
    state_before = controller.state

    prompt = build_proposal_prompt(state_before)

    llm = LLMClient()
    raw_output = llm.generate(prompt)

    proposal_data = json.loads(raw_output)

    validate_proposal_schema(proposal_data)

    result = controller.step(proposal_data)

    return raw_output, result
