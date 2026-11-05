# -*- coding: utf-8 -*-
"""
Anthropic Claude API 연동 모듈 (Claude Sonnet 5.5 / Opus 5.5 / Fable 5.1)
사용자의 워크스페이스 API Key를 기반으로 작동합니다.
"""
import os
import sys
import json
import urllib.request
import urllib.error
import argparse

def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되어 있지 않습니다.")
    return key

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5")

def ask_claude(
    prompt: str,
    system_prompt: str = "",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8192,
    temperature: float = None,
    workspace_id: str = "wrkspc_018fnBEHEmqn8kGz1hgx2s36"
) -> str:
    """
    Claude API를 호출하여 응답 텍스트를 반환합니다.
    """
    api_key = get_api_key()
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    if workspace_id:
        headers["anthropic-workspace-id"] = workspace_id

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if system_prompt:
        payload["system"] = system_prompt

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data_bytes,
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            content_blocks = res_json.get("content", [])
            text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            ans = "".join(text_parts).strip()
            # If text is empty but thinking exists, or if truncated, check
            if not ans:
                for b in content_blocks:
                    if b.get("type") == "thinking":
                        # log or fallback
                        pass
            return ans
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Claude API HTTP Error {e.code}: {err_body}")
    except Exception as e:
        raise RuntimeError(f"Claude API Request Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Call Claude API")
    parser.add_argument("prompt", nargs="?", default="", help="Prompt text to send")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Model name (e.g. claude-sonnet-5-5, claude-opus-5-5)")
    parser.add_argument("--system", "-s", default="", help="System prompt")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from standard input")
    args = parser.parse_args()

    prompt_text = args.prompt
    if args.stdin or not prompt_text:
        prompt_text = sys.stdin.read().strip()

    if not prompt_text:
        print("Error: No prompt provided.")
        sys.exit(1)

    try:
        reply = ask_claude(prompt_text, system_prompt=args.system, model=args.model)
        print(reply)
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
