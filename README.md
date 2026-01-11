# AutoStream AI Agent - Social-to-Lead Workflow

A conversational AI agent that converts social media conversations into qualified business leads for AutoStream, an automated video editing SaaS platform.

## Features

- **Intent Detection**: Classifies user intent (greeting, product inquiry, high-intent lead)
- **RAG-Powered Knowledge Retrieval**: Answers questions using local knowledge base
- **Lead Capture**: Collects user information and triggers mock API calls
- **State Management**: Maintains conversation context across multiple turns

## How to Run Locally

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd internshala-assignment
   pip install -r requirements.txt
   ```

2. **Set Environment Variable**
   ```bash
   # Windows
   set OPENAI_API_KEY=your_openai_api_key_here
   
   # Linux/Mac
   export OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the Agent**
   ```bash
   python agent.py
   ```

4. **Test Conversation Flow**
   - Start with: "Hi, tell me about your pricing"
   - Follow up with: "That sounds good, I want to try the Pro plan for my YouTube channel"
   - Provide name, email, and platform when asked

## Architecture Explanation

**Framework Choice: LangGraph**
I chose LangGraph over AutoGen because it provides superior state management for multi-turn conversations and conditional workflow routing. LangGraph's graph-based approach allows for complex conversation flows where the agent can dynamically route between different capabilities (intent detection → RAG retrieval → lead qualification → tool execution) based on user responses.

**State Management**
The agent uses LangGraph's built-in state management with MemorySaver checkpointer to maintain conversation context across 5-6 turns. The AgentState TypedDict tracks:
- Conversation messages
- Current user intent
- Lead qualification data (name, email, platform)
- Retrieved knowledge context

**Workflow Design**
The agent follows a conditional graph structure:
1. **Intent Detection** → Routes to appropriate handler
2. **RAG Retrieval** → Fetches relevant knowledge for product inquiries  
3. **Lead Qualification** → Collects required user information
4. **Tool Execution** → Calls mock_lead_capture() when complete

## WhatsApp Deployment Integration

To integrate this agent with WhatsApp using webhooks:

1. **Webhook Setup**
   - Register webhook URL with WhatsApp Business API
   - Handle incoming POST requests containing message data
   - Extract user message and phone number as thread_id

2. **Message Processing**
   ```python
   @app.route('/webhook', methods=['POST'])
   def webhook():
       data = request.json
       user_message = data['messages'][0]['text']['body']
       phone_number = data['messages'][0]['from']
       
       response = agent.chat(user_message, thread_id=phone_number)
       
       # Send response back via WhatsApp API
       send_whatsapp_message(phone_number, response)
   ```

3. **State Persistence**
   - Use phone number as unique thread_id for LangGraph state management
   - Each user maintains separate conversation context
   - Lead capture data persists across message sessions

4. **API Integration**
   - Replace mock_lead_capture() with actual CRM API calls
   - Add error handling and retry logic for webhook reliability
   - Implement message queuing for high-volume scenarios

## Project Structure

```
internshala-assignment/
├── agent.py              # Main agent implementation
├── knowledge_base.json   # AutoStream pricing & policies
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Demo Video

Record a 2-3 minute screen recording showing:
1. Agent answering pricing questions using RAG
2. Agent detecting high-intent user behavior
3. Agent collecting user details (name, email, platform)
4. Successful lead capture with mock tool execution