from __future__ import annotations

from pathlib import Path

from deployment_manager.ai_agent.config import AgentConfig


class SkillLoader:
    def __init__(self, config: AgentConfig):
        self._config = config

    def load_instructions(self) -> str:
        if not self._config.agent_path:
            return ""
        try:
            return self._config.agent_path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            return ""

    def load_skills_text(self) -> str:
        skill_paths = [self._config.skills_path, *self._config.extra_skills_paths]
        skill_files: list[Path] = []
        for skill_path in skill_paths:
            if not skill_path.exists():
                continue
            skill_files.extend(sorted(skill_path.glob("*.md")))
        if not skill_files:
            return ""
        content = []
        for skill_file in skill_files:
            try:
                skill_text = skill_file.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                continue
            if skill_text:
                content.append(f"\n# Skill: {skill_file.name}\n{skill_text}")
        return "\n".join(content).strip()

    def count_base_skills(self) -> int:
        return self._count_skills(self._config.skills_path)

    def count_extra_skills(self) -> int:
        return sum(self._count_skills(path) for path in self._config.extra_skills_paths)

    def load_skill_file(self, skill_name: str) -> str:
        skill_paths = [*self._config.extra_skills_paths, self._config.skills_path]
        for skill_path in skill_paths:
            if not skill_path.exists():
                continue
            skill_file = skill_path / skill_name
            if not skill_file.exists():
                continue
            try:
                skill_text = skill_file.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                continue
            if skill_text:
                return f"\n# Skill: {skill_file.name}\n{skill_text}"
        return ""

    @staticmethod
    def _count_skills(skill_path: Path) -> int:
        if not skill_path.exists():
            return 0
        return len([path for path in skill_path.glob("*.md") if path.is_file()])
