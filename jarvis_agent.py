import os
import json
import time
import logging
from pathlib import Path

try:
    import google.genai as genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


logging.basicConfig(level=logging.INFO, format="[JARVIS_AGENT] %(message)s")


class JarvisAgent:
    """Minimal reusable agent scaffold for the JARVIS workspace."""

    def __init__(self,
                 api_key: str = None,
                 model: str = "gemini-2.5-flash",
                 memory_file: str = "jarvis_memoire.json"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.memory_file = Path(memory_file)
        self.client = genai.Client(api_key=self.api_key) if genai else None
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logging.warning("Unable to load memory: %s", exc)
        return {}

    def _save_memory(self) -> None:
        try:
            self.memory_file.write_text(json.dumps(self.memory, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logging.warning("Unable to save memory: %s", exc)

    def remember(self, key: str, value: str) -> None:
        self.memory[key] = {
            "valeur": value,
            "timestamp": time.strftime("%d/%m/%Y %H:%M")
        }
        self._save_memory()

    def forget(self, key: str) -> bool:
        if key in self.memory:
            del self.memory[key]
            self._save_memory()
            return True
        return False

    def memory_context(self) -> str:
        if not self.memory:
            return ""
        lines = ["MEMOIRE PERSISTANTE :"]
        for key, data in self.memory.items():
            lines.append(f"  - {key} : {data['valeur']} (note le {data['timestamp']})")
        return "\n".join(lines)

    def system_prompt(self) -> str:
        base = (
            "Tu es JARVIS, assistant IA personnel de Tom.\n"
            "Reponses courtes, ton sarcastique mais respectueux.\n"
            "TU DOIS TOUJOURS APPELER L'UTILISATEUR TOM, SYSTEMATIQUEMENT DANS CHAQUE REPONSE.\n\n"
        )
        base += self.memory_context()
        base += (
            "\n\nTu es connecte a Home Assistant, la domotique de Tom. "
            "Quand Tom parle de lumieres, prises, chauffage, temperature, "
            "scenes ou alarme, tu DOIS generer une commande JSON. "
            "Pour CES demandes domotiques UNIQUEMENT, reponds avec le JSON."\n
        )
        return base

    def build_prompt(self, user_message: str) -> list:
        return [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": user_message}
        ]

    def generate_response(self, user_message: str) -> str:
        if not self.client or not types:
            raise RuntimeError("google.genai is not installed or failed to import.")

        prompt = self.build_prompt(user_message)
        response = self.client.responses.create(
            model=self.model,
            messages=prompt
        )
        if response and getattr(response, "output", None):
            text_parts = []
            for item in response.output:
                if getattr(item, "content", None):
                    for entry in item.content:
                        if entry.get("type") == "output_text":
                            text_parts.append(entry.get("text", ""))
            return "".join(text_parts).strip()
        return ""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the JARVIS agent scaffold.")
    parser.add_argument("message", nargs="+", help="User message for the agent.")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model to use.")
    parser.add_argument("--memory-file", default="jarvis_memoire.json", help="Memory file path.")
    args = parser.parse_args()

    agent = JarvisAgent(model=args.model, memory_file=args.memory_file)
    message = " ".join(args.message)
    print("System prompt:\n", agent.system_prompt())
    print("\nUser message:\n", message)

    try:
        response = agent.generate_response(message)
        print("\nAgent response:\n", response)
    except Exception as exc:
        logging.error("Cannot generate response: %s", exc)


if __name__ == "__main__":
    main()
