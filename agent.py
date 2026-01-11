import json
import os
from typing import Dict, List, Optional, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, add_messages
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    intent: Optional[str]
    user_name: Optional[str]
    user_email: Optional[str]
    user_platform: Optional[str]
    knowledge_context: Optional[str]

class AutoStreamAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            temperature=0.1
        )
        self.knowledge_base = self._load_knowledge_base()
        self.graph = self._build_graph()
        
    def _load_knowledge_base(self) -> Dict:
        with open('knowledge_base.json', 'r') as f:
            return json.load(f)
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("intent_detection", self._detect_intent)
        workflow.add_node("rag_retrieval", self._rag_retrieval)
        workflow.add_node("response_generation", self._generate_response)
        workflow.add_node("lead_qualification", self._lead_qualification)
        workflow.add_node("lead_capture", self._lead_capture)
        
        workflow.set_entry_point("intent_detection")
        
        workflow.add_conditional_edges(
            "intent_detection",
            self._route_intent,
            {
                "greeting": "response_generation",
                "product_inquiry": "rag_retrieval", 
                "high_intent": "lead_qualification"
            }
        )
        
        workflow.add_edge("rag_retrieval", "response_generation")
        workflow.add_edge("response_generation", END)
        
        workflow.add_conditional_edges(
            "lead_qualification",
            self._check_lead_complete,
            {
                "complete": "lead_capture",
                "incomplete": "response_generation"
            }
        )
        
        workflow.add_edge("lead_capture", END)
        
        return workflow.compile(checkpointer=MemorySaver())
    
    def _detect_intent(self, state: AgentState) -> AgentState:
        last_message = state["messages"][-1].content
        
        intent_prompt = ChatPromptTemplate.from_template("""
        Classify the user's intent into one of these categories:
        1. "greeting" - casual greetings, general conversation
        2. "product_inquiry" - questions about pricing, features, policies
        3. "high_intent" - ready to sign up, wants to try/buy, shows purchase intent
        
        User message: {message}
        
        Respond with only the category name.
        """)
        
        response = self.llm.invoke(intent_prompt.format(message=last_message))
        intent = response.content.strip().lower()
        
        state["intent"] = intent
        return state
    
    def _route_intent(self, state: AgentState) -> str:
        return state["intent"]
    
    def _rag_retrieval(self, state: AgentState) -> AgentState:
        last_message = state["messages"][-1].content
        
        # Simple keyword-based retrieval
        context_parts = []
        
        if any(word in last_message.lower() for word in ["price", "pricing", "cost", "plan"]):
            context_parts.append(f"Pricing Plans: {json.dumps(self.knowledge_base['pricing_plans'], indent=2)}")
        
        if any(word in last_message.lower() for word in ["policy", "refund", "support"]):
            context_parts.append(f"Policies: {json.dumps(self.knowledge_base['company_policies'], indent=2)}")
        
        if any(word in last_message.lower() for word in ["feature", "what", "about", "autostream"]):
            context_parts.append(f"Company Info: {json.dumps(self.knowledge_base['company_info'], indent=2)}")
            context_parts.append(f"Pricing Plans: {json.dumps(self.knowledge_base['pricing_plans'], indent=2)}")
        
        state["knowledge_context"] = "\\n".join(context_parts)
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        last_message = state["messages"][-1].content
        intent = state["intent"]
        
        if intent == "greeting":
            response_prompt = ChatPromptTemplate.from_template("""
            You are a helpful AI assistant for AutoStream, an automated video editing SaaS for content creators.
            Respond to this greeting in a friendly, professional way and offer to help with questions about our product.
            
            User: {message}
            """)
            response = self.llm.invoke(response_prompt.format(message=last_message))
            
        elif intent == "product_inquiry":
            response_prompt = ChatPromptTemplate.from_template("""
            You are a helpful AI assistant for AutoStream. Use the provided context to answer the user's question accurately.
            Be concise and helpful. If asked about pricing, mention both plans clearly.
            
            Context: {context}
            User Question: {message}
            """)
            response = self.llm.invoke(response_prompt.format(
                context=state.get("knowledge_context", ""),
                message=last_message
            ))
        
        state["messages"].append(AIMessage(content=response.content))
        return state
    
    def _lead_qualification(self, state: AgentState) -> AgentState:
        # Extract user info from the latest message
        last_message = state["messages"][-1].content
        state = self._extract_user_info(last_message, state)
        
        missing_info = []
        
        if not state.get("user_name"):
            missing_info.append("name")
        if not state.get("user_email"):
            missing_info.append("email")
        if not state.get("user_platform"):
            missing_info.append("creator platform (YouTube, Instagram, etc.)")
        
        if missing_info:
            response = f"Great! I'd love to help you get started with AutoStream. To proceed, I'll need your {', '.join(missing_info)}."
        else:
            response = "Perfect! I have all your information. Let me get you signed up."
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def _check_lead_complete(self, state: AgentState) -> str:
        if state.get("user_name") and state.get("user_email") and state.get("user_platform"):
            return "complete"
        return "incomplete"
    
    def _lead_capture(self, state: AgentState) -> AgentState:
        # Call the mock API function
        mock_lead_capture(
            state["user_name"],
            state["user_email"], 
            state["user_platform"]
        )
        
        response = f"Excellent! I've successfully captured your information and you're all set to get started with AutoStream Pro. Welcome aboard, {state['user_name']}!"
        state["messages"].append(AIMessage(content=response))
        return state
    
    def _extract_user_info(self, message: str, state: AgentState) -> AgentState:
        """Extract user information from message using LLM"""
        extract_prompt = ChatPromptTemplate.from_template("""
        Extract the following information from the user's message if present:
        - Name
        - Email
        - Platform (YouTube, Instagram, TikTok, etc.)
        
        Message: {message}
        
        Respond in JSON format:
        {{"name": "value or null", "email": "value or null", "platform": "value or null"}}
        """)
        
        response = self.llm.invoke(extract_prompt.format(message=message))
        try:
            extracted = json.loads(response.content)
            if extracted.get("name"):
                state["user_name"] = extracted["name"]
            if extracted.get("email"):
                state["user_email"] = extracted["email"]
            if extracted.get("platform"):
                state["user_platform"] = extracted["platform"]
        except:
            pass
        
        return state
    
    def chat(self, message: str, thread_id: str = "default") -> str:
        # Get current state
        config = {"configurable": {"thread_id": thread_id}}
        current_state = self.graph.get_state(config)
        
        if current_state.values:
            state = current_state.values
        else:
            state = AgentState(
                messages=[],
                intent=None,
                user_name=None,
                user_email=None,
                user_platform=None,
                knowledge_context=None
            )
        
        # Add user message
        state["messages"].append(HumanMessage(content=message))
        
        # Run the graph
        result = self.graph.invoke(state, config)
        
        # Return the last assistant message
        return result["messages"][-1].content

def mock_lead_capture(name: str, email: str, platform: str):
    """Mock API function for lead capture"""
    print(f"Lead captured successfully: {name}, {email}, {platform}")

if __name__ == "__main__":
    # Demo conversation
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    agent = AutoStreamAgent(api_key)
    
    print("AutoStream AI Agent Demo")
    print("Type 'quit' to exit\\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        response = agent.chat(user_input)
        print(f"Agent: {response}\\n")