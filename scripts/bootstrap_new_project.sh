#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_REPO=${1:-"$(pwd)"}
TARGET_REPO_URL=${2:-"git@github.com:alevic/novo-projeto.git"}
TARGET_DIR=${3:-"../novo-projeto"}

if [[ -z "$TARGET_REPO_URL" ]]; then
  echo "Uso: scripts/bootstrap_new_project.sh /caminho/do/template git@github.com:alevic/novo-projeto.git"
  exit 1
fi

WORK_DIR=$(mktemp -d)
echo "Clonando template em modo bare para $WORK_DIR"
git clone --bare "$TEMPLATE_REPO" "$WORK_DIR/template.git"

pushd "$WORK_DIR/template.git" >/dev/null
echo "Publicando mirror em $TARGET_REPO_URL"
git push --mirror "$TARGET_REPO_URL"
popd >/dev/null

echo "Clonando novo repositório em $TARGET_DIR"
rm -rf "$TARGET_DIR"
git clone "$TARGET_REPO_URL" "$TARGET_DIR"

echo "Limpando histórico local temporário"
rm -rf "$WORK_DIR/template.git"

cat <<'EOF'

Novo repositório criado em "$TARGET_DIR".
Passos sugeridos:
1. cd "$TARGET_DIR"
2. Ajuste README, .env.example, migrations e configs específicas
3. Faça git push para começar o desenvolvimento do novo projeto.

EOF
