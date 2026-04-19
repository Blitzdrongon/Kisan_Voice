################################################################

"""
Main LangGraph workflow for RaithaMithra
"""

import os
from typing import Dict, Any, List
from loguru import logger

# Try different LangGraph imports for compatibility
try:
    from langgraph import StateGraph, END
except ImportError:
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        try:
            from langgraph.graph.state import StateGraph
            from langgraph.graph import END
        except ImportError:
            # Fallback for older versions
            from langgraph import Graph as StateGraph
            END = "END"

from nodes.conversation_nodes import get_conversation_nodes
from services.groq_service import get_groq_service
from services.whisper_services import get_whisper_service
from core.state import ConversationState


class RaithaMithraWorkflow:
    """Main conversation workflow"""
    
    def __init__(self):
        self.nodes = get_conversation_nodes()
        self.workflow_graph = None
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the conversation workflow"""
        try:
            from typing import TypedDict
            
            class WorkflowState(TypedDict):
                user_input: str
                session_id: str
                user_id: str
                language: str
                image_url: str | None
                audio_url: str | None          # 🔹 added audio support
                messages: list
                current_intent: str | None
                assistant_response: str | None
                audio_response_path: str | None
                audio_generated: bool
                conversation_history: list
                user_preferences: dict
                memory_saved: bool
                memory_id: str | None
                error: str | None
            
            workflow = StateGraph(WorkflowState)
            
            # Add nodes
            workflow.add_node("process_input", self.nodes.process_user_input)
            workflow.add_node("generate_response", self.nodes.generate_response)
            workflow.add_node("save_to_memory", self.nodes.save_to_memory)
            workflow.add_node("generate_audio", self.nodes.generate_audio_response)
            
            # Define edges
            workflow.add_edge("process_input", "generate_response")
            workflow.add_edge("generate_response", "save_to_memory")
            workflow.add_edge("save_to_memory", "generate_audio")
            workflow.add_edge("generate_audio", END)
            
            workflow.set_entry_point("process_input")

            self.workflow_graph = workflow
            return workflow.compile()
            
        except Exception as e:
            logger.error(f"Error building workflow: {e}")
            return self._build_simple_workflow()
    
    def _build_simple_workflow(self):
        """Build a simple workflow as fallback"""
        try:
            from typing import TypedDict
            
            class WorkflowState(TypedDict):
                user_input: str
                session_id: str
                user_id: str
                language: str
                image_url: str | None
                audio_url: str | None          # 🔹 added here too
                messages: list
                current_intent: str | None
                assistant_response: str | None
                audio_response_path: str | None
                audio_generated: bool
                conversation_history: list
                user_preferences: dict
                memory_saved: bool
                memory_id: str | None
                error: str | None
            
            workflow = StateGraph(WorkflowState)
            workflow.add_node("process_input", self.nodes.process_user_input)
            workflow.add_node("generate_response", self.nodes.generate_response)
            workflow.add_edge("process_input", "generate_response")
            workflow.add_edge("generate_response", END)
            workflow.set_entry_point("process_input")
            self.workflow_graph = workflow
            return workflow.compile()
        except Exception as e:
            logger.error(f"Error building simple workflow: {e}")
            return None
    
    async def run_conversation(
        self, 
        user_input: str, 
        session_id: str = None,
        user_id: str = None,
        language: str = "kn",
        image_url: str = None,
        audio_url: str = None       # 🔹 added audio here
    ) -> Dict[str, Any]:
        """Run the conversation workflow"""
        
        try:
            if not self.workflow:
                return await self._run_direct_conversation(
                    user_input, session_id, user_id, language, image_url, audio_url
                )
            
            if not session_id:
                session_id = f"session_{user_id}_{language}"
            
            # If audio is provided and no text input, transcribe audio first
            if audio_url and (not user_input or not str(user_input).strip()):
                try:
                    whisper = get_whisper_service()
                    transcription = await whisper.transcribe_file(audio_url, language=language)
                    if transcription:
                        user_input = transcription
                        logger.info("Audio transcribed and used as user_input in workflow")
                except Exception as transcribe_err:
                    logger.warning(f"Audio transcription failed: {transcribe_err}")
            
            initial_state = {
                "user_input": user_input,
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "language": language,
                "image_url": image_url,
                "audio_url": audio_url,   # 🔹 include correct key for downstream nodes
                "messages": [],
                "current_intent": None,
                "assistant_response": None,
                "audio_response_path": None,
                "audio_generated": False,
                "conversation_history": [],
                "user_preferences": {},
                "memory_saved": False,
                "memory_id": None,
                "error": None
            }
            
            logger.info(f"Starting conversation workflow for session: {session_id}")
            if hasattr(self.workflow, "ainvoke"):
                result = await self.workflow.ainvoke(initial_state)
            else:
                try:
                    result = self.workflow.invoke(initial_state)
                except Exception:
                    return await self._run_direct_conversation(
                        user_input, session_id, user_id, language, image_url, audio_url
                    )
            
            response_text = (result.get("assistant_response") or "").strip()
            if not response_text:
                response_text = "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, I couldn't generate a response."

            response = {
                "session_id": session_id,
                "user_input": user_input,
                "assistant_response": response_text,
                "audio_path": result.get("audio_response_path"),
                "audio_generated": result.get("audio_generated", False),
                "intent": result.get("current_intent", "general"),
                "language": language,
                "messages": result.get("messages", []),
                "conversation_history": result.get("conversation_history", []),
                "user_preferences": result.get("user_preferences", {}),
                "memory_saved": result.get("memory_saved", False),
                "memory_id": result.get("memory_id"),
                "error": result.get("error")
            }
            
            logger.info(f"Conversation completed for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in conversation workflow: {e}")
            return await self._run_direct_conversation(
                user_input, session_id, user_id, language, image_url, audio_url
            )
    
    async def _run_direct_conversation(
        self, 
        user_input: str, 
        session_id: str = None,
        user_id: str = None,
        language: str = "kn",
        image_url: str = None,
        audio_url: str = None       # 🔹 added audio param
    ) -> Dict[str, Any]:
        """Fallback: Run conversation directly without workflow"""
        
        try:
            if not session_id:
                session_id = f"session_{user_id}_{language}"
            
            # If audio is provided and no text input, transcribe audio first
            if audio_url and (not user_input or not str(user_input).strip()):
                try:
                    whisper = get_whisper_service()
                    transcription = await whisper.transcribe_file(audio_url, language=language)
                    if transcription:
                        user_input = transcription
                        logger.info("Audio transcribed and used as user_input (direct mode)")
                except Exception as transcribe_err:
                    logger.warning(f"Audio transcription failed (direct mode): {transcribe_err}")
            
            state = {
                "user_input": user_input,
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "language": language,
                "image_url": image_url,
                "audio_url": audio_url,   # 🔹 added here too
                "messages": [],
                "current_intent": None,
                "assistant_response": None,
                "audio_response_path": None,
                "audio_generated": False,
                "conversation_history": [],
                "user_preferences": {},
                "memory_saved": False,
                "memory_id": None,
                "error": None
            }
            
            state = await self.nodes.process_user_input(state)
            state = await self.nodes.generate_response(state)
            state = await self.nodes.save_to_memory(state)
            state = await self.nodes.generate_audio_response(state)
            
            return {
                "session_id": session_id,
                "user_input": user_input,
                "assistant_response": state.get("assistant_response", ""),
                "audio_path": state.get("audio_response_path"),
                "audio_generated": state.get("audio_generated", False),
                "intent": state.get("current_intent", "general"),
                "language": language,
                "messages": state.get("messages", []),
                "conversation_history": state.get("conversation_history", []),
                "user_preferences": state.get("user_preferences", {}),
                "memory_saved": state.get("memory_saved", False),
                "memory_id": state.get("memory_id"),
                "error": state.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error in direct conversation: {e}")
            return {
                "session_id": session_id,
                "user_input": user_input,
                "assistant_response": "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred.",
                "audio_path": None,
                "audio_generated": False,
                "intent": "error",
                "language": language,
                "messages": [],
                "conversation_history": [],
                "user_preferences": {},
                "memory_saved": False,
                "memory_id": None,
                "error": str(e)
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow information"""
        return {
            "name": "RaithaMithra Conversation Workflow",
            "nodes": ["process_input", "generate_response", "save_to_memory", "generate_audio"],
            "entry_point": "process_input",
            "end_point": "END",
            "status": "active" if self.workflow else "fallback_mode"
        }


# Global workflow instance
raithamithra_workflow = RaithaMithraWorkflow()


def get_workflow() -> RaithaMithraWorkflow:
    """Get workflow instance"""
    return raithamithra_workflow
