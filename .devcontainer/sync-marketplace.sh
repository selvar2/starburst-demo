#!/usr/bin/env bash
# sync-marketplace.sh — syncs Claude marketplace plugin assets into .claude/
# Idempotent: safe to run on every container start, restart, or rebuild.
# Uses relative symlinks so they work on any clone path.
# Installs: agents → .claude/agents/, commands → .claude/commands/, skills → .claude/skills/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE="$REPO_ROOT/claude-marketplace/plugins"
CLAUDE_DIR="$REPO_ROOT/.claude"

AGENTS_DST="$CLAUDE_DIR/agents"
COMMANDS_DST="$CLAUDE_DIR/commands"
SKILLS_DST="$CLAUDE_DIR/skills"

echo "[MARKETPLACE] Syncing Claude marketplace plugins..."
echo "  Source: $MARKETPLACE"
echo "  Target: $CLAUDE_DIR"

mkdir -p "$AGENTS_DST" "$COMMANDS_DST" "$SKILLS_DST"

installed=0
skipped=0
errors=0

# Compute relative symlink path from $dst_dir to $src
rel_path() {
    local src="$1" dst_dir="$2"
    realpath --relative-to="$dst_dir" "$src"
}

# ── Agents ──────────────────────────────────────
while IFS= read -r -d '' src; do
    name="$(basename "$src")"
    dst="$AGENTS_DST/$name"
    rel="$(rel_path "$src" "$AGENTS_DST")"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$rel" ]; then
        skipped=$((skipped + 1))
    else
        ln -sf "$rel" "$dst" && echo "  [agent]   $name" && installed=$((installed + 1)) || errors=$((errors + 1))
    fi
done < <(find "$MARKETPLACE" -path "*/agents/*.md" -print0 2>/dev/null)

# ── Commands ────────────────────────────────────
while IFS= read -r -d '' src; do
    name="$(basename "$src")"
    dst="$COMMANDS_DST/$name"
    rel="$(rel_path "$src" "$COMMANDS_DST")"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$rel" ]; then
        skipped=$((skipped + 1))
    else
        ln -sf "$rel" "$dst" && echo "  [command] $name" && installed=$((installed + 1)) || errors=$((errors + 1))
    fi
done < <(find "$MARKETPLACE" -path "*/commands/*.md" -print0 2>/dev/null)

# ── Skills ──────────────────────────────────────
while IFS= read -r -d '' src; do
    skill_name="$(basename "$(dirname "$src")")"
    skill_dst_dir="$SKILLS_DST/$skill_name"
    mkdir -p "$skill_dst_dir"
    dst="$skill_dst_dir/SKILL.md"
    rel="$(rel_path "$src" "$skill_dst_dir")"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$rel" ]; then
        skipped=$((skipped + 1))
    else
        ln -sf "$rel" "$dst" && echo "  [skill]   $skill_name/SKILL.md" && installed=$((installed + 1)) || errors=$((errors + 1))
    fi
done < <(find "$MARKETPLACE" -path "*/skills/*/SKILL.md" -print0 2>/dev/null)

# ── Summary ─────────────────────────────────────
echo "[MARKETPLACE] Done — installed=$installed skipped=$skipped errors=$errors"
[ "$errors" -gt 0 ] && echo "[MARKETPLACE][WARN] $errors asset(s) failed to install."

# ── Validation ──────────────────────────────────
echo "[MARKETPLACE] Validating installed assets..."
agent_count=$(find "$AGENTS_DST" -name "*.md" | wc -l)
command_count=$(find "$COMMANDS_DST" -name "*.md" | wc -l)
skill_count=$(find "$SKILLS_DST" -name "SKILL.md" | wc -l)
echo "  agents:   $agent_count"
echo "  commands: $command_count"
echo "  skills:   $skill_count"

if [ "$agent_count" -eq 0 ] && [ "$command_count" -eq 0 ] && [ "$skill_count" -eq 0 ]; then
    echo "[MARKETPLACE][WARN] No assets found in $MARKETPLACE — check plugin folder structure."
else
    echo "[MARKETPLACE] All assets available in .claude/"
fi
