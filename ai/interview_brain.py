"""AI-powered interview brain using Google Gemini Flash 2.0 for intelligent conversations."""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)


class InterviewAI:
    """AI brain for conducting intelligent interviews using Google Gemini Flash 2.0."""
    
    def __init__(self):
        """Initialize the interview AI with Google Gemini configuration."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        # Conversation state
        self.conversation_history: List[Dict] = []
        self.candidate_info: Dict = {}
        self.interview_context: Dict = {}
        self.current_topic: str = "introduction"
        self.questions_asked: int = 0
        self.max_questions: int = settings.max_questions
        
        # Interview framework
        self.interview_stages = [
            "introduction",
            "background",
            "technical_skills",
            "problem_solving",
            "behavioral",
            "scenario_based",
            "closing"
        ]
        
        self.current_stage_index = 0
        
        # Question templates and scoring
        self.question_templates = self._load_question_templates()
        self.evaluation_criteria = self._load_evaluation_criteria()
        
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different interview stages."""
        return {
            "introduction": [
                "Hello! I'm your AI interviewer today. Could you please introduce yourself and tell me a bit about your background?",
                "Welcome to the interview! Let's start with you telling me about yourself and what interests you about this role.",
                "Hi there! I'm excited to learn more about you. Could you walk me through your professional journey so far?"
            ],
            "background": [
                "Can you tell me about a recent project you worked on that you're particularly proud of?",
                "What's the most challenging technical problem you've solved recently?",
                "Describe a time when you had to learn a new technology quickly. How did you approach it?"
            ],
            "technical_skills": [
                "Let's dive into your technical expertise. Can you explain [specific technology] and how you've used it?",
                "Walk me through how you would approach designing a system for [specific scenario].",
                "What are some best practices you follow when writing code?"
            ],
            "problem_solving": [
                "Here's a technical challenge: [problem]. How would you approach solving this?",
                "If you encountered a performance issue in production, what steps would you take to diagnose and fix it?",
                "Describe your debugging process when facing a complex issue."
            ],
            "behavioral": [
                "Tell me about a time when you disagreed with a team member. How did you handle it?",
                "Describe a situation where you had to work under tight deadlines. How did you manage?",
                "Can you give me an example of when you went above and beyond in your role?"
            ],
            "scenario_based": [
                "Imagine you're tasked with improving the performance of a slow application. Walk me through your approach.",
                "How would you handle a situation where a critical bug is discovered right before a major release?",
                "If you had to explain a complex technical concept to a non-technical stakeholder, how would you do it?"
            ],
            "closing": [
                "Do you have any questions about the role or the company?",
                "Is there anything else you'd like to share that we haven't covered?",
                "What are you most excited about regarding this opportunity?"
            ]
        }
    
    def _load_evaluation_criteria(self) -> Dict[str, List[str]]:
        """Load evaluation criteria for different aspects."""
        return {
            "technical_knowledge": [
                "Depth of understanding",
                "Practical application experience",
                "Problem-solving approach",
                "Code quality awareness"
            ],
            "communication": [
                "Clarity of explanation",
                "Ability to simplify complex concepts",
                "Active listening",
                "Professional demeanor"
            ],
            "problem_solving": [
                "Analytical thinking",
                "Creative solutions",
                "Systematic approach",
                "Handling ambiguity"
            ],
            "cultural_fit": [
                "Team collaboration",
                "Adaptability",
                "Learning mindset",
                "Professional values"
            ]
        }
    
    async def initialize_interview(self, candidate_info: Dict, role_info: Dict) -> str:
        """
        Initialize the interview session with candidate and role information.
        
        Args:
            candidate_info: Information about the candidate
            role_info: Information about the role/position
            
        Returns:
            Opening question/greeting
        """
        try:
            self.candidate_info = candidate_info
            self.interview_context = {
                "role": role_info,
                "start_time": datetime.now().isoformat(),
                "duration_minutes": settings.interview_duration_minutes
            }
            
            # Generate personalized opening
            opening_prompt = f"""
            You are an AI interviewer conducting a professional interview for a {role_info.get('title', 'software developer')} position.
            
            Candidate information:
            - Name: {candidate_info.get('name', 'Candidate')}
            - Experience: {candidate_info.get('experience_level', 'Not specified')}
            - Background: {candidate_info.get('background', 'Not provided')}
            
            Generate a warm, professional opening greeting that:
            1. Introduces you as the AI interviewer
            2. Sets expectations for the interview
            3. Makes the candidate feel comfortable
            4. Asks for a brief self-introduction
            
            Keep it concise and professional.
            """
            
            response = await self._generate_response(opening_prompt, max_tokens=200, temperature=0.7)
            
            opening_message = response.strip()
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "interviewer",
                "content": opening_message,
                "stage": "introduction"
            })
            
            logger.info("Interview initialized successfully")
            return opening_message
            
        except Exception as e:
            logger.error(f"Error initializing interview: {str(e)}")
            return "Hello! I'm your AI interviewer today. Could you please introduce yourself?"
    
    async def analyze_response(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Analyze candidate response and generate evaluation.
        
        Args:
            question: The question that was asked
            answer: The candidate's response
            
        Returns:
            Analysis results including scores and insights
        """
        try:
            analysis_prompt = f"""
            As an expert interviewer, analyze this candidate response:
            
            Question: {question}
            Answer: {answer}
            
            Provide analysis in the following JSON format:
            {{
                "content_quality": {{
                    "score": 1-10,
                    "reasoning": "explanation"
                }},
                "communication_clarity": {{
                    "score": 1-10,
                    "reasoning": "explanation"
                }},
                "technical_depth": {{
                    "score": 1-10,
                    "reasoning": "explanation"
                }},
                "key_insights": ["insight1", "insight2"],
                "areas_to_explore": ["area1", "area2"],
                "overall_assessment": "brief summary",
                "follow_up_suggestions": ["suggestion1", "suggestion2"]
            }}
            
            Be objective and constructive in your analysis.
            """
            
            response = await self._generate_response(analysis_prompt, max_tokens=500, temperature=0.3)
            
            analysis_text = response.strip()
            
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = {
                    "content_quality": {"score": 7, "reasoning": "Response analyzed"},
                    "communication_clarity": {"score": 7, "reasoning": "Clear communication"},
                    "technical_depth": {"score": 6, "reasoning": "Adequate technical detail"},
                    "key_insights": ["Response provided"],
                    "areas_to_explore": ["Further technical details"],
                    "overall_assessment": "Satisfactory response",
                    "follow_up_suggestions": ["Ask for more specific examples"]
                }
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "candidate",
                "content": answer,
                "question": question,
                "analysis": analysis,
                "stage": self.current_topic
            })
            
            logger.info(f"Response analyzed successfully. Overall quality: {analysis.get('overall_assessment', 'N/A')}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response: {str(e)}")
            return {
                "content_quality": {"score": 5, "reasoning": "Analysis error"},
                "communication_clarity": {"score": 5, "reasoning": "Analysis error"},
                "technical_depth": {"score": 5, "reasoning": "Analysis error"},
                "key_insights": ["Unable to analyze"],
                "areas_to_explore": ["Technical skills"],
                "overall_assessment": "Unable to analyze response",
                "follow_up_suggestions": ["Continue with next question"]
            }
    
    async def generate_next_question(self, previous_analysis: Optional[Dict] = None) -> str:
        """
        Generate the next interview question based on conversation history.
        
        Args:
            previous_analysis: Analysis of the previous response
            
        Returns:
            Next question to ask
        """
        try:
            self.questions_asked += 1
            
            # Check if we should move to next stage
            if self.questions_asked > 2 and self.current_stage_index < len(self.interview_stages) - 1:
                self.current_stage_index += 1
                self.current_topic = self.interview_stages[self.current_stage_index]
            
            # Build context for question generation
            context = self._build_conversation_context()
            
            question_prompt = f"""
            You are conducting a professional interview. Based on the conversation so far, generate the next appropriate question.
            
            Current interview stage: {self.current_topic}
            Questions asked so far: {self.questions_asked}
            Max questions: {self.max_questions}
            
            Conversation context:
            {context}
            
            Previous response analysis:
            {json.dumps(previous_analysis, indent=2) if previous_analysis else "No previous analysis"}
            
            Generate a relevant, engaging question that:
            1. Fits the current interview stage
            2. Builds on previous responses
            3. Explores areas identified for further discussion
            4. Is appropriate for the candidate's experience level
            5. Helps assess the candidate's fit for the role
            
            Return only the question, no additional text.
            """
            
            response = await self._generate_response(question_prompt, max_tokens=200, temperature=0.8)
            
            next_question = response.strip()
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "interviewer",
                "content": next_question,
                "stage": self.current_topic
            })
            
            logger.info(f"Generated next question for stage '{self.current_topic}': {next_question[:50]}...")
            return next_question
            
        except Exception as e:
            logger.error(f"Error generating next question: {str(e)}")
            
            # Fallback to template questions
            stage_templates = self.question_templates.get(self.current_topic, self.question_templates["background"])
            fallback_question = stage_templates[self.questions_asked % len(stage_templates)]
            
            return fallback_question
    
    def _build_conversation_context(self) -> str:
        """Build a summary of the conversation for context."""
        if not self.conversation_history:
            return "No conversation history yet."
        
        context_parts = []
        for entry in self.conversation_history[-5:]:  # Last 5 entries
            speaker = entry["speaker"]
            content = entry["content"][:100] + "..." if len(entry["content"]) > 100 else entry["content"]
            context_parts.append(f"{speaker.title()}: {content}")
        
        return "\n".join(context_parts)
    
    async def generate_final_assessment(self) -> Dict[str, Any]:
        """
        Generate comprehensive final assessment of the interview.
        
        Returns:
            Complete interview evaluation and recommendations
        """
        try:
            # Compile all analyses
            all_analyses = [
                entry.get("analysis", {}) for entry in self.conversation_history
                if entry.get("speaker") == "candidate" and "analysis" in entry
            ]
            
            assessment_prompt = f"""
            Generate a comprehensive interview assessment based on the complete conversation.
            
            Candidate: {self.candidate_info.get('name', 'Candidate')}
            Role: {self.interview_context.get('role', {}).get('title', 'Software Developer')}
            Interview Duration: {len(self.conversation_history)} exchanges
            
            Conversation Summary:
            {self._build_conversation_context()}
            
            Individual Response Analyses:
            {json.dumps(all_analyses, indent=2)}
            
            Provide a comprehensive assessment in JSON format:
            {{
                "overall_score": 1-10,
                "category_scores": {{
                    "technical_skills": 1-10,
                    "communication": 1-10,
                    "problem_solving": 1-10,
                    "cultural_fit": 1-10
                }},
                "strengths": ["strength1", "strength2"],
                "areas_for_improvement": ["area1", "area2"],
                "key_highlights": ["highlight1", "highlight2"],
                "recommendation": "hire/consider/pass",
                "reasoning": "detailed explanation",
                "next_steps": ["step1", "step2"],
                "interview_quality": "assessment of interview process"
            }}
            """
            
            response = await self._generate_response(assessment_prompt, max_tokens=800, temperature=0.3)
            
            assessment_text = response.strip()
            
            try:
                final_assessment = json.loads(assessment_text)
            except json.JSONDecodeError:
                # Fallback assessment
                final_assessment = {
                    "overall_score": 7,
                    "category_scores": {
                        "technical_skills": 7,
                        "communication": 7,
                        "problem_solving": 7,
                        "cultural_fit": 7
                    },
                    "strengths": ["Participated in interview"],
                    "areas_for_improvement": ["Continue developing skills"],
                    "key_highlights": ["Engaged in conversation"],
                    "recommendation": "consider",
                    "reasoning": "Standard interview performance",
                    "next_steps": ["Follow up with hiring team"],
                    "interview_quality": "Interview completed successfully"
                }
            
            # Add metadata
            final_assessment["interview_metadata"] = {
                "total_questions": self.questions_asked,
                "duration_minutes": settings.interview_duration_minutes,
                "stages_covered": list(set(entry.get("stage") for entry in self.conversation_history)),
                "completion_time": datetime.now().isoformat()
            }
            
            logger.info(f"Final assessment generated. Overall score: {final_assessment.get('overall_score')}")
            return final_assessment
            
        except Exception as e:
            logger.error(f"Error generating final assessment: {str(e)}")
            return {
                "overall_score": 5,
                "recommendation": "consider",
                "reasoning": "Assessment generation error",
                "interview_quality": "Technical issues during assessment"
            }
    
    def should_end_interview(self) -> bool:
        """
        Determine if the interview should end.
        
        Returns:
            True if interview should end
        """
        # End conditions
        if self.questions_asked >= self.max_questions:
            return True
        
        if self.current_stage_index >= len(self.interview_stages) - 1:
            return True
        
        # Check if we've covered all essential topics
        stages_covered = set(entry.get("stage") for entry in self.conversation_history)
        essential_stages = {"introduction", "background", "technical_skills"}
        
        if essential_stages.issubset(stages_covered) and self.questions_asked >= 8:
            return True
        
        return False
    
    async def _generate_response(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Generate response using Google Gemini Flash 2.0.
        
        Args:
            prompt: Input prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                top_k=64,
            )
            
            # Generate response
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {str(e)}")
            # Fallback response
            return "I apologize, but I'm having trouble generating a response right now. Let's continue with the interview."
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation state.
        
        Returns:
            Conversation summary dictionary
        """
        return {
            "questions_asked": self.questions_asked,
            "current_stage": self.current_topic,
            "stages_covered": list(set(entry.get("stage") for entry in self.conversation_history)),
            "total_exchanges": len(self.conversation_history),
            "candidate_responses": len([e for e in self.conversation_history if e.get("speaker") == "candidate"]),
            "interview_progress": f"{self.questions_asked}/{self.max_questions}"
        }