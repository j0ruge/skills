# Configuração da loja iniciada com sdd install. Mantenha apenas atribuições.
PROJECT_NAME="chewiesoft-marketplace"
DEFAULT_BRANCH="main"
OUTPUT_LANG="pt-BR"
HANDOFF_DIR="docs/handoffs"
TODO_FILE="TODO.md"
JIRA_ENABLED=false

# A suíte da loja não descobre os testes de atribuição da retrofit-watch.
# O sandbox não permite o Bubblewrap aninhado das três provas reais de distribuição.
TEST_CMD='python3 scripts/codex-adapters.py --check && python3 scripts/codex-marketplace.py --check && SKILLS_SKIP_NATIVE_DISTRIBUTION=1 python3 -m unittest discover -s tests -p "test_*.py" && python3 -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -p "test_retrofit_watch.py" && python3 scripts/validate-versions.py'

# O teto da missão vem do worker quando houver delegação. O canal de aviso é local.
ON_ESCALATION_CMD="${ON_ESCALATION_CMD:-}"
