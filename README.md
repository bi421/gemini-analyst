# 🤖 Smart AI Data Analyst with Claude AI

A **powerful AI-powered data analysis chatbot** powered by Claude 3.5 Sonnet. Upload your data and chat naturally with Claude to get instant insights, visualizations, and analysis.

## ✨ Key Features

### 🧠 Claude AI Chat
- **Natural language understanding** - Ask questions naturally, no SQL needed
- **Contextual analysis** - Claude understands your data structure
- **Smart insights** - Get actionable recommendations and patterns
- **Follow-up questions** - Maintain conversation context across messages
- **Multi-turn conversation** - Build on previous answers

### 📊 Data Operations
- **Filtering & sorting** - Quick data filtering with natural language
- **Aggregation** - Sum, average, count, min/max calculations
- **Grouping** - Analyze data by categories
- **Visualization** - Automatic chart generation

### 📁 File Support
- ✅ CSV (.csv)
- ✅ Excel (.xlsx, .xls)
- ✅ JSON (.json)

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Anthropic API Key (get one at https://console.anthropic.com)

### Setup

1. Clone or download this repository
```bash
git clone <your-repo-url>
cd smart-data-analyst
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the application
```bash
streamlit run app.py
```

5. Open your browser to `http://localhost:8501`

## 📖 Usage

### Step 1: Set Up API Key
1. Get your Anthropic API Key from https://console.anthropic.com
2. Paste it in the "🔑 Anthropic API Key" field in the sidebar
3. You'll see a ✅ confirmation

### Step 2: Upload Data
1. Click "Upload CSV, Excel, or JSON file" in the sidebar
2. Select your data file
3. Wait for the file to load successfully

### Step 3: Start Chatting
1. Type your question in the chat input field
2. Press Enter or click send
3. Claude will analyze your data and respond

## 🎯 Example Queries

### Analysis & Insights
- "What are the key insights in this dataset?"
- "Summarize the main trends"
- "What patterns do you see in the data?"
- "Give me a statistical summary"

### Visualization
- "Create a chart showing sales by region"
- "Visualize the distribution of prices"
- "Make a bar chart of top customers"

### Specific Calculations
- "What's the average price?"
- "How many records do we have?"
- "Show me all items with price > 1000"

### Business Questions
- "What's our top product?"
- "Which region has the highest sales?"
- "What customer segment is most profitable?"
- "How can we improve revenue?"

## 🏗️ Project Structure

```
smart-data-analyst/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
└── sample_data.csv       # (Optional) Sample dataset
```

## 🛠️ Technologies

- **Streamlit** - Web UI framework
- **Claude 3.5 Sonnet** - Advanced AI model by Anthropic
- **Pandas** - Data manipulation
- **Plotly** - Interactive visualization
- **Python 3.8+** - Programming language

## 📊 How It Works

1. **File Upload** → Data is loaded and analyzed
2. **Natural Language Processing** → Claude understands your question
3. **Data Analysis** → Claude examines your data context
4. **Intelligent Response** → Get insights, visualizations, or recommendations
5. **Conversation Memory** → All previous messages are considered for context

## 🔐 Security & Privacy

- API keys are **NOT stored** on our servers
- Data is sent directly to Anthropic's API
- Each session is **independent**
- No data is logged or saved permanently
- You control all your data

## ⚙️ Configuration

### API Key Management
```python
# Your API key is stored in Streamlit session state
# Never hardcode API keys in production!
api_key = st.text_input("API Key", type="password")
```

### Model Selection
The app uses `claude-3-5-sonnet-20241022` by default. You can change it in `ClaudeDataAnalyst` class:
```python
self.model = "claude-3-5-sonnet-20241022"  # Change model here
```

## 📊 Sample Data

Create a sample CSV file to test:

```csv
Date,Product,Sales,Region,Price,Quantity
2024-01-01,Product A,1500,North,2500,6
2024-01-02,Product B,2000,South,3000,5
2024-01-03,Product A,1750,East,2500,7
2024-01-04,Product C,3000,West,4500,5
2024-01-05,Product B,2500,North,3000,8
2024-01-06,Product A,2000,South,2500,8
```

## 🐛 Troubleshooting

### "API Key not configured"
- Make sure you pasted your API key in the sidebar
- Check that the key is valid at https://console.anthropic.com

### "No module named 'anthropic'"
```bash
pip install anthropic --upgrade
```

### File upload fails
- Check file format (CSV, Excel, or JSON)
- Ensure UTF-8 encoding
- File size should be reasonable (< 100MB recommended)

### Claude doesn't respond
- Check your internet connection
- Verify your API key is valid
- Check that you have API credits
- Try a simpler question first

## 🚀 Deployment

### Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to https://streamlit.io/cloud
3. Click "New app"
4. Select your repository and branch
5. Add secrets in app settings:
```
ANTHROPIC_API_KEY = "your-api-key-here"
```

### Deploy to Other Platforms

**Heroku:**
```bash
heroku create your-app-name
git push heroku main
```

**AWS, Azure, Google Cloud:**
- Use their container deployment services
- Set environment variables for API key
- Ensure HTTPS is enabled

## 💰 Pricing

- **Claude API** - Pay per token used (very affordable)
- **Streamlit Cloud** - Free tier available
- Check Anthropic's pricing: https://www.anthropic.com/pricing

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

This project is open source under the MIT License.

## 🆘 Support

- **Anthropic Support:** https://support.anthropic.com
- **Streamlit Docs:** https://docs.streamlit.io
- **Claude Documentation:** https://docs.anthropic.com

## 🎓 Learning Resources

- [Claude Prompt Engineering Guide](https://docs.anthropic.com/prompt-engineering/guide)
- [Streamlit Tutorial](https://docs.streamlit.io/get-started)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

**Made with ❤️ for data enthusiasts**

**Powered by Claude AI** 🤖
