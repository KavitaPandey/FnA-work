import streamlit as st
import os
import json
import re
import tempfile
import time
from datetime import datetime
from simple_tracer import InvoiceTracer
from spreadsheet_tracer import SpreadsheetTracer

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
            
            # Display structured data
            st.markdown("## 📊 Extracted Invoice Data")
            
            # Handle both single invoice (dict) and multiple invoices (list)
            if isinstance(json_data, list):
                # Multiple invoices
                total_outstanding = 0
                
                for i, invoice in enumerate(json_data):
                    with st.expander(f"📄 Invoice {i+1}: {invoice.get('invoice_number', 'N/A')}", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### Basic Information")
                            st.write(f"**Invoice Number:** {invoice.get('invoice_number', 'N/A')}")
                            st.write(f"**Date:** {invoice.get('date', 'N/A')}")
                            st.write(f"**Due Date:** {invoice.get('due_date', 'N/A')}")
                            st.write(f"**Vendor:** {invoice.get('vendor', 'N/A')}")
                        
                        with col2:
                            st.markdown("### Financial Details")
                            total_amount = invoice.get('total_amount', 'N/A')
                            outstanding_amount = invoice.get('outstanding_amount', 'N/A')
                            
                            st.write(f"**Total Amount:** {total_amount}")
                            st.write(f"**Outstanding Amount:** {outstanding_amount}")
                            
                            # Add to total outstanding if it's a valid number
                            if isinstance(outstanding_amount, (int, float)):
                                total_outstanding += outstanding_amount
                            elif isinstance(outstanding_amount, str) and outstanding_amount.replace('$', '').replace(',', '').replace('.', '').isdigit():
                                total_outstanding += float(outstanding_amount.replace('$', '').replace(',', ''))
                
                # Display combined total
                st.markdown("### 💰 Combined Total")
                st.metric("Total Outstanding Amount", f"${total_outstanding:,.2f}")
                
            else:
                # Single invoice
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Basic Information")
                    st.write(f"**Invoice Number:** {json_data.get('invoice_number', 'N/A')}")
                    st.write(f"**Date:** {json_data.get('date', 'N/A')}")
                    st.write(f"**Due Date:** {json_data.get('due_date', 'N/A')}")
                    st.write(f"**Vendor:** {json_data.get('vendor', 'N/A')}")
                    st.write(f"**Payment Terms:** {json_data.get('payment_terms', 'N/A')}")
                
                with col2:
                    st.markdown("### Financial Details")
                    st.write(f"**Total Amount:** {json_data.get('total_amount', 'N/A')}")
                    outstanding = json_data.get('outstanding_amount', 'N/A')
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

# Initialize the invoice tracer
@st.cache_resource
def get_invoice_tracer():
    return InvoiceTracer()

# Initialize the spreadsheet tracer
@st.cache_resource  
def get_spreadsheet_tracer():
    return SpreadsheetTracer()

try:
    invoice_agent = get_invoice_tracer()
    spreadsheet_agent = get_spreadsheet_tracer()
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
                
                # Initially show all agents as inactive
                agent1_box.markdown("📄 **Agent 1: PDF Analysis** 🔴 *Waiting*")
                arrow1.markdown("⬇️")
                agent2_box.markdown("📊 **Agent 2: Spreadsheet** 🔴 *Waiting*")
                arrow2.markdown("⬇️")
                agent3_box.markdown("🔄 **Agent 3: Reclassification** 🔴 *Waiting*")
                arrow3.markdown("⬇️")
                agent4_box.markdown("📈 **Agent 4: Amortization** 🔴 *Waiting*")
        
        with main_col:
            # Agent 1: PDF Analysis Agent
            st.markdown("### 📄 Agent 1: PDF Analysis")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    agent1_status = st.empty()
                    agent1_output = st.empty()
                with col2:
                    agent1_progress = st.empty()
                
                # Update flow to show Agent 1 is active
                agent1_box.markdown("📄 **Agent 1: PDF Analysis** 🟢 *Active*")
                
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
                        
                        # Mark Agent 1 as complete
                        agent1_box.markdown("📄 **Agent 1: PDF Analysis** ✅ *Complete*")
                        
                    except Exception as e:
                        agent1_status.error(f"Invoice analysis failed: {str(e)}")
                        agent1_box.markdown("📄 **Agent 1: PDF Analysis** ❌ *Failed*")
                        result = None
                else:
                    agent1_status.warning("No invoice file uploaded")
                    agent1_output.info("Upload an invoice file to activate this agent")
                    agent1_box.markdown("📄 **Agent 1: PDF Analysis** ⚪ *Skipped*")
            
            st.divider()
                
                # Wait 5 seconds before Agent 2
                time.sleep(5)
                
                # Agent 2: Spreadsheet Reading Agent
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
                    
                    agent2_status.info("Reading spreadsheet data and identifying amounts...")
                    agent2_progress.progress(0)
                    
                    # Simulate processing time
                    for i in range(0, 101, 20):
                        agent2_progress.progress(i)
                        time.sleep(3)
                    
                    agent2_status.success("Spreadsheet analysis ready (placeholder)")
                    agent2_output.text_area("Spreadsheet Analysis", value="Spreadsheet reading agent will be implemented here", height=100, disabled=True)
                    
                    # Show agent 2 thinking process
                    with st.expander("Agent 2 Thinking Process"):
                        st.text_area("Planning & Strategy", 
                                   value="Analyzing document structure for tabular data and numeric patterns",
                                   height=100, disabled=True)
                        st.text_area("Data Processing", 
                                   value="Identifying rows, columns, and monetary amounts in structured format",
                                   height=100, disabled=True)
                        st.text_area("Amount Extraction", 
                                   value="Cross-referencing invoice totals with spreadsheet calculations",
                                   height=100, disabled=True)
                    
                    # Mark Agent 2 as complete
                    agent2_box.markdown("📊 **Agent 2: Spreadsheet** ✅ *Complete*")
                
                st.divider()
                
                # Wait 5 seconds before Agent 3
                time.sleep(5)
                
                # Agent 3: Reclassification Agent
                st.markdown("### 🔄 Agent 3: Reclassification")
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        agent3_status = st.empty()
                        agent3_output = st.empty()
                    with col2:
                        agent3_progress = st.empty()
                    
                    # Update flow to show Agent 3 is active
                    agent3_box.markdown("🔄 **Agent 3: Reclassification** 🟢 *Active*")
                    
                    agent3_status.info("Reclassifying invoice items and categories...")
                    agent3_progress.progress(0)
                    
                    # Simulate processing time
                    for i in range(0, 101, 20):
                        agent3_progress.progress(i)
                        time.sleep(3)
                    
                    agent3_status.success("Reclassification ready (placeholder)")
                    agent3_output.text_area("Reclassification Results", value="Reclassification agent will be implemented here", height=100, disabled=True)
                    
                    # Show agent 3 thinking process
                    with st.expander("Agent 3 Thinking Process"):
                        st.text_area("Planning & Strategy", 
                                   value="Analyzing invoice line items and categorizing by business expense types",
                                   height=100, disabled=True)
                        st.text_area("Classification Logic", 
                                   value="Applying accounting standards to categorize expenses (Office Supplies, Software, etc.)",
                                   height=100, disabled=True)
                        st.text_area("Business Rules", 
                                   value="Validating classifications against company policies and tax requirements",
                                   height=100, disabled=True)
                    
                    # Mark Agent 3 as complete
                    agent3_box.markdown("🔄 **Agent 3: Reclassification** ✅ *Complete*")
                
                st.divider()
                
                # Wait 5 seconds before Agent 4
                time.sleep(5)
                
                # Agent 4: Amortization Agent
                st.markdown("### 📈 Agent 4: Amortization Analysis")
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        agent4_status = st.empty()
                        agent4_output = st.empty()
                    with col2:
                        agent4_progress = st.empty()
                    
                    # Update flow to show Agent 4 is active
                    agent4_box.markdown("📈 **Agent 4: Amortization** 🟢 *Active*")
                    
                    agent4_status.info("Calculating amortization schedules...")
                    agent4_progress.progress(0)
                    
                    # Simulate processing time
                    for i in range(0, 101, 20):
                        agent4_progress.progress(i)
                        time.sleep(3)
                    
                    agent4_status.success("Amortization analysis ready (placeholder)")
                    agent4_output.text_area("Amortization Results", value="Amortization agent will be implemented here", height=100, disabled=True)
                    
                    # Show agent 4 thinking process
                    with st.expander("Agent 4 Thinking Process"):
                        st.text_area("Planning & Strategy", 
                                   value="Calculating payment schedules and depreciation timelines for invoice items",
                                   height=100, disabled=True)
                        st.text_area("Financial Analysis", 
                                   value="Determining amortization periods based on item types and accounting standards",
                                   height=100, disabled=True)
                        st.text_area("Schedule Generation", 
                                   value="Creating monthly payment schedules and tracking remaining balances",
                                   height=100, disabled=True)
                    
                    # Mark Agent 4 as complete
                    agent4_box.markdown("📈 **Agent 4: Amortization** ✅ *Complete*")
                
                st.divider()
                
            # Final Results Summary
            st.markdown("### 📋 Processing Summary")
            if "invoice" in temp_paths:
                try:
                    if 'result' in locals():
                        display_invoice_results(result)
                except:
                    st.info("Invoice processing completed - see results above")
            
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
                except Exception as e:
                    agent1_status.error(f"Text analysis failed: {str(e)}")
                    text_result = None
            
            # Same placeholder agents as above
            st.divider()
            st.markdown("### 📊 Agent 2: Spreadsheet Analysis")
            st.info("Spreadsheet reading agent ready (placeholder)")
            
            st.divider()
            st.markdown("### 🔄 Agent 3: Reclassification")
            st.info("Reclassification agent ready (placeholder)")
            
            st.divider()
            st.markdown("### 📈 Agent 4: Amortization Analysis")
            st.info("Amortization analysis ready (placeholder)")
            
            # Final Results Summary
            if text_result:
                st.markdown("### 📋 Processing Summary")
                display_invoice_results(text_result)
            
            # Clean up
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            st.error(f"Error processing text: {str(e)}")
    else:
        st.warning("Please enter some invoice text to process.")

# Create output directory
os.makedirs("output", exist_ok=True)

# Information section
st.markdown("---")
st.markdown("## 🚀 Multi-Agent System Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📄 Agent 1: PDF Analysis
    - Extract text from PDF documents
    - Process images within PDFs  
    - Handle complex document structures
    - Real-time processing feedback
    """)
    
    st.markdown("""
    ### 🔄 Agent 3: Reclassification
    - Categorize invoice items
    - Apply business rules
    - Standardize classifications
    - Generate audit trails
    """)

with col2:
    st.markdown("""
    ### 📊 Agent 2: Spreadsheet Analysis
    - Read tabular data structures
    - Identify monetary amounts
    - Process multiple invoices
    - Calculate combined totals
    """)
    
    st.markdown("""
    ### 📈 Agent 4: Amortization Analysis
    - Calculate payment schedules
    - Generate amortization tables
    - Track payment progress
    - Financial planning insights
    """)