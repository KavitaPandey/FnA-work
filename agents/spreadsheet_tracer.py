"""
LangGraph Spreadsheet Analyzer with Advanced Tracing and Observability
Specialized agent for processing spreadsheets and extracting amortization data
"""

import os
import yaml
import json
import pandas as pd
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
                "system_role": "You are an AI assistant that specializes in analyzing spreadsheet data, particularly amortization schedules and financial calculations."
            }
        }

# Define the state structure for LangGraph
class SpreadsheetState(TypedDict):
    """State structure for the spreadsheet processing workflow."""
    file_path: str
    file_type: str
    sheet_data: Dict[str, Any]
    amortization_data: Dict[str, Any]
    total_amount: str
    thinking_log: Dict[str, str]
    trace_id: str
    workflow_step: str
    error: str

class SpreadsheetTracer:
    """LangGraph-powered spreadsheet analyzer with advanced tracing and observability."""
    
    def __init__(self, config_path="config.yml"):
        """Initialize the LangGraph-based spreadsheet tracer."""
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
            "analysis": "",
            "sheet_detection": "",
            "amortization_extraction": ""
        }
    
    def _is_convertible_to_number(self, value):
        """Check if a string value can be converted to a number."""
        if pd.isna(value) or value == '':
            return False
        try:
            # Clean common formatting characters
            cleaned = str(value).replace('$', '').replace(',', '').replace('%', '').strip()
            if cleaned and cleaned != 'nan':
                float(cleaned)
                return True
        except (ValueError, AttributeError):
            pass
        return False
    
    def _create_trace_id(self):
        """Create a unique trace ID for this run."""
        self.current_trace_id = f"spreadsheet_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace_data[self.current_trace_id] = {
            "workflow_steps": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "result": None,
            "state_transitions": []
        }
        return self.current_trace_id
    
    def _log_thinking(self, state: SpreadsheetState, step_name: str, thinking: str):
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
                "has_sheet_data": bool(state.get("sheet_data", {})),
                "has_amortization_data": bool(state.get("amortization_data", {})),
                "total_amount": state.get("total_amount", "")
            }
        })
        
        return state
    
    def analyze_spreadsheet_node(self, state: SpreadsheetState) -> SpreadsheetState:
        """LangGraph Node 1: Analyze spreadsheet file and load data."""
        state["workflow_step"] = "analyze_spreadsheet"
        
        thinking = f"""
📊 SPREADSHEET ANALYSIS
======================
File: {state['file_path']}
Type: {state['file_type']}

Planning analysis approach:
• Excel files → Read all sheets, identify structure
• CSV files → Load data and analyze columns
• Detecting amortization patterns → Payment schedules, principal/interest breakdowns
• Looking for financial data indicators → Balance, payment amounts, dates

Loading spreadsheet data...
"""
        
        try:
            sheet_data = {}
            
            if state['file_type'].lower() in ['xlsx', 'xls']:
                thinking += "🔧 Excel Processing:\n"
                thinking += "• Reading Excel file with pandas\n"
                thinking += "• Discovering available sheets\n"
                
                # Read Excel file and get all sheet names
                excel_file = pd.ExcelFile(state['file_path'])
                sheet_names = excel_file.sheet_names
                
                thinking += f"• Found {len(sheet_names)} sheets: {', '.join(sheet_names)}\n"
                
                # Load data from each sheet with numerical analysis
                for sheet_name in sheet_names:
                    df = pd.read_excel(state['file_path'], sheet_name=sheet_name)
                    
                    # Analyze numerical columns and detect totals/balances
                    numerical_columns = []
                    total_columns = []
                    for col in df.columns:
                        # Check if column contains numerical data
                        numeric_count = df[col].apply(lambda x: pd.api.types.is_numeric_dtype(type(x)) or 
                                                     (isinstance(x, str) and self._is_convertible_to_number(x))).sum()
                        if numeric_count > len(df) * 0.3:  # More than 30% numerical
                            numerical_columns.append(col)
                        
                        # Check for total/balance keywords in column names
                        col_lower = str(col).lower()
                        if any(keyword in col_lower for keyword in ['total', 'balance', 'amount', 'sum', 'outstanding']):
                            total_columns.append(col)
                    
                    sheet_data[sheet_name] = {
                        "columns": df.columns.tolist(),
                        "shape": df.shape,
                        "sample_data": df.head().to_dict(),
                        "data": df.to_dict(),
                        "numerical_columns": numerical_columns,
                        "total_columns": total_columns,
                        "numerical_score": len(numerical_columns)
                    }
                    thinking += f"  - {sheet_name}: {df.shape[0]} rows × {df.shape[1]} columns, {len(numerical_columns)} numerical cols\n"
                
            elif state['file_type'].lower() == 'csv':
                thinking += "📄 CSV Processing:\n"
                thinking += "• Reading CSV file with pandas\n"
                
                df = pd.read_csv(state['file_path'])
                
                # Analyze numerical columns for CSV
                numerical_columns = []
                total_columns = []
                for col in df.columns:
                    # Check if column contains numerical data
                    numeric_count = df[col].apply(lambda x: pd.api.types.is_numeric_dtype(type(x)) or 
                                                 (isinstance(x, str) and self._is_convertible_to_number(x))).sum()
                    if numeric_count > len(df) * 0.3:  # More than 30% numerical
                        numerical_columns.append(col)
                    
                    # Check for total/balance keywords in column names
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in ['total', 'balance', 'amount', 'sum', 'outstanding']):
                        total_columns.append(col)
                
                sheet_data["Sheet1"] = {
                    "columns": df.columns.tolist(),
                    "shape": df.shape,
                    "sample_data": df.head().to_dict(),
                    "data": df.to_dict(),
                    "numerical_columns": numerical_columns,
                    "total_columns": total_columns,
                    "numerical_score": len(numerical_columns)
                }
                thinking += f"• Loaded: {df.shape[0]} rows × {df.shape[1]} columns, {len(numerical_columns)} numerical cols\n"
            
            thinking += "\n✅ Spreadsheet analysis completed\n"
            thinking += "🔍 Analyzing sheet structure for amortization patterns...\n"
            
            state["sheet_data"] = sheet_data
            
        except Exception as e:
            thinking += f"\n❌ Error during spreadsheet analysis: {str(e)}\n"
            state["error"] = str(e)
        
        return self._log_thinking(state, "analysis", thinking)
    
    def detect_amortization_sheet_node(self, state: SpreadsheetState) -> SpreadsheetState:
        """LangGraph Node 2: Detect which sheet contains amortization data."""
        state["workflow_step"] = "detect_amortization"
        
        thinking = f"""
🔍 AMORTIZATION SHEET DETECTION
==============================
Analyzing {len(state.get('sheet_data', {}))} sheets for amortization patterns...

Looking for indicators:
• Column names containing: payment, principal, interest, balance, rate
• Date columns for payment schedules
• Numerical data patterns consistent with loan amortization
• Total amounts and running balances

"""
        
        amortization_sheet = None
        amortization_indicators = {}
        
        try:
            for sheet_name, sheet_info in state.get("sheet_data", {}).items():
                thinking += f"\n📋 Analyzing sheet: {sheet_name}\n"
                
                columns = sheet_info.get("columns", [])
                column_text = " ".join(str(col).lower() for col in columns)
                data = sheet_info.get("data", {})
                
                # Score sheet based on keywords and data content
                score = 0
                indicators = []
                
                # Priority 1: Check sheet name for 'prepaid'
                sheet_name_lower = sheet_name.lower()
                if 'prepaid' in sheet_name_lower:
                    score += 10
                    indicators.append("prepaid_in_sheet_name")
                    thinking += f"  ⭐ HIGH PRIORITY: Sheet name contains 'prepaid'\n"
                
                # Priority 2: Check for key financial keywords in column names
                financial_keywords = [
                    'prepaid', 'payment', 'balance', 'principal', 'interest', 'rate',
                    'amortization', 'loan', 'schedule', 'amount', 'date', 'total'
                ]
                
                for keyword in financial_keywords:
                    if keyword in column_text:
                        if keyword in ['prepaid', 'payment', 'balance']:
                            score += 3  # Higher weight for priority keywords
                        else:
                            score += 1
                        indicators.append(f"column_{keyword}")
                
                # Priority 3: Search within cell values for keywords
                cell_keyword_matches = 0
                priority_keywords = ['prepaid', 'payment', 'balance']
                
                for col_name, col_data in data.items():
                    if isinstance(col_data, dict):
                        for cell_value in col_data.values():
                            if isinstance(cell_value, str):
                                cell_value_lower = cell_value.lower()
                                for keyword in priority_keywords:
                                    if keyword in cell_value_lower:
                                        cell_keyword_matches += 1
                                        indicators.append(f"cell_contains_{keyword}")
                                        break  # Count each cell only once
                
                if cell_keyword_matches > 0:
                    score += cell_keyword_matches * 2  # 2 points per matching cell
                    thinking += f"  📋 Found {cell_keyword_matches} cells containing priority keywords\n"
                
                thinking += f"  - Columns: {', '.join(str(col) for col in columns[:5])}{'...' if len(columns) > 5 else ''}\n"
                thinking += f"  - Amortization score: {score}/10\n"
                thinking += f"  - Found indicators: {', '.join(indicators)}\n"
                
                amortization_indicators[sheet_name] = {
                    "score": score,
                    "indicators": indicators,
                    "columns": columns
                }
                
                # Select sheet with highest score
                if score > 0 and (amortization_sheet is None or score > amortization_indicators[amortization_sheet]["score"]):
                    amortization_sheet = sheet_name
            
            if amortization_sheet:
                thinking += f"\n✅ Selected amortization sheet: '{amortization_sheet}'\n"
                thinking += f"   Best match with score: {amortization_indicators[amortization_sheet]['score']}\n"
            else:
                thinking += "\n⚠️ No clear amortization sheet detected\n"
                thinking += "   Will analyze first sheet with numerical data\n"
                # Fallback to first sheet with data
                if state.get("sheet_data"):
                    amortization_sheet = list(state["sheet_data"].keys())[0]
            
            state["amortization_data"] = {
                "selected_sheet": amortization_sheet,
                "sheet_analysis": amortization_indicators,
                "sheet_data": state["sheet_data"].get(amortization_sheet, {}) if amortization_sheet else {}
            }
            
        except Exception as e:
            thinking += f"\n❌ Error during sheet detection: {str(e)}\n"
            state["error"] = str(e)
        
        return self._log_thinking(state, "sheet_detection", thinking)
    
    def extract_total_amount_node(self, state: SpreadsheetState) -> SpreadsheetState:
        """LangGraph Node 3: Extract total amount from amortization data with numerical processing."""
        state["workflow_step"] = "extract_total"
        
        amortization_data = state.get("amortization_data", {})
        selected_sheet = amortization_data.get("selected_sheet", "")
        
        thinking = f"""
💰 TOTAL AMOUNT EXTRACTION
==========================
Analyzing sheet: '{selected_sheet}'
Processing numerical data to identify total amounts...

"""
        
        try:
            if not amortization_data or not selected_sheet:
                thinking += "❌ No amortization data available for analysis\n"
                state["total_amount"] = "Error: No amortization data found"
                return self._log_thinking(state, "amortization_extraction", thinking)
            
            sheet_data = amortization_data.get("sheet_data", {})
            columns = sheet_data.get("columns", [])
            data = sheet_data.get("data", {})
            numerical_columns = sheet_data.get("numerical_columns", [])
            total_columns = sheet_data.get("total_columns", [])
            
            thinking += f"• Columns available: {', '.join(str(col) for col in columns)}\n"
            thinking += f"• Numerical columns: {', '.join(numerical_columns)}\n"
            thinking += f"• Total-related columns: {', '.join(total_columns)}\n"
            
            # First, try to find explicit total amounts in total_columns
            found_totals = {}
            
            for col_name in total_columns:
                if col_name in data:
                    col_data = data[col_name]
                    thinking += f"\n🔢 Analyzing column '{col_name}':\n"
                    
                    # Extract numerical values from this column
                    numerical_values = []
                    for key, value in col_data.items():
                        if isinstance(value, (int, float)) and not pd.isna(value):
                            numerical_values.append(float(value))
                        elif isinstance(value, str) and self._is_convertible_to_number(value):
                            try:
                                cleaned = str(value).replace('$', '').replace(',', '').replace('%', '').strip()
                                numerical_values.append(float(cleaned))
                            except:
                                pass
                    
                    if numerical_values:
                        # Find the largest value (likely the total)
                        max_value = max(numerical_values)
                        sum_value = sum(numerical_values)
                        
                        thinking += f"  - Found {len(numerical_values)} numerical values\n"
                        thinking += f"  - Largest value: {max_value:,.2f}\n"
                        thinking += f"  - Sum of all values: {sum_value:,.2f}\n"
                        
                        found_totals[col_name] = {
                            "max_value": max_value,
                            "sum_value": sum_value,
                            "count": len(numerical_values)
                        }
            
            # If we found totals in dedicated columns, use the largest one
            if found_totals:
                best_total = max(found_totals.items(), key=lambda x: x[1]["max_value"])
                total_amount = best_total[1]["max_value"]
                total_column = best_total[0]
                
                thinking += f"\n✅ Found total amount: ${total_amount:,.2f}\n"
                thinking += f"   From column: '{total_column}'\n"
                
                state["total_amount"] = f"${total_amount:,.2f}"
            else:
                # Fallback: analyze all numerical columns for the largest values
                thinking += "\n🔍 No explicit total columns found, analyzing all numerical data...\n"
                
                all_values = []
                for col_name in numerical_columns:
                    if col_name in data:
                        col_data = data[col_name]
                        for value in col_data.values():
                            if isinstance(value, (int, float)) and not pd.isna(value):
                                all_values.append(float(value))
                            elif isinstance(value, str) and self._is_convertible_to_number(value):
                                try:
                                    cleaned = str(value).replace('$', '').replace(',', '').replace('%', '').strip()
                                    all_values.append(float(cleaned))
                                except:
                                    pass
                
                if all_values:
                    max_value = max(all_values)
                    thinking += f"  - Largest numerical value found: ${max_value:,.2f}\n"
                    state["total_amount"] = f"${max_value:,.2f}"
                else:
                    # Use AI analysis as final fallback
                    thinking += "\n🤖 Using AI analysis as fallback...\n"
                    ai_result = self._analyze_with_ai(selected_sheet, columns, sheet_data.get("sample_data", {}))
                    state["total_amount"] = ai_result
                    thinking += f"  - AI Result: {ai_result}\n"
            
        except Exception as e:
            thinking += f"\n❌ Error during total extraction: {str(e)}\n"
            state["error"] = str(e)
            state["total_amount"] = f"Error: {str(e)}"
        
        return self._log_thinking(state, "amortization_extraction", thinking)
    
    def _analyze_with_ai(self, sheet_name, columns, sample_data):
        """Fallback AI analysis for complex cases with prepaid focus."""
        try:
            ai_prompt = f"""
Analyze this spreadsheet data and extract the most significant total amount, with special focus on prepaid amounts.

Sheet: {sheet_name}
Columns: {', '.join(str(col) for col in columns)}
Sample Data: {json.dumps(sample_data, indent=2)}

Priority search order:
1. Look for any amounts related to "prepaid" entries
2. Look for "payment" amounts 
3. Look for "balance" amounts
4. Look for any total amounts

Search within:
- Column headers containing keywords: prepaid, payment, balance, total, amount
- Cell values containing text: prepaid, payment, balance
- Numerical values in cells adjacent to keyword cells

Return only the numerical total amount with currency symbol (e.g., "$1,234.56").
If multiple relevant amounts are found, return the largest one.
If no clear total is found, return "No clear total found".
"""

            response = self.client.chat.completions.create(
                model=self.config["openai"]["model"],
                messages=[
                    {"role": "system", "content": self.config["openai"]["system_role"]},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=self.config["openai"]["temperature"]
            )
            
            ai_result = response.choices[0].message.content or "No result from AI"
            return ai_result.strip()
            
        except Exception as e:
            return f"AI analysis failed: {str(e)}"
    
    def _build_workflow(self):
        """Build the LangGraph workflow with proper state transitions and tracing."""
        workflow = StateGraph(SpreadsheetState)
        
        # Add nodes to the workflow
        workflow.add_node("analyze_spreadsheet", self.analyze_spreadsheet_node)
        workflow.add_node("detect_amortization", self.detect_amortization_sheet_node)
        workflow.add_node("extract_total", self.extract_total_amount_node)
        
        # Define the workflow edges (state transitions)
        workflow.set_entry_point("analyze_spreadsheet")
        workflow.add_edge("analyze_spreadsheet", "detect_amortization")
        workflow.add_edge("detect_amortization", "extract_total")
        workflow.add_edge("extract_total", END)
        
        # Compile the workflow with tracing enabled
        return workflow.compile()
    
    def process_spreadsheet(self, file_path: str, file_type: str):
        """Process spreadsheet using LangGraph workflow with advanced tracing."""
        # Create new trace
        trace_id = self._create_trace_id()
        
        # Reset live thinking
        self.live_thinking = {
            "analysis": "",
            "sheet_detection": "",
            "amortization_extraction": ""
        }
        
        # Initialize LangGraph state
        initial_state: SpreadsheetState = {
            "file_path": file_path,
            "file_type": file_type,
            "sheet_data": {},
            "amortization_data": {},
            "total_amount": "",
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
                self.trace_data[self.current_trace_id]["result"] = final_state.get("total_amount", "")
                self.trace_data[self.current_trace_id]["final_state"] = {
                    "workflow_step": final_state.get("workflow_step", ""),
                    "has_error": bool(final_state.get("error", "")),
                    "sheets_analyzed": len(final_state.get("sheet_data", {})),
                    "selected_sheet": final_state.get("amortization_data", {}).get("selected_sheet", ""),
                    "total_amount": final_state.get("total_amount", "")
                }
            
            return final_state.get("total_amount", "")
            
        except Exception as e:
            if self.current_trace_id:
                self.trace_data[self.current_trace_id]["end_time"] = datetime.now().isoformat()
                self.trace_data[self.current_trace_id]["error"] = str(e)
            return f"Error processing spreadsheet: {str(e)}"
    
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
            file_path = f"output/{trace_id}_spreadsheet_enhanced.json"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Add workflow metrics to export
        enhanced_export = {
            "trace_data": trace,
            "workflow_metrics": self.get_workflow_metrics(),
            "export_timestamp": datetime.now().isoformat(),
            "langraph_version": "spreadsheet_enhanced_tracing"
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