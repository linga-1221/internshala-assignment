import json

def mock_lead_capture(name: str, email: str, platform: str):
    """Mock API function for lead capture"""
    print(f"Lead captured successfully: {name}, {email}, {platform}")

class AutoStreamAgent:
    def __init__(self):
        self.state = {
            "intent": None,
            "user_name": None,
            "user_email": None,
            "user_platform": None
        }
        
    def chat(self, message: str) -> str:
        message_lower = message.lower()
        
        # Extract user info
        if "@" in message and not self.state["user_email"]:
            words = message.split()
            for word in words:
                if "@" in word:
                    self.state["user_email"] = word
                    break
        
        if any(platform in message_lower for platform in ["youtube", "instagram", "tiktok"]):
            for word in message.split():
                if word.lower() in ["youtube", "instagram", "tiktok"]:
                    self.state["user_platform"] = word.capitalize()
                    break
        
        if not self.state["user_name"] and any(phrase in message_lower for phrase in ["name is", "i'm", "i am"]):
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["is", "i'm", "am"] and i + 1 < len(words):
                    self.state["user_name"] = words[i + 1]
                    break
        
        # Intent Detection
        if any(word in message_lower for word in ["want", "try", "buy", "sign up", "pro plan"]):
            self.state["intent"] = "high_intent"
            return self._handle_high_intent()
        elif any(word in message_lower for word in ["price", "pricing", "cost", "plan", "feature"]):
            self.state["intent"] = "product_inquiry"
            return self._handle_product_inquiry()
        else:
            self.state["intent"] = "greeting"
            return "Hello! I'm the AutoStream AI assistant. I can help you learn about our automated video editing platform. What would you like to know about our pricing or features?"
    
    def _handle_product_inquiry(self) -> str:
        return """Here are AutoStream's pricing plans:

Basic Plan - $29/month
• 10 videos/month
• 720p resolution

Pro Plan - $79/month
• Unlimited videos
• 4K resolution
• AI captions
• 24/7 support

Policies:
• No refunds after 7 days
• 24/7 support available only on Pro plan

Would you like to try one of our plans?"""
    
    def _handle_high_intent(self) -> str:
        missing = []
        if not self.state["user_name"]:
            missing.append("name")
        if not self.state["user_email"]:
            missing.append("email")
        if not self.state["user_platform"]:
            missing.append("creator platform (YouTube, Instagram, etc.)")
        
        if missing:
            return f"Great! I'd love to help you get started with AutoStream Pro. To proceed, I'll need your {', '.join(missing)}."
        else:
            mock_lead_capture(
                self.state["user_name"],
                self.state["user_email"],
                self.state["user_platform"]
            )
            return f"Excellent! I've successfully captured your information and you're all set to get started with AutoStream Pro. Welcome aboard, {self.state['user_name']}!"

if __name__ == "__main__":
    print("AutoStream AI Agent - DEMO MODE")
    print("Type 'quit' to exit\n")
    
    agent = AutoStreamAgent()
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        response = agent.chat(user_input)
        print(f"Agent: {response}\n")