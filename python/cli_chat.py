"""
Interactive Command Line Chat Application (CLI).
Demonstrates real-time multi-turn chat, system persona tuning,
context sliding window, token counting, and API cost tracking.
"""

import sys
from .config import load_config
from .conversation_manager import ConversationManager
from .cost_manager import CostManager
from .client import UnifiedLLMClient
from .structured_outputs import StructuredOutputParser, CodeReviewSchema


def print_banner():
    print("=" * 70)
    print("      🚀 AI CHAT APPLICATION - INTERACTIVE TERMINAL STUDIO 🚀      ")
    print("           Module 3: LLM APIs & Application Development            ")
    print("=" * 70)
    print("Commands:")
    print("  /persona <text>     - Update custom system instruction / persona")
    print("  /model <name>       - Switch model (gpt-4o-mini, gemini-1.5-flash, mock-llm)")
    print("  /params <temp> <max>- Set temperature (0-2) and max_tokens")
    print("  /cost               - View cumulative token usage and cost audit")
    print("  /structured         - Run a demonstration structured JSON extraction")
    print("  /clear              - Clear conversation history")
    print("  /help               - Show this command reference")
    print("  /exit or /quit      - Terminate interactive session")
    print("=" * 70)


def main():
    config = load_config()
    cost_manager = CostManager(budget_usd=config.session_budget_usd)
    client = UnifiedLLMClient(config=config, cost_manager=cost_manager)
    conv_manager = ConversationManager(
        system_instruction="You are an expert AI development assistant with deep knowledge of LLM APIs.",
        max_context_tokens=config.max_context_tokens,
        temperature=config.default_temperature,
        max_tokens=config.default_max_tokens,
        top_p=config.default_top_p,
    )

    current_model = config.default_model

    print_banner()
    print(f"[*] Provider: {config.get_active_provider().upper()} | Active Model: {current_model}")
    print(f"[*] System Prompt: \"{conv_manager.system_message.content}\"")
    print(f"[*] Session Budget: ${cost_manager.budget_usd:.2f}\n")

    while True:
        try:
            user_input = input("User ❯ ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("/exit", "/quit"):
                print("\n[+] Exiting session. Here is your final usage summary:")
                report = cost_manager.get_summary_report()
                for k, v in report.items():
                    print(f"    - {k}: {v}")
                print("Goodbye!")
                break

            if user_input.lower() == "/help":
                print_banner()
                continue

            if user_input.lower() == "/clear":
                conv_manager.clear_history()
                print("[✔] Conversation history cleared. System prompt preserved.\n")
                continue

            if user_input.lower() == "/cost":
                report = cost_manager.get_summary_report()
                print("\n--- 📊 Token & Cost Audit ---")
                for k, v in report.items():
                    print(f"  {k}: {v}")
                print("----------------------------\n")
                continue

            if user_input.lower().startswith("/persona "):
                new_persona = user_input[9:].strip()
                conv_manager.set_system_instruction(new_persona)
                print(f"[✔] Updated System Persona: \"{new_persona}\"\n")
                continue

            if user_input.lower().startswith("/model "):
                current_model = user_input[7:].strip()
                print(f"[✔] Switched active model to: {current_model}\n")
                continue

            if user_input.lower().startswith("/params "):
                parts = user_input.split()
                if len(parts) >= 2:
                    temp = float(parts[1])
                    max_tok = int(parts[2]) if len(parts) >= 3 else conv_manager.max_tokens
                    conv_manager.update_parameters(temperature=temp, max_tokens=max_tok)
                    print(f"[✔] Parameters updated: Temp={conv_manager.temperature}, MaxTokens={conv_manager.max_tokens}\n")
                continue

            if user_input.lower() == "/structured":
                print("\n[*] Running Structured Output Demonstration (Code Review Schema)...")
                sample_prompt = [
                    {"role": "system", "content": StructuredOutputParser.get_system_prompt_for_schema(CodeReviewSchema)},
                    {"role": "user", "content": "Review this Python code: def calc(x): return x*2"},
                ]
                resp = client.call_api(sample_prompt, model=current_model)
                print(f"\nAssistant (Structured JSON):\n{resp.content}\n")
                try:
                    validated = StructuredOutputParser.validate_schema(resp.content, CodeReviewSchema)
                    print(f"[✔] Pydantic Validation Passed! Score: {validated.quality_score}/100, Language: {validated.language}\n")
                except Exception as ex:
                    print(f"[!] Validation warning: {ex}\n")
                continue

            # Standard chat interaction
            conv_manager.add_user_message(user_input)
            api_messages = conv_manager.get_messages_for_api()

            print("AI Thinking...", end="\r", flush=True)
            response = client.call_api(
                messages=api_messages,
                model=current_model,
                temperature=conv_manager.temperature,
                max_tokens=conv_manager.max_tokens,
                top_p=conv_manager.top_p,
            )

            conv_manager.add_assistant_message(response.content)

            print(" " * 20, end="\r")  # Clear "AI Thinking..."
            print(f"Assistant ❯\n{response.content}\n")
            print(
                f"[Tokens: {response.total_tokens} (Prompt: {response.prompt_tokens}, Comp: {response.completion_tokens}) | "
                f"Cost: ${response.cost_usd:.6f} | Latency: {response.latency_ms:.0f}ms | "
                f"History Context: {conv_manager.estimate_total_tokens()} tokens]\n"
            )

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted.")
            break
        except Exception as ex:
            print(f"\n[Error] {ex}\n")


if __name__ == "__main__":
    main()
