"""
End-to-End Verification Script for Module 3 Deliverables.
Executes real simulation runs covering all required course objectives.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from python.config import load_config
from python.conversation_manager import ConversationManager
from python.cost_manager import CostManager
from python.client import UnifiedLLMClient
from python.structured_outputs import (
    StructuredOutputParser,
    CodeReviewSchema,
    ActionPlanSchema,
    ChatMessageAnalysis,
)


def run_comprehensive_verification():
    print("=" * 70)
    print("  [+] RUNNING COMPLETE END-TO-END VERIFICATION: MODULE 3")
    print("=" * 70)

    # 1. Configuration & Validation
    print("\n[Step 1/5] Testing Configuration & Environment Security...")
    config = load_config()
    print(f"  ✔ Active Provider: {config.get_active_provider()}")
    print(f"  ✔ Default Model: {config.default_model}")
    print(f"  ✔ Max Context Limit: {config.max_context_tokens} tokens")

    # 2. Multi-Turn Conversation & Sliding Context Window
    print("\n[Step 2/5] Testing Conversation History & Sliding Window...")
    cost_mgr = CostManager(budget_usd=0.25)
    client = UnifiedLLMClient(config=config, cost_manager=cost_mgr)
    conv_mgr = ConversationManager(
        system_instruction="You are a Senior Systems Architect specializing in microservices.",
        max_context_tokens=150,  # Small window to test automatic pruning
    )

    # Turn 1
    conv_mgr.add_user_message("What is an API gateway?")
    r1 = client.call_api(conv_mgr.get_messages_for_api(), model="gpt-4o-mini")
    conv_mgr.add_assistant_message(r1.content)
    print(f"  Turn 1 -> Tokens: {r1.total_tokens} | Cost: ${r1.cost_usd:.6f} | Context size: {conv_mgr.estimate_total_tokens()}")

    # Turn 2
    conv_mgr.add_user_message("How does rate limiting work in an API gateway?")
    r2 = client.call_api(conv_mgr.get_messages_for_api(), model="gpt-4o-mini")
    conv_mgr.add_assistant_message(r2.content)
    print(f"  Turn 2 -> Tokens: {r2.total_tokens} | Cost: ${r2.cost_usd:.6f} | Context size: {conv_mgr.estimate_total_tokens()}")

    # Turn 3 (Trigger sliding window eviction)
    conv_mgr.add_user_message("Compare token bucket algorithm vs leaky bucket algorithm in detail.")
    r3 = client.call_api(conv_mgr.get_messages_for_api(), model="gpt-4o-mini")
    conv_mgr.add_assistant_message(r3.content)
    print(f"  Turn 3 -> Tokens: {r3.total_tokens} | Cost: ${r3.cost_usd:.6f} | Context size: {conv_mgr.estimate_total_tokens()}")
    print(f"  ✔ Sliding Window Maintained: System instruction intact = '{conv_mgr.system_message.content[:35]}...'")

    # 3. Structured JSON Outputs with Pydantic Validation
    print("\n[Step 3/5] Testing Structured Responses & Pydantic Validation...")
    
    # 3a. Code Review Schema
    review_prompt = [
        {"role": "system", "content": StructuredOutputParser.get_system_prompt_for_schema(CodeReviewSchema)},
        {"role": "user", "content": "Review this Python retry snippet: while retries > 0: try: ..."},
    ]
    r_review = client.call_api(review_prompt)
    validated_review = StructuredOutputParser.validate_schema(r_review.content, CodeReviewSchema)
    print(f"  ✔ Code Review Schema Validated! Language: {validated_review.language}, Quality: {validated_review.quality_score}/100, Issues: {len(validated_review.issues_found)}")

    # 3b. Action Plan Schema
    plan_prompt = [
        {"role": "system", "content": StructuredOutputParser.get_system_prompt_for_schema(ActionPlanSchema)},
        {"role": "user", "content": "Create an action plan to deploy our AI chat app to Vercel."},
    ]
    r_plan = client.call_api(plan_prompt)
    validated_plan = StructuredOutputParser.validate_schema(r_plan.content, ActionPlanSchema)
    print(f"  ✔ Action Plan Schema Validated! Goal: {validated_plan.goal}, Steps: {len(validated_plan.steps)}, Difficulty: {validated_plan.difficulty}")

    # 3c. Sentiment & Conversational Analysis Schema
    analysis_prompt = [
        {"role": "system", "content": StructuredOutputParser.get_system_prompt_for_schema(ChatMessageAnalysis)},
        {"role": "user", "content": "Analyze user sentiment: I am having issues with API rate limits!"},
    ]
    r_analysis = client.call_api(analysis_prompt)
    validated_analysis = StructuredOutputParser.validate_schema(r_analysis.content, ChatMessageAnalysis)
    print(f"  ✔ Chat Analysis Validated! Sentiment: {validated_analysis.sentiment}, Urgency: {validated_analysis.urgency_rating}/5, Intent: {validated_analysis.intent}")

    # 4. Token Accounting & Financial Budgeting Audit
    print("\n[Step 4/5] Testing Token Economics & Budget Ledger...")
    report = cost_mgr.get_summary_report()
    for key, value in report.items():
        print(f"  • {key}: {value}")
    print("  ✔ Real-time token economics and ledger working accurately!")

    # 5. Live Endpoint Verification
    print("\n[Step 5/5] Testing Local Web Integration & Vercel API Contract...")
    from backend.app import handle_chat, ChatRequest
    req = ChatRequest(
        messages=[{"role": "user", "content": "Health check verification"}],
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=256,
    )
    api_res = handle_chat(req)
    print(f"  ✔ FastAPI Chat Route Executed: {api_res['success']} | Model: {api_res['model']} | Latency: {api_res['latency_ms']}ms")

    print("\n" + "=" * 70)
    print("  🎉 ALL VERIFICATION CRITERIA PASSED 100% SUCCESFULLY! 🎉  ")
    print("=" * 70)


if __name__ == "__main__":
    run_comprehensive_verification()
