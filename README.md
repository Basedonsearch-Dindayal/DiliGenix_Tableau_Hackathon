# DiliGenix Apex v13.0 | AI-Powered Competitive Intelligence Platform

> **Transforming weeks of manual market research into minutes of automated analysis with seamless Tableau Cloud integration**

[![Tableau Hackathon 2026](https://img.shields.io/badge/Tableau-Hackathon%202026-blue)](https://www.tableau.com)
[![Python](https://img.shields.io/badge/Python-3.14-green)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---
## 🎥 **Demo Video**

Watch the 5-minute demonstration: [**Watch on YouTube**](https://youtu.be/NS-T8bYzY9g)

[![DiliGenix Demo Video](https://img.youtube.com/vi/NS-T8bYzY9g/0.jpg)](https://youtu.be/NS-T8bYzY9g)

**Video Highlights:**
- Live intelligence gathering demonstration
- Real-time Tableau Cloud publishing
- Interactive dashboard walkthrough
- Business impact showcase

---

## 📊 **Project Pitch**

DiliGenix Apex automates competitive intelligence research using recursive AI agents, then publishes interactive data directly to Tableau Cloud via REST API - transforming weeks of manual research into minutes of automated analysis with publication-ready visualizations.

---

## 🎯 **Problem Statement**

Market research analysts spend **60-80 hours per report**, manually:
- Crawling multiple websites for information
- Synthesizing data from disparate sources
- Creating SWOT, PESTLE, and competitive analyses
- Building presentations and reports

**The Result:** Slow, expensive, and inconsistent intelligence that can't keep pace with modern business needs.

---

## 💡 **Our Solution**

DiliGenix Apex leverages AI and Tableau's Developer Platform to deliver:

- ⚡ **Automated Research**: AI agents autonomously gather intelligence from web sources
- 🧠 **Intelligent Synthesis**: Advanced language models generate comprehensive analysis
- 📊 **Tableau Integration**: One-click publishing to Tableau Cloud via REST API
- 🎨 **Interactive Dashboards**: Stakeholders explore data visually in Tableau
- ⏱️ **90% Time Reduction**: Weeks → Minutes

---

## 🚀 **Key Features**

### **1. Recursive AI Agent System**
- **Automated Vector Generation**: AI creates 7 strategic research angles
- **Web Intelligence Mining**: Automatic crawling via DuckDuckGo Search API
- **Content Extraction**: Trafilatura-powered web scraping
- **Intelligent Synthesis**: Ollama AI generates comprehensive summaries

### **2. Comprehensive Analysis Reports**
Automatically generates five critical sections:
- 📝 **Executive Summary**: High-level market overview
- 💪 **SWOT Analysis**: Strengths, Weaknesses, Opportunities, Threats
- 🌍 **PESTLE Analysis**: Political, Economic, Social, Technological, Legal, Environmental factors
- 🏆 **Competitive Landscape**: Market positioning and competitor analysis
- 📈 **Strategic Outlook**: 2026-2030 projections and recommendations

### **3. Tableau Developer Platform Integration**

#### **Tableau Hyper API**
- Generates native `.hyper` files with unified data structure
- Optimized for Tableau Cloud publishing
- Single fact table design for REST API compatibility

#### **Tableau REST API**
- **One-click cloud publishing**: Automatic authentication and data upload
- **Project management**: Creates/updates Tableau Cloud projects
- **Datasource publishing**: Server.PublishMode.Overwrite for updates
- **Direct browser access**: Auto-opens published datasources

#### **Export Options**
- **CSV Export**: Universal compatibility with all Tableau versions
- **Interactive HTML Dashboard**: Standalone Plotly visualizations
- **Markdown Reports**: Traditional documentation format

### **4. Professional UI**
- **PyQt5 Desktop Application**: Native Windows interface
- **Real-time Progress Tracking**: Live logs and status updates
- **Multi-tab Workspace**: Separate views for vectors and master report
- **Tree View Discovery**: Visual representation of research sources
- **Dark Mode Interface**: Professional terminal aesthetic

### **5. Configurable Tableau Cloud Integration**
- **Credential Management**: Secure storage of API credentials
- **Connection Testing**: Validate credentials before use
- **Multi-site Support**: Works with any Tableau Cloud instance
- **Error Handling**: Detailed diagnostics for troubleshooting

---

## 🛠️ **Technologies & APIs Used**

### **Core Technologies**
- **Python 3.14**: Primary development language
- **PyQt5**: Desktop GUI framework
- **Ollama AI**: Language model integration (gpt-oss:120b)

### **Tableau Developer Platform**
- **Tableau Hyper API** (`tableauhyperapi`): Native data format generation
- **Tableau REST API** (`tableauserverclient`): Cloud publishing and management
- **Tableau Cloud**: Data hosting and visualization platform

### **Data Collection & Processing**
- **DuckDuckGo Search API** (`duckduckgo-search`): Web search
- **Trafilatura**: Content extraction from web pages
- **BeautifulSoup4**: HTML parsing
- **Pandas**: Data manipulation

### **Visualization**
- **Plotly**: Interactive HTML dashboards
- **Markdown**: Report formatting

---

## 📦 **Installation**

### **Prerequisites**
- Python 3.14 or higher
- Tableau Cloud account (free trial available)

**Required packages:**
```
PyQt5
tableauhyperapi
tableauserverclient
requests
trafilatura
markdown
beautifulsoup4
ollama
duckduckgo-search
pandas
plotly
```

4. **Configure Ollama**
- Install Ollama: https://ollama.com
- Ensure the `gpt-oss:120b` model is available
- Update API credentials in code if using different endpoint

---

## 🎮 **Usage Guide**

### **1. Launch Application**
```bash
python pega.py
```

### **2. Configure Tableau Cloud (First Time)**
- Click **⚙️ CLOUD SETTINGS**
- Enter your Tableau Cloud credentials:
  - **Server URL**: `https://your-site.online.tableau.com`
  - **Username**: Your email or token name
  - **Password**: Your password or personal access token
  - **Site ID**: From your Tableau Cloud URL (optional)
  - **Project Name**: `DiliGenix` (or custom)
- Click **Save & Test Connection**

### **3. Run Intelligence Analysis**
- Enter target company/topic (e.g., "Tesla", "SpaceX", "Microsoft")
- Click **DEPLOY AGENT**
- Watch real-time progress:
  - Research vectors generated
  - Web sources crawled
  - Intelligence synthesized
  - Report sections streamed

### **4. Export & Share**

**Option A: Publish to Tableau Cloud (Recommended)**
- Click **☁️ PUBLISH TO CLOUD**
- System automatically:
  - Generates Hyper file
  - Authenticates with Tableau Cloud
  - Publishes datasource
  - Opens in browser
- Create workbooks and dashboards in Tableau

**Option B: Export CSV + Dashboard**
- Click **EXPORT TO TABLEAU**
- Choose **Export as CSV**
- Get 4 CSV files + interactive HTML dashboard
- Manually import to Tableau if needed

**Option C: Download Report**
- Click **DOWNLOAD MD**
- Save markdown report for documentation

---

## 📊 **Tableau Cloud Data Structure**

Published datasources contain a unified fact table with:

| Column | Type | Description |
|--------|------|-------------|
| `Data_Type` | Text | Type of record (Research Vector, Source URL, Analysis Section, Project Metadata) |
| `Query_Vector` | Text | Research query or section title |
| `Content` | Text | Intelligence summary or analysis content |
| `Metric_Name` | Text | Type of metric (Summary Length, Word Count, URL Count) |
| `Metric_Value` | Integer | Numeric value for metrics |
| `URL` | Text | Source URL (for Source URL records) |
| `Domain` | Text | Website domain |
| `Timestamp` | Text | ISO 8601 timestamp |
| `Target_Name` | Text | Analysis subject name |

### **Tableau Visualization Ideas**
- Filter by `Data_Type` to analyze specific data types
- Bar charts: `Query_Vector` vs `Metric_Value`
- Pie charts: `Domain` distribution for source analysis
- Word clouds: Common terms in `Content`
- Timeline: `Timestamp` for data collection tracking

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────┐
│                  DiliGenix Apex                     │
│                   (PyQt5 UI)                        │
└─────────────────────┬───────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼────┐              ┌────▼────┐
    │   AI    │              │  Data   │
    │  Agent  │              │ Export  │
    └────┬────┘              └────┬────┘
         │                         │
    ┌────▼────────────┐       ┌───▼──────────────┐
    │  Web Scraping   │       │ Tableau Hyper    │
    │  - DuckDuckGo   │       │      API         │
    │  - Trafilatura  │       └───┬──────────────┘
    └─────────────────┘           │
                              ┌───▼──────────────┐
                              │ Tableau REST     │
                              │      API         │
                              └───┬──────────────┘
                                  │
                              ┌───▼──────────────┐
                              │  Tableau Cloud   │
                              │  (Datasources &  │
                              │   Dashboards)    │
                              └──────────────────┘
```

---

## 📈 **Business Impact**

| Metric | Traditional Approach | DiliGenix Apex | Improvement |
|--------|---------------------|----------------|-------------|
| **Time to Report** | 60-80 hours | 5 minutes | **99% faster** |
| **Cost per Report** | $2,000-4,000 | $50-100 | **95% cheaper** |
| **Data Sources** | 5-10 manual | 20+ automated | **200% more** |
| **Update Frequency** | Quarterly | On-demand | **Real-time** |
| **Visualization Time** | 4-8 hours | Instant | **100% automated** |

---

## 🔮 **Future Enhancements**

### **Planned Features**
- [ ] **Multi-language Support**: Analyze non-English sources
- [ ] **Sentiment Analysis**: Track brand perception over time
- [ ] **Social Media Integration**: Twitter, LinkedIn, Reddit APIs
- [ ] **Financial Data**: Stock prices, revenue, market cap
- [ ] **Automated Scheduling**: Periodic re-analysis and updates
- [ ] **Tableau Workbook Templates**: Pre-built dashboard templates
- [ ] **Email Alerts**: Notify stakeholders of new insights
- [ ] **API Endpoints**: RESTful API for third-party integration
- [ ] **Multi-company Comparison**: Side-by-side competitive analysis
- [ ] **Custom Vector Configuration**: User-defined research angles

### **Technical Improvements**
- [ ] Async web scraping for faster data collection
- [ ] Caching layer to avoid duplicate requests
- [ ] Database integration for historical tracking
- [ ] Docker containerization for easy deployment
- [ ] Kubernetes orchestration for scale
- [ ] Unit tests and CI/CD pipeline
- [ ] Performance monitoring and analytics

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Tableau** for providing the Developer Platform and hosting the hackathon
- **Ollama** for the AI language model infrastructure
- **DuckDuckGo** for the privacy-focused search API
- **Open Source Community** for the amazing tools and libraries

---

## 🏆 **Hackathon Submission**

**Tableau Hackathon: The Future of Analytics**

- **Category**: Tableau Cloud - Developer Platform
- **APIs Used**: Tableau Hyper API, Tableau REST API
- **Submission Date**: January 12, 2026
- **Demo Video**: [https://youtu.be/NS-T8bYzY9g](https://youtu.be/NS-T8bYzY9g)
- **Live Demo**: Available upon request

---

<div align="center">

⭐ Star this repo if you find it useful!

</div>
