import unittest
from python.conversation_manager import ConversationManager, ChatMessage


class TestConversationManager(unittest.TestCase):
    def setUp(self):
        self.mgr = ConversationManager(
            system_instruction="You are a test assistant.",
            max_context_tokens=500,
            temperature=0.8,
            max_tokens=150,
        )

    def test_initial_state(self):
        self.assertIsNotNone(self.mgr.system_message)
        self.assertEqual(self.mgr.system_message.role, "system")
        self.assertEqual(len(self.mgr.history), 0)

    def test_message_flow(self):
        user_msg = self.mgr.add_user_message("What is an API?")
        asst_msg = self.mgr.add_assistant_message("An API is an Application Programming Interface.")

        self.assertEqual(len(self.mgr.history), 2)
        self.assertEqual(self.mgr.history[0].role, "user")
        self.assertEqual(self.mgr.history[1].role, "assistant")

        api_payload = self.mgr.get_messages_for_api()
        self.assertEqual(len(api_payload), 3)  # system + 2 turns
        self.assertEqual(api_payload[0]["role"], "system")
        self.assertEqual(api_payload[1]["role"], "user")

    def test_sliding_window_pruning(self):
        # Setup tight limit to force window sliding
        tight_mgr = ConversationManager(
            system_instruction="System",
            max_context_tokens=100,
            max_tokens=50,
        )
        # Add multiple long messages
        for i in range(10):
            tight_mgr.add_user_message(f"This is a relatively lengthy sentence number {i} to trigger token consumption.")
            tight_mgr.add_assistant_message(f"This is a response sentence number {i} that also consumes token budget.")

        # Total history messages should be pruned to keep under limit
        self.assertLess(len(tight_mgr.history), 20)
        # System prompt must remain intact
        self.assertEqual(tight_mgr.system_message.content, "System")

    def test_session_serialization(self):
        self.mgr.add_user_message("First question")
        self.mgr.add_assistant_message("First answer")
        exported = self.mgr.export_session()

        new_mgr = ConversationManager()
        new_mgr.import_session(exported)

        self.assertEqual(new_mgr.system_message.content, self.mgr.system_message.content)
        self.assertEqual(len(new_mgr.history), 2)
        self.assertEqual(new_mgr.temperature, 0.8)


if __name__ == "__main__":
    unittest.main()
