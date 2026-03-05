# 🤖 Smart AI Data Analyst

An intelligent data analysis assistant powered by natural language processing (NLP-lite). Upload your CSV, Excel, or JSON files and ask questions in natural language to get insights, visualizations, and statistical analysis.

## ✨ Features

### 📊 Arithmetic Operations
- **Average** - Calculate mean values
- **Sum** - Get total sums
- **Min/Max** - Find minimum and maximum values
- **Count** - Count total records
- **Standard Deviation** - Measure variability

### 🔍 Data Filtering
- **Greater than** (`column > value`)
- **Less than** (`column < value`)
- **Equal to** (`column = value`)
- **Not equal** (`column ≠ value`)

### 📈 Visualization
- **Histograms** - Distribution analysis
- **Bar Charts** - Category comparison
- **Grouping** - Aggregate by categories
- **Interactive Charts** - Powered by Plotly

### ℹ️ Data Information
- Column statistics
- Data types
- Missing values
- Memory usage

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone or download this repository
```bash
git clone <your-repo-url>
cd smart-data-analyst
```

2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

## 📖 Usage

1. Start the application
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

3. Upload a data file (CSV, Excel, or JSON) using the sidebar

4. Ask questions in natural language:
   - "Sales column average"
   - "Price > 1000"
   - "Category sales"
   - "Revenue chart"

## 🎯 Example Queries

### English
- "What is the average price?"
- "Show me products with sales > 100"
- "Create a chart for revenue by category"
- "Group by region and sum sales"

### Mongolian
- "Үнийн дундаж хэд вэ?"
- "Sales > 100 байх өгөгдлийг үзүүлэх"
- "Category-ээр Revenue-ийн график"
- "Region-ээр бүлгэлэн Sales нийлбэр"

## 🏗️ Project Structure

```
smart-data-analyst/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── sample_data.csv       # (Optional) Sample dataset
```

## 🛠️ Technologies Used

- **Streamlit** - Web application framework
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive data visualization
- **Python** - Programming language

## 📝 Supported File Formats

- ✅ CSV (.csv)
- ✅ Excel (.xlsx, .xls)
- ✅ JSON (.json)

## 🎨 Features Details

### Smart Query Processing
The application uses an intelligent NLP-lite agent that:
- Detects column names from your queries (case-insensitive)
- Recognizes mathematical operations
- Identifies filtering conditions
- Generates appropriate visualizations

### Session Management
- Chat history is preserved during your session
- Clear chat history anytime with the "Clear Chat" button
- File data is cached for performance

### Error Handling
- Comprehensive error messages
- Validation of data and inputs
- Safe numeric conversions
- Detailed logging for debugging

## 📊 Sample Data

To test the application, create a sample CSV file:

```csv
Date,Product,Sales,Region,Price
2024-01-01,Product A,150,North,2500
2024-01-02,Product B,200,South,3000
2024-01-03,Product A,175,East,2500
2024-01-04,Product C,300,West,4500
```

## 🔧 Configuration

You can customize:
- Page title and icon
- Layout (wide/centered)
- Sidebar state (expanded/collapsed)
- Chart styles and themes
- Default number of bins for histograms

## 🐛 Troubleshooting

### File Upload Issues
- Ensure file is in supported format (CSV, Excel, JSON)
- Check file encoding (UTF-8 recommended)
- Verify file size (Streamlit has limits)

### Query Processing Issues
- Use simple, clear language
- Include column names as they appear in data
- Try rephrasing your question
- Check column names in the sidebar

### Performance Issues
- Reduce dataset size for faster processing
- Use simpler queries
- Clear browser cache
- Restart the Streamlit app

## 🚀 Deployment

### Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create new app and select your repository
4. Configure secrets if needed
5. Deploy!

### Deploy to Other Platforms

- **Heroku** - Use Procfile and setup.sh
- **AWS** - Use EC2 or Lightsail
- **Azure** - Use App Service
- **Docker** - Containerize with Docker

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Created with ❤️ for data enthusiasts who love natural language interfaces.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Happy Data Analyzing!** 🚀📊
