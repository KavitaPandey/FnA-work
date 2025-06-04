"""
LangGraph Invoice Parser with Advanced Tracing and Observability
"""

import os
import yaml
import json
import base64
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime
from openai import OpenAI
from langgraph.graph import StateGraph, END
from utils import convert_image_to_base64, extract_text_from_pdf, read_text_file

# Define the state structure for LangGraph
class InvoiceState(TypedDict):
    """State structure for the invoice processing workflow."""
    file_path: str
    file_type: str
    extracted_content: str
    analysis_result: str
    thinking_log: Dict[str, str]
    trace_id: str
    workflow_step: str
    error: str

def load_config(config_path="config.yml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        return {
            "openai": {
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens_summary": 1000,
                "max_tokens_image_analysis": 1000,
                "system_role_summary": "You are an AI assistant that specializes in extracting and summarizing invoice information.",
                "system_role_image": "You are an AI assistant that specializes in extracting text from invoice images and organizing the information."
            }
        }

class InvoiceTracer:
    """LangGraph-powered invoice parser with advanced tracing and observability."""
    
    def __init__(self, config_path="config.yml"):
        """Initialize the LangGraph-based tracer."""
        self.config = load_config(config_path)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required but not found in environment variables.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # LangGraph workflow and tracing
        self.workflow = self._build_workflow()
        self.trace_data = {}
        self.current_trace_id = None
        self.live_thinking = {
            "workflow": "",
            "extraction": "",
            "analysis": ""
        }
    
    def _create_trace_id(self):
        """Create a unique trace ID for this run."""
        self.current_trace_id = f"langraph_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace_data[self.current_trace_id] = {
            "workflow_steps": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "result": None,
            "state_transitions": []
        }
        return self.current_trace_id
    
    def _log_thinking(self, state: InvoiceState, step_name: str, thinking: str):
        """Log thinking process with LangGraph state tracking."""
        if not self.current_trace_id:
            self._create_trace_id()
        
        # Update live thinking
        self.live_thinking[step_name] = thinking
        state["thinking_log"][step_name] = thinking
        
        # Log to trace data with state information
        self.trace_data[self.current_trace_id]["workflow_steps"].append({
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "thinking": thinking,
            "state_snapshot": {
                "workflow_step": state.get("workflow_step", ""),
                "file_path": state.get("file_path", ""),
                "file_type": state.get("file_type", ""),
                "has_content": bool(state.get("extracted_content", "")),
                "has_result": bool(state.get("analysis_result", ""))
            }
        })
        
        return state
    
    def analyze_file_node(self, state: InvoiceState) -> InvoiceState:
        """LangGraph Node 1: Analyze file type and plan processing approach."""
        state["workflow_step"] = "analyze_file"
        
        thinking = f"""
🔍 WORKFLOW ANALYSIS
==================
File: {state['file_path']}
Type: {state['file_type']}

Planning processing approach:
• PDF files → Extract text, check for embedded images/tables
• Image files → Use vision capabilities for OCR and analysis  
• Text files → Direct text processing

Determining if document contains single or multiple invoices...
Looking for invoice separators, headers, and structure patterns...
"""
        
        return self._log_thinking(state, "workflow", thinking)
    
    def extract_content_node(self, state: InvoiceState) -> InvoiceState:
        """LangGraph Node 2: Extract content from the file."""
        state["workflow_step"] = "extract_content"
        
        thinking = f"""
📄 CONTENT EXTRACTION
====================
Processing: {state['file_path']}

"""
        
        extracted_text = ""
        
        try:
            if "pdf" in state['file_type'].lower():
                thinking += "🔧 PDF Processing:\n"
                thinking += "• Opening PDF with PyPDF2\n"
                thinking += "• Extracting text from each page\n"
                thinking += "• Identifying potential image-only pages\n"
                
                extracted_text = extract_text_from_pdf(state['file_path'])
                
                # Check for image markers
                if "Image-based content" in extracted_text:
                    thinking += "• Found pages with potential images/tables\n"
                    thinking += "• These may need visual analysis\n"
                
                thinking += f"\n📝 Sample extracted text:\n{extracted_text[:300]}...\n"
                
            elif state['file_type'].lower().startswith("image"):
                thinking += "🖼️ Image Processing:\n"
                thinking += "• Preparing image for vision analysis\n"
                thinking += "• Will use OpenAI Vision API for OCR\n"
                extracted_text = f"[IMAGE_FILE:{state['file_path']}]"
                
            else:  # Text files
                thinking += "📝 Text File Processing:\n"
                thinking += "• Reading file content directly\n"
                extracted_text = read_text_file(state['file_path'])
                thinking += f"\n📄 Text sample:\n{extracted_text[:300]}...\n"
            
            thinking += "\n✅ Content extraction completed successfully\n"
            thinking += "🔍 Analyzing structure for invoice patterns...\n"
            
            state["extracted_content"] = extracted_text
            
        except Exception as e:
            thinking += f"\n❌ Error during extraction: {str(e)}\n"
            state["error"] = str(e)
        
        return self._log_thinking(state, "extraction", thinking)
    
    def analyze_invoice_node(self, state: InvoiceState) -> InvoiceState:
        """LangGraph Node 3: Analyze the extracted content to generate invoice data."""
        state["workflow_step"] = "analyze_invoice"
        
        extracted_text = state.get("extracted_content", "")
        thinking = f"""
🧠 INVOICE ANALYSIS
==================
Content type: {state['file_type']}
Text length: {len(extracted_text)} characters

Analysis strategy:
• Identify invoice structure and key sections
• Extract financial data (amounts, dates, vendors)
• Detect multiple invoices if present
• Generate structured JSON output
• Provide business interpretation

"""
        
        try:
            if extracted_text.startswith("[IMAGE_FILE:"):
                # Handle image analysis
                thinking += "🖼️ Using Vision API for image analysis:\n"
                thinking += "• Converting image to base64\n"
                thinking += "• Sending to OpenAI Vision model\n"
                thinking += "• Extracting structured data from visual content\n"
                
                result = self._analyze_image(state['file_path'])
                
            else:
                # Handle text analysis
                thinking += "📝 Using Text API for content analysis:\n"
                thinking += "• Sending to OpenAI text model\n"
                thinking += "• Looking for invoice patterns and structure\n"
                thinking += "• Extracting key fields and financial data\n"
                
                result = self._analyze_text(extracted_text)
            
            thinking += "\n✅ Analysis completed\n"
            thinking += "📊 Generating structured output...\n"
            
            if result:
                state["analysis_result"] = str(result)
            else:
                state["analysis_result"] = ""
            
        except Exception as e:
            thinking += f"\n❌ Error during analysis: {str(e)}\n"
            state["error"] = str(e)
        
        return self._log_thinking(state, "analysis", thinking)
    
    def _analyze_image(self, image_path: str):
        """Analyze image using OpenAI Vision API."""
        base64_image = convert_image_to_base64(image_path)
        
        system_message = self.config["openai"]["system_role_image"]
        prompt = self._get_analysis_prompt()
        
        response = self.client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            temperature=self.config["openai"]["temperature"]
        )
        
        return response.choices[0].message.content
    
    def _analyze_text(self, text: str):
        """Analyze text using OpenAI API."""
        system_message = self.config["openai"]["system_role_summary"]
        prompt = self._get_analysis_prompt() + f"\n\nHere is the invoice content:\n{text}"
        
        response = self.client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config["openai"]["temperature"]
        )
        
        return response.choices[0].message.content
    
    def _build_workflow(self):
        """Build the LangGraph workflow with proper state transitions and tracing."""
        workflow = StateGraph(InvoiceState)
        
        # Add nodes to the workflow
        workflow.add_node("analyze_file", self.analyze_file_node)
        workflow.add_node("extract_content", self.extract_content_node)
        workflow.add_node("analyze_invoice", self.analyze_invoice_node)
        
        # Define the workflow edges (state transitions)
        workflow.set_entry_point("analyze_file")
        workflow.add_edge("analyze_file", "extract_content")
        workflow.add_edge("extract_content", "analyze_invoice")
        workflow.add_edge("analyze_invoice", END)
        
        # Compile the workflow with tracing enabled
        return workflow.compile()
    
    def _get_analysis_prompt(self):
        """Get the standardized analysis prompt."""
        return """
Analyze this invoice carefully. Extract all payment details and financial information accurately.
Pay special attention to outstanding amounts, payment history, and fee structures.

If the document contains multiple invoices, identify and analyze each one separately.

INSTRUCTIONS:
1. Provide your response in two parts.

PART 1: 
If there's only ONE invoice, output structured invoice data in JSON format with only these keys:
{
  "Invoice_Number": "value",
  "Invoice_Date": "value", 
  "Vendor": "value",
  "Total_Invoice_Amount": "value",
  "Payment_Terms": "value",
  "Outstanding_Amount": "value",
  "Due_Date": "value"
}

If there are MULTIPLE invoices, output a JSON array with one object for each invoice:
[
  {
    "Invoice_Number": "value for invoice 1",
    "Invoice_Date": "value for invoice 1",
    "Vendor": "value for invoice 1",
    "Total_Invoice_Amount": "value for invoice 1", 
    "Payment_Terms": "value for invoice 1",
    "Outstanding_Amount": "value for invoice 1",
    "Due_Date": "value for invoice 1"
  },
  {
    "Invoice_Number": "value for invoice 2",
    "Invoice_Date": "value for invoice 2",
    ...and so on
  }
]

Additionally, if there are multiple invoices, calculate and add a field for combined totals:
{
  "Combined_Total_Invoice_Amount": "sum of all invoice amounts",
  "Combined_Outstanding_Amount": "sum of all outstanding amounts", 
  "Invoice_Count": "number of invoices found"
}

PART 2: Provide a brief business interpretation of the invoice(s) in 3-5 bullet points. Include:
- The business relationship context
- Important dates or deadlines
- Payment status and recommendations
- Any unusual aspects of the invoice that require attention
- If multiple invoices, summarize the overall financial picture
"""
    
    def process_invoice(self, file_path: str, file_type: str):
        """Process invoice using LangGraph workflow with advanced tracing."""
        # Create new trace
        trace_id = self._create_trace_id()
        
        # Reset live thinking
        self.live_thinking = {
            "workflow": "",
            "extraction": "", 
            "analysis": ""
        }
        
        # Initialize LangGraph state
        initial_state: InvoiceState = {
            "file_path": file_path,
            "file_type": file_type,
            "extracted_content": "",
            "analysis_result": "",
            "thinking_log": {},
            "trace_id": trace_id,
            "workflow_step": "",
            "error": ""
        }
        
        try:
            # Execute the LangGraph workflow with full tracing
            final_state = self.workflow.invoke(initial_state)
            
            # Finalize trace with LangGraph observability data
            if self.current_trace_id:
                self.trace_data[self.current_trace_id]["end_time"] = datetime.now().isoformat()
                self.trace_data[self.current_trace_id]["result"] = final_state.get("analysis_result", "")
                self.trace_data[self.current_trace_id]["final_state"] = {
                    "workflow_step": final_state.get("workflow_step", ""),
                    "has_error": bool(final_state.get("error", "")),
                    "content_length": len(final_state.get("extracted_content", "")),
                    "result_length": len(final_state.get("analysis_result", ""))
                }
            
            return final_state.get("analysis_result", "")
            
        except Exception as e:
            if self.current_trace_id:
                self.trace_data[self.current_trace_id]["end_time"] = datetime.now().isoformat()
                self.trace_data[self.current_trace_id]["error"] = str(e)
            return f"Error processing invoice: {str(e)}"
    
    def get_live_thinking(self):
        """Get the current live thinking process."""
        return self.live_thinking
    
    def get_trace(self, trace_id=None):
        """Get LangGraph trace data with enhanced observability metrics."""
        if not trace_id:
            trace_id = self.current_trace_id
        
        if trace_id and trace_id in self.trace_data:
            trace = self.trace_data[trace_id].copy()
            
            # Add LangGraph observability metrics
            trace["observability"] = {
                "total_workflow_steps": len(trace.get("workflow_steps", [])),
                "execution_duration": self._calculate_duration(trace),
                "state_transitions": len(trace.get("state_transitions", [])),
                "thinking_process_length": sum(len(step.get("thinking", "")) 
                                             for step in trace.get("workflow_steps", [])),
                "success_rate": 1.0 if not trace.get("error") else 0.0
            }
            
            return trace
        return None
    
    def _calculate_duration(self, trace):
        """Calculate workflow execution duration."""
        try:
            if trace.get("start_time") and trace.get("end_time"):
                start = datetime.fromisoformat(trace["start_time"])
                end = datetime.fromisoformat(trace["end_time"])
                return (end - start).total_seconds()
        except:
            pass
        return None
    
    def get_workflow_metrics(self):
        """Get comprehensive workflow performance metrics."""
        if not self.trace_data:
            return {}
        
        traces = list(self.trace_data.values())
        total_traces = len(traces)
        
        successful_traces = [t for t in traces if not t.get("error")]
        failed_traces = [t for t in traces if t.get("error")]
        
        durations = [self._calculate_duration(t) for t in traces]
        valid_durations = [d for d in durations if d is not None]
        
        return {
            "total_executions": total_traces,
            "success_rate": len(successful_traces) / total_traces if total_traces > 0 else 0,
            "failure_rate": len(failed_traces) / total_traces if total_traces > 0 else 0,
            "average_duration": sum(valid_durations) / len(valid_durations) if valid_durations else 0,
            "min_duration": min(valid_durations) if valid_durations else 0,
            "max_duration": max(valid_durations) if valid_durations else 0,
            "total_thinking_steps": sum(len(t.get("workflow_steps", [])) for t in traces)
        }
    
    def export_trace_to_json(self, trace_id=None, file_path=None):
        """Export enhanced trace data with LangGraph observability to JSON file."""
        trace = self.get_trace(trace_id)
        
        if not trace:
            return False
        
        if not file_path:
            trace_id = trace_id or self.current_trace_id
            file_path = f"output/{trace_id}_enhanced.json"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Add workflow metrics to export
        enhanced_export = {
            "trace_data": trace,
            "workflow_metrics": self.get_workflow_metrics(),
            "export_timestamp": datetime.now().isoformat(),
            "langraph_version": "enhanced_tracing"
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(enhanced_export, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting trace: {e}")
            return False
    
    def get_live_workflow_state(self):
        """Get current workflow state with LangGraph observability."""
        return {
            "current_trace_id": self.current_trace_id,
            "live_thinking": self.live_thinking,
            "workflow_status": "running" if self.current_trace_id else "idle",
            "total_traces": len(self.trace_data),
            "current_metrics": self.get_workflow_metrics()
        }