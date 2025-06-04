# Multi-Agent Invoice Processing System

A Python-based multi-agent invoice and financial document processing platform that leverages advanced AI technologies for intelligent document analysis across different document types, with enhanced agent workflow and flexible processing capabilities.

## Features

- **5-Agent Workflow**: Sequential processing with specialized agents
- **LangGraph Integration**: Advanced workflow management and tracing
- **OpenAI GPT-4o Analysis**: Intelligent document understanding
- **Real-time Tracing**: Live workflow visualization and thinking processes
- **Session Management**: Persistent storage of agent results
- **Reconciliation**: Cross-verification between invoice and spreadsheet data

## Agent Architecture

1. **Agent 1: Invoice Analysis** - Processes PDFs, images, and text files to extract invoice data
2. **Agent 2: Spreadsheet Analysis** - Analyzes Excel/CSV files for amortization and financial data
3. **Agent 3: Reconciliation** - Compares amounts between invoice and spreadsheet data with Yes/No verdict
4. **Agent 4: Reclassification** - Categorizes and classifies processed data
5. **Agent 5: Amortization** - Calculates payment schedules and amortization

## Technology Stack

- **Backend**: Python 3.11+
- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT-4o, LangGraph
- **Document Processing**: PyPDF2, OpenPyXL, Pandas
- **Workflow Management**: LangGraph with advanced tracing
- **Session Storage**: JSON-based file system

## Installation

### Prerequisites

- Python 3.11 or higher
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd invoice-processing-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install streamlit langgraph openai openpyxl pandas pillow pypdf2 pyyaml trafilatura xlrd
   ```

4. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. **Create required directories**
   ```bash
   mkdir sessions output
   ```

## Usage

1. **Start the application**
   ```bash
   streamlit run app.py --server.port 5000
   ```

2. **Access the web interface**
   Open your browser to `http://localhost:5000`

3. **Upload files**
   - Upload invoice files (PDF, PNG, JPG, TXT)
   - Upload spreadsheet files (XLSX, XLS, CSV) - optional

4. **Process documents**
   - Click "Start Multi-Agent Processing"
   - Watch the real-time agent workflow
   - View results and thinking processes

## Configuration

Edit `config.yml` to customize:
- OpenAI model settings
- Processing parameters
- Agent behavior

## File Structure

```
├── app.py                      # Main Streamlit application
├── agents/                     # Agent modules
│   ├── __init__.py            # Package initialization
│   ├── simple_tracer.py       # Invoice analysis agent
│   ├── spreadsheet_tracer.py  # Spreadsheet analysis agent
│   └── reconciliation_tracer.py # Reconciliation agent
├── utils.py                   # Utility functions
├── config.yml                 # Configuration file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── sessions/                  # Session storage (auto-created)
├── output/                    # Processing outputs (auto-created)
├── requirements-local.txt     # Python dependencies
├── SETUP.md                   # Git setup instructions
└── README.md                  # This file
```

## API Requirements

This application requires an OpenAI API key for document analysis. Get your key from:
https://platform.openai.com/api-keys

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, please create an issue in the repository.