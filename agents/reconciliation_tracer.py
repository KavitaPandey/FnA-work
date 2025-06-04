"""
LangGraph Reconciliation Agent with Advanced Tracing and Observability
Compares amounts from invoice and spreadsheet agents to determine if they match
"""

import os
import yaml
import json
import re
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime
from openai import OpenAI
from langgraph.graph import StateGraph, END

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
                "max_tokens": 1000,
                "system_role": "You are an AI assistant that specializes in financial data reconciliation and amount comparison."
            }
        }

# Define the state structure for LangGraph
class ReconciliationState(TypedDict):
    """State structure for the reconciliation workflow."""
    invoice_amount: str
    spreadsheet_amount: str
    reconciliation_result: str
    verdict: str
    thinking_log: Dict[str, str]
    trace_id: str
    workflow_step: str
    error: str

class ReconciliationTracer:
    """LangGraph-powered reconciliation agent with advanced tracing and observability."""
    
    def __init__(self, config_path="config.yml"):
        """Initialize the LangGraph-based reconciliation tracer."""
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
            "parsing": "",
            "comparison": "",
            "verdict": ""
        }
    
    def _create_trace_id(self):
        """Create a unique trace ID for this run."""
        self.current_trace_id = f"reconciliation_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace_data[self.current_trace_id] = {
            "workflow_steps": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "result": None,
            "state_transitions": []
        }
        return self.current_trace_id
    
    def _log_thinking(self, state: ReconciliationState, step_name: str, thinking: str):
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
                "invoice_amount": state.get("invoice_amount", ""),
                "spreadsheet_amount": state.get("spreadsheet_amount", ""),
                "verdict": state.get("verdict", "")
            }
        })
        
        return state
    
    def parse_amounts_node(self, state: ReconciliationState) -> ReconciliationState:
        """LangGraph Node 1: Parse and extract numerical amounts from both sources."""
        state["workflow_step"] = "parse_amounts"
        
        thinking = f"""
🔍 AMOUNT PARSING
================
Invoice Data: {state.get('invoice_amount', 'Not provided')}
Spreadsheet Data: {state.get('spreadsheet_amount', 'Not provided')}

Extracting numerical values for comparison...
"""
        
        try:
            invoice_amount = state.get("invoice_amount", "")
            spreadsheet_amount = state.get("spreadsheet_amount", "")
            
            # Extract numerical values from invoice amount
            invoice_number = self._extract_number(invoice_amount)
            thinking += f"• Invoice amount extracted: {invoice_number}\n"
            
            # Extract numerical values from spreadsheet amount
            spreadsheet_number = self._extract_number(spreadsheet_amount)
            thinking += f"• Spreadsheet amount extracted: {spreadsheet_number}\n"
            
            # Store parsed amounts back to state
            state["invoice_amount"] = str(invoice_number) if invoice_number is not None else "0"
            state["spreadsheet_amount"] = str(spreadsheet_number) if spreadsheet_number is not None else "0"
            
            thinking += "\n✅ Amount parsing completed\n"
            
        except Exception as e:
            thinking += f"\n❌ Error during amount parsing: {str(e)}\n"
            state["error"] = str(e)
        
        return self._log_thinking(state, "parsing", thinking)
    
    def compare_amounts_node(self, state: ReconciliationState) -> ReconciliationState:
        """LangGraph Node 2: Compare the extracted amounts and determine match."""
        state["workflow_step"] = "compare_amounts"
        
        thinking = f"""
⚖️ AMOUNT COMPARISON
===================
Invoice Amount: ${state.get('invoice_amount', '0')}
Spreadsheet Amount: ${state.get('spreadsheet_amount', '0')}

Performing comparison analysis...
"""
        
        try:
            invoice_val = float(state.get("invoice_amount", "0"))
            spreadsheet_val = float(state.get("spreadsheet_amount", "0"))
            
            thinking += f"• Invoice numerical value: {invoice_val:,.2f}\n"
            thinking += f"• Spreadsheet numerical value: {spreadsheet_val:,.2f}\n"
            
            # Calculate difference
            difference = abs(invoice_val - spreadsheet_val)
            percentage_diff = (difference / max(invoice_val, spreadsheet_val)) * 100 if max(invoice_val, spreadsheet_val) > 0 else 0
            
            thinking += f"• Absolute difference: ${difference:,.2f}\n"
            thinking += f"• Percentage difference: {percentage_diff:.2f}%\n"
            
            # Determine if amounts match (within 1% tolerance for rounding)
            tolerance = 0.01  # 1% tolerance
            amounts_match = percentage_diff <= tolerance
            
            thinking += f"• Tolerance threshold: {tolerance*100}%\n"
            thinking += f"• Amounts match: {amounts_match}\n"
            
            # Create comparison result
            if amounts_match:
                comparison_result = f"MATCH: Invoice amount ${invoice_val:,.2f} matches spreadsheet amount ${spreadsheet_val:,.2f} (difference: ${difference:,.2f})"
            else:
                comparison_result = f"MISMATCH: Invoice amount ${invoice_val:,.2f} does not match spreadsheet amount ${spreadsheet_val:,.2f} (difference: ${difference:,.2f}, {percentage_diff:.2f}%)"
            
            state["reconciliation_result"] = comparison_result
            thinking += f"\n📊 Comparison result: {comparison_result}\n"
            
        except Exception as e:
            thinking += f"\n❌ Error during amount comparison: {str(e)}\n"
            state["error"] = str(e)
            state["reconciliation_result"] = f"Error comparing amounts: {str(e)}"
        
        return self._log_thinking(state, "comparison", thinking)
    
    def generate_verdict_node(self, state: ReconciliationState) -> ReconciliationState:
        """LangGraph Node 3: Generate final YES/NO verdict with reasoning."""
        state["workflow_step"] = "generate_verdict"
        
        thinking = f"""
⚖️ VERDICT GENERATION
====================
Reconciliation Result: {state.get('reconciliation_result', 'No result')}

Generating final verdict...
"""
        
        try:
            reconciliation_result = state.get("reconciliation_result", "")
            
            # Determine verdict based on comparison result
            if "MATCH" in reconciliation_result:
                verdict = "YES"
                reasoning = "The amounts from the invoice and spreadsheet match within acceptable tolerance."
            elif "MISMATCH" in reconciliation_result:
                verdict = "NO"
                reasoning = "The amounts from the invoice and spreadsheet do not match. Investigation required."
            else:
                verdict = "INCONCLUSIVE"
                reasoning = "Unable to determine match due to data processing errors."
            
            thinking += f"• Final verdict: {verdict}\n"
            thinking += f"• Reasoning: {reasoning}\n"
            
            # Create comprehensive verdict statement
            verdict_statement = f"""
RECONCILIATION VERDICT: {verdict}

ANALYSIS:
{reasoning}

DETAILS:
{reconciliation_result}

RECOMMENDATION:
{self._get_recommendation(verdict)}
"""
            
            state["verdict"] = verdict_statement
            thinking += "\n✅ Verdict generation completed\n"
            
        except Exception as e:
            thinking += f"\n❌ Error during verdict generation: {str(e)}\n"
            state["error"] = str(e)
            state["verdict"] = f"Error generating verdict: {str(e)}"
        
        return self._log_thinking(state, "verdict", thinking)
    
    def _extract_number(self, text):
        """Extract numerical value from text, handling currency and formatting."""
        if not text or text == "":
            return None
        
        try:
            # Remove common currency symbols and formatting
            cleaned = str(text).replace('$', '').replace(',', '').replace('€', '').replace('£', '').strip()
            
            # Find numerical patterns
            number_pattern = r'[-+]?\d*\.?\d+'
            matches = re.findall(number_pattern, cleaned)
            
            if matches:
                # Take the largest number found (likely the main amount)
                numbers = [float(match) for match in matches if match]
                return max(numbers) if numbers else None
            
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _get_recommendation(self, verdict):
        """Get recommendation based on verdict."""
        if verdict == "YES":
            return "Amounts are reconciled. Proceed with processing."
        elif verdict == "NO":
            return "Amounts do not match. Review source documents and resolve discrepancies before proceeding."
        else:
            return "Manual review required to determine data accuracy."
    
    def _build_workflow(self):
        """Build the LangGraph workflow with proper state transitions and tracing."""
        workflow = StateGraph(ReconciliationState)
        
        # Add nodes to the workflow
        workflow.add_node("parse_amounts", self.parse_amounts_node)
        workflow.add_node("compare_amounts", self.compare_amounts_node)
        workflow.add_node("generate_verdict", self.generate_verdict_node)
        
        # Define the workflow edges (state transitions)
        workflow.set_entry_point("parse_amounts")
        workflow.add_edge("parse_amounts", "compare_amounts")
        workflow.add_edge("compare_amounts", "generate_verdict")
        workflow.add_edge("generate_verdict", END)
        
        # Compile the workflow with tracing enabled
        return workflow.compile()
    
    def reconcile_amounts(self, invoice_amount: str, spreadsheet_amount: str):
        """Reconcile amounts using LangGraph workflow with advanced tracing."""
        # Create new trace
        trace_id = self._create_trace_id()
        
        # Reset live thinking
        self.live_thinking = {
            "parsing": "",
            "comparison": "",
            "verdict": ""
        }
        
        # Initialize LangGraph state
        initial_state: ReconciliationState = {
            "invoice_amount": invoice_amount,
            "spreadsheet_amount": spreadsheet_amount,
            "reconciliation_result": "",
            "verdict": "",
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
                self.trace_data[self.current_trace_id]["result"] = final_state.get("verdict", "")
                self.trace_data[self.current_trace_id]["final_state"] = {
                    "workflow_step": final_state.get("workflow_step", ""),
                    "has_error": bool(final_state.get("error", "")),
                    "verdict": final_state.get("verdict", ""),
                    "reconciliation_result": final_state.get("reconciliation_result", "")
                }
            
            return final_state.get("verdict", "")
            
        except Exception as e:
            if self.current_trace_id:
                self.trace_data[self.current_trace_id]["end_time"] = datetime.now().isoformat()
                self.trace_data[self.current_trace_id]["error"] = str(e)
            return f"Error during reconciliation: {str(e)}"
    
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
            file_path = f"output/{trace_id}_reconciliation_enhanced.json"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Add workflow metrics to export
        enhanced_export = {
            "trace_data": trace,
            "workflow_metrics": self.get_workflow_metrics(),
            "export_timestamp": datetime.now().isoformat(),
            "langraph_version": "reconciliation_enhanced_tracing"
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