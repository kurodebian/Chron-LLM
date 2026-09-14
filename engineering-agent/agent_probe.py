from agent import EngineeringAgent


agent = EngineeringAgent(max_turns=20)

result = agent.run(
    """
Work only inside the sandbox directory.

Engineering objective:
Make the sandbox pytest suite pass.

Constraints:
- Do not modify files outside sandbox/.
- Preserve the existing test.
- Do not delete or weaken tests.
- Use repository evidence and test results.
- Determine the implementation changes autonomously.
- Run pytest after making changes.
- Do not claim success without an actual passing test result.

Stop only when the pytest suite passes.
"""
)

print("\n=== AGENT RESULT ===")
print("completed =", result.completed)
print("turns =", result.turns)
print("final_message =", repr(result.final_message))
