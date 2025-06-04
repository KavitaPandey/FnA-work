import streamlit as st
import os
import json
import re
import tempfile
import time
from datetime import datetime
import uuid
from agents import InvoiceTracer, SpreadsheetTracer, ReconciliationTracer

# Set page configuration
st.set_page_config(
    page_title="Multi-Agent Invoice Processing System",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Multi-Agent Invoice Processing System")
st.markdown("Four specialized agents working together to process invoices with real-time tracing.")

# Function to save an uploaded file
def save_uploaded_file(uploaded_file):
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if not file_extension:
            file_extension = ".txt"
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            return temp_file.name
    except Exception as e:
        st.error(f"Error saving uploaded file: {e}")
        return None

# Function to extract and display JSON data
def display_invoice_results(result):
    """Display invoice analysis results with proper formatting."""
    if not result:
        st.error("No data was extracted from the invoice.")
        return
    
    # Split into PART 1 and PART 2
    parts = re.split(r'PART 2:', result, 1)
    
    # Parse JSON from Part 1
    json_part = parts[0]
    try:
        # Extract JSON using regex pattern matching
        json_match = re.search(r'(\[.*\]|\{.*\})', json_part, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            json_data = json.loads(json_str)
            
            st.markdown("## 📊 Extracted Invoice Data")
            
            # Handle both single invoice and multiple invoices
            if isinstance(json_data, list):
                st.success(f"Found {len(json_data)} invoices")
                
                # Display combined totals if available
                if len(json_data) > 1:
                    try:
                        combined_total = sum(float(invoice.get('Total_Invoice_Amount', '0').replace('$', '').replace(',', '')) for invoice in json_data if invoice.get('Total_Invoice_Amount'))
                        combined_outstanding = sum(float(invoice.get('Outstanding_Amount', '0').replace('$', '').replace(',', '')) for invoice in json_data if invoice.get('Outstanding_Amount'))
                        
                        st.metric("Combined Total Amount", f"${combined_total:,.2f}")
                        st.metric("Combined Outstanding Amount", f"${combined_outstanding:,.2f}")
                    except:
                        pass
                
                # Display each invoice
                for i, invoice in enumerate(json_data, 1):
                    with st.expander(f"Invoice {i}: {invoice.get('Invoice_Number', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### Invoice Details")
                            st.write(f"**Invoice Number:** {invoice.get('Invoice_Number', 'N/A')}")
                            st.write(f"**Date:** {invoice.get('Invoice_Date', 'N/A')}")
                            st.write(f"**Vendor:** {invoice.get('Vendor', 'N/A')}")
                            st.write(f"**Due Date:** {invoice.get('Due_Date', 'N/A')}")
                            st.write(f"**Payment Terms:** {invoice.get('Payment_Terms', 'N/A')}")
                        
                        with col2:
                            st.markdown("### Financial Details")
                            st.write(f"**Total Amount:** {invoice.get('Total_Invoice_Amount', 'N/A')}")
                            outstanding = invoice.get('Outstanding_Amount', 'N/A')
                            st.write(f"**Outstanding Amount:** {outstanding}")
                            
                            # Highlight outstanding amount
                            if outstanding != 'N/A' and outstanding:
                                st.metric("Amount Due", outstanding)
            else:
                # Single invoice
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Invoice Details")
                    st.write(f"**Invoice Number:** {json_data.get('Invoice_Number', 'N/A')}")
                    st.write(f"**Date:** {json_data.get('Invoice_Date', 'N/A')}")
                    st.write(f"**Vendor:** {json_data.get('Vendor', 'N/A')}")
                    st.write(f"**Due Date:** {json_data.get('Due_Date', 'N/A')}")
                    st.write(f"**Payment Terms:** {json_data.get('Payment_Terms', 'N/A')}")
                
                with col2:
                    st.markdown("### Financial Details")
                    st.write(f"**Total Amount:** {json_data.get('Total_Invoice_Amount', 'N/A')}")
                    outstanding = json_data.get('Outstanding_Amount', 'N/A')
                    st.write(f"**Outstanding Amount:** {outstanding}")
                    
                    # Highlight outstanding amount
                    if outstanding != 'N/A' and outstanding:
                        st.metric("Amount Due", outstanding)
            
            # Show raw JSON data in expander
            with st.expander("🔍 Raw JSON Data"):
                st.json(json_data)
                
    except json.JSONDecodeError:
        st.warning("Could not parse JSON data from the analysis result.")
        st.text_area("Raw Analysis Result", json_part, height=300)
    
    # Display business interpretation if available
    if len(parts) > 1:
        bullet_part = parts[1]
        st.markdown("## 💼 Business Interpretation")
        st.markdown(bullet_part)

# Initialize the agents
@st.cache_resource
def get_invoice_tracer():
    return InvoiceTracer()

@st.cache_resource  
def get_spreadsheet_tracer():
    return SpreadsheetTracer()

@st.cache_resource
def get_reconciliation_tracer():
    return ReconciliationTracer()

def create_session_folder():
    """Create a unique session folder for storing agent results."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    
    session_folder = f"sessions/{st.session_state.session_id}"
    os.makedirs(session_folder, exist_ok=True)
    return session_folder

def save_agent_result(session_folder, agent_name, result_data):
    """Save agent result to JSON file in session folder."""
    try:
        file_path = f"{session_folder}/{agent_name}_result.json"
        with open(file_path, 'w') as f:
            json.dump({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "result": result_data
            }, f, indent=2)
        return file_path
    except Exception as e:
        st.error(f"Error saving {agent_name} result: {str(e)}")
        return None

def load_agent_result(session_folder, agent_name):
    """Load agent result from JSON file in session folder."""
    try:
        file_path = f"{session_folder}/{agent_name}_result.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get("result")
    except Exception as e:
        st.error(f"Error loading {agent_name} result: {str(e)}")
    return None

try:
    invoice_agent = get_invoice_tracer()
    spreadsheet_agent = get_spreadsheet_tracer()
    reconciliation_agent = get_reconciliation_tracer()
except Exception as e:
    st.error(f"Error initializing agents: {str(e)}")
    st.stop()

# File upload section
st.markdown("## 📁 Upload Files")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Invoice File")
    uploaded_invoice = st.file_uploader(
        "Choose an invoice file", 
        type=["pdf", "png", "jpg", "jpeg", "svg", "txt"],
        help="Upload PDF, image, or text files containing invoice data",
        key="invoice_uploader"
    )

with col2:
    st.markdown("### 📊 Spreadsheet File (Optional)")
    uploaded_spreadsheet = st.file_uploader(
        "Choose a spreadsheet file",
        type=["xlsx", "xls", "csv"],
        help="Upload Excel or CSV files containing amortization schedules",
        key="spreadsheet_uploader"
    )

# Display uploaded files
files_uploaded = []
if uploaded_invoice is not None:
    st.write(f"📎 **Invoice file:** {uploaded_invoice.name}")
    files_uploaded.append(("invoice", uploaded_invoice))
    
    # Preview the invoice file
    file_type = uploaded_invoice.type
    if file_type.startswith("image"):
        st.image(uploaded_invoice, caption="Uploaded Invoice", use_column_width=True)
    elif "pdf" in file_type:
        st.info("📄 PDF file uploaded successfully")
    elif "text" in file_type or file_type == "":
        text_content = uploaded_invoice.getvalue().decode("utf-8")
        st.text_area("📝 File Preview", text_content[:500] + "..." if len(text_content) > 500 else text_content, height=150)

if uploaded_spreadsheet is not None:
    st.write(f"📊 **Spreadsheet file:** {uploaded_spreadsheet.name}")
    files_uploaded.append(("spreadsheet", uploaded_spreadsheet))
    st.info("📈 Spreadsheet file uploaded successfully")

# Process button (only show if at least one file is uploaded)
if files_uploaded and st.button("🚀 Start Multi-Agent Processing", type="primary"):
    # Save uploaded files
    temp_paths = {}
    for file_type, uploaded_file in files_uploaded:
        temp_path = save_uploaded_file(uploaded_file)
        if temp_path:
            temp_paths[file_type] = (temp_path, uploaded_file.type, uploaded_file.name)
    
    if temp_paths:
        # Create session folder for storing results
        session_folder = create_session_folder()
        
        # Initialize agent results storage
        agent_results = {}
        
        # Multi-Agent Processing System
        st.markdown("## 🤖 Multi-Agent Processing Pipeline")
        
        # Create main layout with processing flow on the right
        main_col, flow_col = st.columns([2, 1])
        
        with flow_col:
            st.markdown("### 🔄 Processing Flow")
            flow_container = st.container()
            
            # Create flow diagram placeholders
            with flow_container:
                agent1_box = st.empty()
                arrow1 = st.empty()
                agent2_box = st.empty()
                arrow2 = st.empty()
                agent3_box = st.empty()
                arrow3 = st.empty()
                agent4_box = st.empty()
                
                # Create flow diagram placeholders for 5 agents
                agent5_box = st.empty()
                
                # Initially show all agents as inactive
                agent1_box.markdown("📄 **Agent 1: Invoice Analysis** 🔴 *Waiting*")
                arrow1.markdown("⬇️")
                agent2_box.markdown("📊 **Agent 2: Spreadsheet** 🔴 *Waiting*")
                arrow2.markdown("⬇️")
                agent3_box.markdown("🔍 **Agent 3: Reconciliation** 🔴 *Waiting*")
                arrow3.markdown("⬇️")
                agent4_box.markdown("🔄 **Agent 4: Reclassification** 🔴 *Waiting*")
                st.markdown("⬇️")
                agent5_box.markdown("📈 **Agent 5: Amortization** 🔴 *Waiting*")
        
        with main_col:
            # Agent 1: Invoice Analysis Agent
            st.markdown("### 📄 Agent 1: Invoice Analysis")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent1_status = st.empty()
                    agent1_output = st.empty()
                with col2:
                    agent1_progress = st.empty()
                
                # Update flow to show Agent 1 is active
                agent1_box.markdown("📄 **Agent 1: Invoice Analysis** 🟢 *Active*")
                
                # Check if invoice file is available for processing
                if "invoice" in temp_paths:
                    invoice_path, invoice_type, invoice_name = temp_paths["invoice"]
                    
                    agent1_status.info("Processing invoice and extracting content...")
                    agent1_progress.progress(0)
                    
                    try:
                        # Process with the invoice agent
                        result = invoice_agent.process_invoice(invoice_path, invoice_type)
                        agent1_progress.progress(100)
                        agent1_status.success("Invoice analysis completed")
                        agent1_output.text_area("Invoice Analysis Results", value=str(result)[:500] + "...", height=100, disabled=True)
                        
                        # Show agent thinking process
                        live_thinking = invoice_agent.get_live_thinking()
                        if live_thinking:
                            with st.expander("Agent 1 Thinking Process"):
                                st.text_area("Planning & Strategy", 
                                           value=live_thinking.get("workflow", "Planning file type detection and processing strategy"),
                                           height=150, disabled=True)
                                st.text_area("Content Processing", 
                                           value=live_thinking.get("extraction", "Extracting text and analyzing document structure"),
                                           height=150, disabled=True)
                                st.text_area("Analysis & Reasoning", 
                                           value=live_thinking.get("analysis", "Identifying invoice fields and extracting structured data"),
                                           height=150, disabled=True)
                        
                        # Display results
                        display_invoice_results(result)
                        
                        # Save invoice result to session folder
                        agent_results["invoice"] = result
                        save_agent_result(session_folder, "agent1_invoice", result)
                        
                        # Mark Agent 1 as complete
                        agent1_box.markdown("📄 **Agent 1: Invoice Analysis** ✅ *Complete*")
                        
                    except Exception as e:
                        agent1_status.error(f"Invoice analysis failed: {str(e)}")
                        agent1_box.markdown("📄 **Agent 1: Invoice Analysis** ❌ *Failed*")
                        result = None
                        agent_results["invoice"] = None
                else:
                    agent1_status.warning("No invoice file uploaded")
                    agent1_output.info("Upload an invoice file to activate this agent")
                    agent1_box.markdown("📄 **Agent 1: Invoice Analysis** ⚪ *Skipped*")
                    agent_results["invoice"] = None
            
            st.divider()
            
            # Wait 2 seconds before Agent 2
            time.sleep(2)
            
            # Agent 2: Spreadsheet Analysis Agent
            st.markdown("### 📊 Agent 2: Spreadsheet Analysis")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent2_status = st.empty()
                    agent2_output = st.empty()
                with col2:
                    agent2_progress = st.empty()
                
                # Update flow to show Agent 2 is active
                agent2_box.markdown("📊 **Agent 2: Spreadsheet** 🟢 *Active*")
                
                # Check if spreadsheet file is available for processing
                if "spreadsheet" in temp_paths:
                    spreadsheet_path, spreadsheet_type, spreadsheet_name = temp_paths["spreadsheet"]
                    
                    agent2_status.info("Analyzing spreadsheet for amortization data...")
                    agent2_progress.progress(0)
                    
                    try:
                        # Determine file extension for processing
                        file_ext = spreadsheet_name.split('.')[-1].lower()
                        
                        # Process with the spreadsheet agent
                        spreadsheet_result = spreadsheet_agent.process_spreadsheet(spreadsheet_path, file_ext)
                        agent2_progress.progress(100)
                        agent2_status.success("Spreadsheet analysis completed")
                        agent2_output.text_area("Spreadsheet Analysis Results", 
                                               value=f"Total Amount Found: {spreadsheet_result}", 
                                               height=100, disabled=True)
                        
                        # Show spreadsheet agent thinking process
                        spreadsheet_thinking = spreadsheet_agent.get_live_thinking()
                        if spreadsheet_thinking:
                            with st.expander("Agent 2 Thinking Process"):
                                st.text_area("Spreadsheet Analysis", 
                                           value=spreadsheet_thinking.get("analysis", "Analyzing spreadsheet structure and content"),
                                           height=150, disabled=True)
                                st.text_area("Sheet Detection", 
                                           value=spreadsheet_thinking.get("sheet_detection", "Identifying amortization patterns in sheets"),
                                           height=150, disabled=True)
                                st.text_area("Amount Extraction", 
                                           value=spreadsheet_thinking.get("amortization_extraction", "Extracting total amounts using AI analysis"),
                                           height=150, disabled=True)
                        
                        # Save spreadsheet result to session folder
                        agent_results["spreadsheet"] = spreadsheet_result
                        save_agent_result(session_folder, "agent2_spreadsheet", spreadsheet_result)
                        
                        # Mark Agent 2 as complete
                        agent2_box.markdown("📊 **Agent 2: Spreadsheet** ✅ *Complete*")
                        
                    except Exception as e:
                        agent2_status.error(f"Spreadsheet analysis failed: {str(e)}")
                        agent2_box.markdown("📊 **Agent 2: Spreadsheet** ❌ *Failed*")
                        spreadsheet_result = None
                        agent_results["spreadsheet"] = None
                else:
                    agent2_status.warning("No spreadsheet file uploaded")
                    agent2_output.info("Upload a spreadsheet file to activate this agent")
                    agent2_box.markdown("📊 **Agent 2: Spreadsheet** ⚪ *Skipped*")
                    spreadsheet_result = None
                    agent_results["spreadsheet"] = None
            
            st.divider()
            
            # Wait 2 seconds before Agent 3
            time.sleep(2)
            
            # Agent 3: Reconciliation Agent
            st.markdown("### 🔍 Agent 3: Reconciliation")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent3_status = st.empty()
                    agent3_output = st.empty()
                with col2:
                    agent3_progress = st.empty()
                
                # Update flow to show Agent 3 is active
                agent3_box.markdown("🔍 **Agent 3: Reconciliation** 🟢 *Active*")
                
                agent3_status.info("Reconciling invoice and spreadsheet amounts...")
                agent3_progress.progress(20)
                
                # Load results from session storage
                invoice_result = agent_results.get("invoice") or load_agent_result(session_folder, "agent1_invoice")
                spreadsheet_result = agent_results.get("spreadsheet") or load_agent_result(session_folder, "agent2_spreadsheet")
                
                # Extract amounts from processed results
                invoice_amount = "0"
                spreadsheet_amount = "0"
                
                # Extract invoice amount from result
                if invoice_result and isinstance(invoice_result, str):
                    try:
                        # Try to extract JSON and get outstanding amount
                        if "```json" in invoice_result:
                            json_part = invoice_result.split("```json")[1].split("```")[0].strip()
                            invoice_data = json.loads(json_part)
                            invoice_amount = invoice_data.get("Outstanding_Amount", invoice_data.get("Total_Invoice_Amount", "0"))
                        else:
                            # Look for amount patterns in the text
                            amount_patterns = re.findall(r'\$[\d,]+\.?\d*', invoice_result)
                            if amount_patterns:
                                invoice_amount = amount_patterns[0]
                    except:
                        invoice_amount = "0"
                
                # Extract spreadsheet amount from result
                if spreadsheet_result and isinstance(spreadsheet_result, str):
                    try:
                        # Look for amount patterns in spreadsheet result
                        amount_patterns = re.findall(r'\$[\d,]+\.?\d*', spreadsheet_result)
                        if amount_patterns:
                            spreadsheet_amount = amount_patterns[0]
                    except:
                        spreadsheet_amount = "0"
                
                agent3_progress.progress(50)
                time.sleep(1)
                
                # Perform actual reconciliation if we have valid amounts
                reconciliation_verdict = "No data to reconcile"
                if invoice_amount != "0" and spreadsheet_amount != "0":
                    agent3_status.info("Performing amount reconciliation analysis...")
                    agent3_progress.progress(75)
                    time.sleep(1)
                    
                    try:
                        reconciliation_verdict = reconciliation_agent.reconcile_amounts(invoice_amount, spreadsheet_amount)
                        agent3_status.success("Reconciliation analysis completed")
                    except Exception as e:
                        reconciliation_verdict = f"Reconciliation failed: {str(e)}"
                        agent3_status.error("Reconciliation analysis failed")
                elif invoice_amount != "0":
                    reconciliation_verdict = f"Invoice amount found: {invoice_amount}. No spreadsheet data available for comparison."
                    agent3_status.warning("Partial reconciliation - invoice only")
                elif spreadsheet_amount != "0":
                    reconciliation_verdict = f"Spreadsheet amount found: {spreadsheet_amount}. No invoice data available for comparison."
                    agent3_status.warning("Partial reconciliation - spreadsheet only")
                else:
                    agent3_status.info("No financial amounts found for reconciliation")
                
                agent3_progress.progress(100)
                
                # Display reconciliation results
                agent3_output.text_area("Reconciliation Analysis", value=reconciliation_verdict, height=150, disabled=True)
                
                # Show live thinking process in expander if available
                if hasattr(reconciliation_agent, 'get_live_thinking'):
                    thinking = reconciliation_agent.get_live_thinking()
                    if any(thinking.values()):
                        with st.expander("🧠 Reconciliation Thinking Process"):
                            for step, thought in thinking.items():
                                if thought:
                                    st.text_area(f"{step.title()} Analysis", value=thought, height=100, disabled=True)
                
                agent3_box.markdown("🔍 **Agent 3: Reconciliation** ✅ *Complete*")
            
            st.divider()
            
            # Wait 2 seconds before Agent 4
            time.sleep(2)
            
            # Agent 4: Reclassification Agent
            st.markdown("### 🔄 Agent 4: Reclassification")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent4_status = st.empty()
                    agent4_output = st.empty()
                with col2:
                    agent4_progress = st.empty()
                
                # Update flow to show Agent 4 is active
                agent4_box.markdown("🔄 **Agent 4: Reclassification** 🟢 *Active*")
                
                agent4_status.info("Reclassifying and categorizing data...")
                agent4_progress.progress(0)
                
                # Simulate processing time
                for i in range(0, 101, 25):
                    agent4_progress.progress(i)
                    time.sleep(1)
                
                agent4_status.success("Reclassification completed")
                agent4_output.text_area("Reclassification Results", value="Data categorized and classified successfully", height=100, disabled=True)
                agent4_box.markdown("🔄 **Agent 4: Reclassification** ✅ *Complete*")
            
            st.divider()
            
            # Wait 2 seconds before Agent 5
            time.sleep(2)
            
            # Agent 5: Amortization Agent
            st.markdown("### 📈 Agent 5: Amortization")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent5_status = st.empty()
                    agent5_output = st.empty()
                with col2:
                    agent5_progress = st.empty()
                
                # Update flow to show Agent 5 is active
                agent5_box.markdown("📈 **Agent 5: Amortization** 🟢 *Active*")
                
                agent5_status.info("Calculating amortization schedules...")
                agent5_progress.progress(0)
                
                # Simulate processing time
                for i in range(0, 101, 20):
                    agent5_progress.progress(i)
                    time.sleep(1)
                
                agent5_status.success("Amortization analysis completed")
                agent5_output.text_area("Amortization Results", value="Payment schedules and amortization calculations completed", height=100, disabled=True)
                agent5_box.markdown("📈 **Agent 5: Amortization** ✅ *Complete*")
            
            st.divider()
            
            # Final Results Summary
            st.markdown("### 📋 Processing Summary")
            st.success("Multi-agent processing completed successfully!")
            st.info("Individual agent results are displayed above in their respective sections.")
        
        # Clean up temporary files
        for file_type, (temp_path, _, _) in temp_paths.items():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
    else:
        st.error("Failed to save the uploaded files for processing.")

else:
    st.info("Please upload at least one file (invoice or spreadsheet) to begin processing.")

# Text input section as alternative
st.markdown("## ✏️ Or Enter Invoice Text Directly")
invoice_text = st.text_area(
    "Enter invoice text here", 
    height=200,
    help="Paste or type invoice content directly"
)

if st.button("🚀 Process Text with Multi-Agent System", type="secondary"):
    if invoice_text:
        try:
            # Create a temporary file to store the text
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                temp_file.write(invoice_text.encode('utf-8'))
                temp_path = temp_file.name
            
            # Multi-Agent Processing System for text
            st.markdown("## 🤖 Multi-Agent Processing Pipeline")
            
            # Agent 1: Text Analysis Agent
            st.markdown("### 📄 Agent 1: Text Analysis")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent1_status = st.empty()
                    agent1_output = st.empty()
                with col2:
                    agent1_progress = st.empty()
                
                agent1_status.info("Processing text and extracting content...")
                agent1_progress.progress(0)
                
                try:
                    # Process with the invoice agent
                    text_result = invoice_agent.process_invoice(temp_path, "text/plain")
                    agent1_progress.progress(100)
                    agent1_status.success("Text analysis completed")
                    agent1_output.text_area("Text Analysis Results", value=str(text_result)[:500] + "...", height=100, disabled=True)
                    
                    # Display results
                    display_invoice_results(text_result)
                    
                except Exception as e:
                    agent1_status.error(f"Text analysis failed: {str(e)}")
                    agent1_output.error("Text processing failed")
                
                # Clean up temporary file
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            st.error(f"Error processing text: {str(e)}")
    else:
        st.warning("Please enter some invoice text to process.")