from models import LoopState, Proposal


def commit_proposal(
    state: LoopState,
    proposal: Proposal,
) -> LoopState:
    if proposal.action != "increment":
        raise ValueError("cannot commit unsupported action")

    if proposal.amount <= 0:
        raise ValueError("cannot commit non-positive amount")

    return LoopState(
        current=state.current + proposal.amount,
        target=state.target,
        iteration=state.iteration + 1,
    )
