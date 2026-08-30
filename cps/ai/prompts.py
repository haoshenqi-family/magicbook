"""AI 提示词模板：本地默认 + {{var}} 渲染。

与 moon-well 的 nacos-prompt-registry 设计对齐（{{var}} 语法、单一模板 +
预计算变量）。Nacos Prompt Registry 稍后接入：``get_prompt()`` 届时优先
读注册表在线版本，miss 时回退本地默认，调用方零改动。
"""
import re

CHAT_SYSTEM = "chat-system"

DEFAULT_PROMPTS = {
    CHAT_SYSTEM: (
        "You are an AI reading companion helping the user understand a book they are currently reading.\n"
        "Answer questions, explain passages, and discuss themes based on the book's metadata, "
        "the current chapter, and the current page text provided below.\n"
        "Be concise and helpful. If the user's question is unrelated to the book, gently redirect.\n"
        "\n"
        "## Book Metadata\n"
        "Title: {{title}}\n"
        "Author(s): {{authors}}{{tags_section}}{{description_section}}\n"
        "\n"
        "## Current Chapter\n"
        "{{chapter}}\n"
        "\n"
        "## Current Page Text\n"
        "{{page_context}}\n"
        "\n"
        "## Unfamiliar words on this page\n"
        "{{unfamiliar_words}}\n"
        "\n"
        "## What you remember about this user (long-term memory)\n"
        "{{memory}}{{extra_section}}"
    ),
}

_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def get_prompt(key: str) -> str:
    """获取模板；Nacos Registry 接入后此处优先读在线版本。未知 key 显式失败。"""
    try:
        return DEFAULT_PROMPTS[key]
    except KeyError:
        raise KeyError("Unknown prompt template: %s" % key)


def render_prompt(key: str, **variables) -> str:
    """渲染模板：替换已提供的 {{var}}（None 按空串），未提供的占位符保留。"""
    rendered = get_prompt(key)
    for name, value in variables.items():
        rendered = rendered.replace("{{%s}}" % name, "" if value is None else str(value))
    return rendered


__all__ = ["CHAT_SYSTEM", "DEFAULT_PROMPTS", "get_prompt", "render_prompt"]
