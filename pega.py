import sys
import requests
import trafilatura
import random
import time
import ast
import re
import markdown
import os
import subprocess
import csv
import json
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from bs4 import BeautifulSoup
from ollama import Client
from duckduckgo_search import DDGS
from tableauhyperapi import HyperProcess, Telemetry, Connection, CreateMode, TableDefinition, SqlType, Inserter, TableName
import tableauserverclient as TSC

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QTextEdit, 
                             QLabel, QProgressBar, QFrame, QStatusBar, QSplitter, 
                             QTabWidget, QTreeWidget, QTreeWidgetItem, QHeaderView, 
                             QFileDialog, QMessageBox, QDialog, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# =================================================================
# 1. THE RECURSIVE SECTIONAL ENGINE (The Worker)
# =================================================================
class RecursiveSectionalAgent(QThread):
    log_sig = pyqtSignal(str, str)
    query_sig = pyqtSignal(str)     
    url_sig = pyqtSignal(str, str)  
    vector_intel_sig = pyqtSignal(str, str) # Vector Header, Content
    master_section_sig = pyqtSignal(str, str) # Section Title, Section Content
    progress_sig = pyqtSignal(int)
    finished_sig = pyqtSignal()

    def __init__(self, target):
        super().__init__()
        self.target = target
        self.client = Client(
            host='https://ollama.com',
            headers={'Authorization': 'Bearer e3e937577e944d74ade2b61703d12843.hBQh6DBmbtM8SOHDB8K2CfEN'}
        )
        self.model = 'gpt-oss:120b'
        self.vector_summaries = [] # Stores summarized intel from each query
        
        # Data structures for Tableau export
        self.tableau_vectors = []  # [{query, intel_summary, timestamp}]
        self.tableau_urls = []     # [{query, url, timestamp}]
        self.tableau_sections = [] # [{section_title, content, word_count, timestamp}]

    def run(self):
        try:
            self.log_sig.emit("SYSTEM", f"AGENT DEPLOYED: {self.target}")
            
            # --- PHASE 1: RESEARCH VECTOR GENERATION ---
            v_prompt = (
                "Generate a Python list of exactly 7 distinct market research queries "
                f"for deep due diligence on: {self.target}. Return ONLY the Python list."
            )
            resp = self.client.chat(self.model, messages=[{'role': 'user', 'content': v_prompt}])
            try:
                match = re.search(r'\[.*\]', resp['message']['content'], re.DOTALL)
                queries = ast.literal_eval(match.group(0)) if match else [self.target]
            except:
                queries = [self.target + " analysis", self.target + " competitors"]

            # --- PHASE 2: PER-VECTOR INTELLIGENCE (Building Blocks) ---
            for idx, q in enumerate(queries):
                self.query_sig.emit(q)
                self.log_sig.emit("AI_THOUGHT", f"Mining Vector: {q}")
                
                raw_texts = []
                try:
                    results = DDGS().text(q, max_results=3)
                    for r in results:
                        link = r['href']
                        self.url_sig.emit(q, link)
                        data = trafilatura.extract(trafilatura.fetch_url(link))
                        if data: raw_texts.append(data[:2000])
                        
                        # Store URL for Tableau
                        self.tableau_urls.append({
                            'query': q,
                            'url': link,
                            'timestamp': datetime.now().isoformat()
                        })
                except: pass

                if raw_texts:
                    sub_prompt = f"Summarize the core intelligence for the query '{q}' based on these sources:\n" + "\n".join(raw_texts)
                    sub_intel = self.client.chat(self.model, messages=[{'role': 'user', 'content': sub_prompt}])
                    intel_txt = sub_intel['message']['content']
                    
                    self.vector_intel_sig.emit(q, intel_txt)
                    self.vector_summaries.append(f"RESEARCH DATA FOR {q}: {intel_txt}")
                    
                    # Store for Tableau
                    self.tableau_vectors.append({
                        'query': q,
                        'intel_summary': intel_txt,
                        'timestamp': datetime.now().isoformat()
                    })
                
                self.progress_sig.emit(int(((idx+1)/len(queries))*50))

            # --- PHASE 3: SECTIONAL MASTER SYNTHESIS (Streaming sections) ---
            self.log_sig.emit("SYSTEM", "Executing Sectional Master Synthesis...")
            
            report_sections = [
                ("Executive Summary", "Synthesize a high-level overview and market standing."),
                ("SWOT Analysis", "Provide a detailed Strengths, Weaknesses, Opportunities, and Threats breakdown."),
                ("PESTLE Analysis", "Analyze Political, Economic, Social, Technological, Legal, and Environmental factors."),
                ("Competitive Landscape", "Analyze market share and direct competitor positioning."),
                ("Strategic Outlook", "Provide 2026-2030 projections and final recommendations.")
            ]

            context_for_master = "\n\n".join(self.vector_summaries)

            for i, (title, instruction) in enumerate(report_sections):
                self.log_sig.emit("AI", f"Streaming Master Section: {title}")
                
                section_prompt = (
                    f"You are the DiliGenix Lead Partner. Using ONLY the following research data, "
                    f"write the '{title}' section of a report for {self.target}. {instruction} "
                    "Be professional, use Markdown headers, and do not truncate. Provide the full text for this section."
                    f"\n\nRESEARCH DATA:\n{context_for_master[:10000]}"
                )
                
                section_resp = self.client.chat(self.model, messages=[{'role': 'user', 'content': section_prompt}])
                section_content = section_resp['message']['content']
                
                # Signal the UI to append this section immediately
                self.master_section_sig.emit(title, section_content)
                self.progress_sig.emit(50 + int(((i+1)/len(report_sections))*50))
                
                # Store section for Tableau
                self.tableau_sections.append({
                    'section_title': title,
                    'content': section_content,
                    'word_count': len(section_content.split()),
                    'timestamp': datetime.now().isoformat()
                })

            self.finished_sig.emit()
            self.log_sig.emit("SUCCESS", "Terminal has vaulted all intelligence sections.")

        except Exception as e:
            self.log_sig.emit("ERROR", f"Agent Error: {str(e)}")

# =================================================================
# TABLEAU CLOUD CONFIGURATION
# =================================================================
class TableauCloudConfig:
    """Store and manage Tableau Cloud credentials"""
    CONFIG_FILE = "tableau_cloud_config.json"
    
    def __init__(self):
        self.server_url = ""
        self.username = ""
        self.password = ""
        self.site_id = ""
        self.project_name = "DiliGenix"
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.server_url = data.get('server_url', '')
                    self.username = data.get('username', '')
                    self.password = data.get('password', '')
                    self.site_id = data.get('site_id', '')
                    self.project_name = data.get('project_name', 'DiliGenix')
            except:
                pass
    
    def save_config(self):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump({
                'server_url': self.server_url,
                'username': self.username,
                'password': self.password,
                'site_id': self.site_id,
                'project_name': self.project_name
            }, f)

class TableauCloudSettingsDialog(QDialog):
    """Dialog for configuring Tableau Cloud credentials"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Tableau Cloud Settings")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout()
        
        # Server URL
        layout.addWidget(QLabel("<b>Tableau Cloud URL:</b>"), 0, 0)
        self.server_input = QLineEdit(self.config.server_url)
        self.server_input.setPlaceholderText("https://your-site.online.tableau.com")
        layout.addWidget(self.server_input, 0, 1)
        
        # Username
        layout.addWidget(QLabel("<b>Username/Email:</b>"), 1, 0)
        self.username_input = QLineEdit(self.config.username)
        self.username_input.setPlaceholderText("your-email@example.com")
        layout.addWidget(self.username_input, 1, 1)
        
        # Password/Token
        layout.addWidget(QLabel("<b>Password/Token:</b>"), 2, 0)
        self.password_input = QLineEdit(self.config.password)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Your password or personal access token")
        layout.addWidget(self.password_input, 2, 1)
        
        # Site ID
        layout.addWidget(QLabel("<b>Site ID:</b>"), 3, 0)
        self.site_input = QLineEdit(self.config.site_id)
        self.site_input.setPlaceholderText("Leave empty for default site")
        layout.addWidget(self.site_input, 3, 1)
        
        # Project Name
        layout.addWidget(QLabel("<b>Project Name:</b>"), 4, 0)
        self.project_input = QLineEdit(self.config.project_name)
        self.project_input.setPlaceholderText("DiliGenix")
        layout.addWidget(self.project_input, 4, 1)
        
        # Help text
        help_label = QLabel(
            "<small><i>Since Personal Access Tokens are disabled on trial accounts,<br>"
            "use your Tableau Cloud <b>email</b> as Username and <b>password</b>.<br><br>"
            "Example:<br>"
            "Server: https://prod-in-a.online.tableau.com<br>"
            "Username: your-email@example.com<br>"
            "Password: your-tableau-password<br>"
            "Site ID: dindayalsinha301-de52cf7cad (from your URL)</i></small>"
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label, 5, 0, 1, 2)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Test Connection")
        save_btn.clicked.connect(self.test_and_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 6, 0, 1, 2)
        
        self.setLayout(layout)
    
    def test_and_save(self):
        # Save values
        self.config.server_url = self.server_input.text().strip()
        self.config.username = self.username_input.text().strip()
        self.config.password = self.password_input.text().strip()
        self.config.site_id = self.site_input.text().strip()
        self.config.project_name = self.project_input.text().strip() or "DiliGenix"
        
        if not all([self.config.server_url, self.config.username, self.config.password]):
            QMessageBox.warning(self, "Missing Info", "Please fill in Server URL, Username, and Password")
            return
        
        # Test connection - supports both PAT and username/password
        try:
            tableau_auth = TSC.TableauAuth(
                self.config.username, 
                self.config.password, 
                site_id=self.config.site_id
            )
            server = TSC.Server(self.config.server_url, use_server_version=True)
            
            with server.auth.sign_in(tableau_auth):
                site_name = server.site_id or "default"
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"✅ Successfully connected to Tableau Cloud!\n\n"
                    f"Server: {self.config.server_url}\n"
                    f"Site: {site_name}\n"
                    f"User: {self.config.username}"
                )
            
            self.config.save_config()
            self.accept()
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                QMessageBox.critical(
                    self, 
                    "Authentication Failed", 
                    f"Could not sign in to Tableau Cloud.\n\n"
                    f"Please check:\n"
                    f"✓ Server URL is correct\n"
                    f"✓ Username is your email address\n"
                    f"✓ Password is correct\n"
                    f"✓ Site ID is correct\n\n"
                    f"Error: {error_msg}"
                )
            else:
                QMessageBox.critical(
                    self, 
                    "Connection Failed", 
                    f"Could not connect to Tableau Cloud:\n\n{error_msg}\n\n"
                    f"Make sure:\n"
                    f"• Your internet connection is working\n"
                    f"• The server URL includes 'https://'\n"
                    f"• You have an active Tableau Cloud account"
                )

def publish_to_tableau_cloud(hyper_path, datasource_name, config, log_callback=None):
    """
    Publish hyper file to Tableau Cloud and create a workbook with visualizations
    Returns: (datasource_url, workbook_url) or raises exception
    """
    if log_callback:
        log_callback("TABLEAU CLOUD", "Authenticating...")
    
    # Authenticate
    tableau_auth = TSC.TableauAuth(config.username, config.password, site_id=config.site_id)
    server = TSC.Server(config.server_url, use_server_version=True)
    
    with server.auth.sign_in(tableau_auth):
        # Find or create project
        all_projects, _ = server.projects.get()
        project = None
        for p in all_projects:
            if p.name == config.project_name:
                project = p
                break
        
        if not project:
            if log_callback:
                log_callback("TABLEAU CLOUD", f"Creating project: {config.project_name}")
            project = TSC.ProjectItem(name=config.project_name, description="DiliGenix Intelligence Reports")
            project = server.projects.create(project)
        
        # Publish datasource
        if log_callback:
            log_callback("TABLEAU CLOUD", f"Publishing datasource: {datasource_name}")
        
        datasource = TSC.DatasourceItem(project.id, name=datasource_name)
        datasource = server.datasources.publish(
            datasource, hyper_path, TSC.Server.PublishMode.Overwrite
        )
        
        datasource_url = f"{config.server_url}/#/site/{config.site_id}/datasources/{datasource.id}"
        
        if log_callback:
            log_callback("SUCCESS", f"Datasource published to Tableau Cloud!")
        
        return datasource_url, datasource.id

# =================================================================
# TABLEAU DATA EXPORT FUNCTIONS
# =================================================================
def generate_tableau_csv(target_name, vectors_data, urls_data, sections_data, output_folder):
    """
    Generate CSV files for Tableau (works with all Tableau versions)
    """
    # Ensure folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Export Research Vectors
    vectors_file = os.path.join(output_folder, f"{target_name}_ResearchVectors.csv")
    with open(vectors_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Query', 'Intelligence_Summary', 'Timestamp', 'Summary_Length'])
        writer.writeheader()
        for vec in vectors_data:
            writer.writerow({
                'Query': vec['query'],
                'Intelligence_Summary': vec['intel_summary'],
                'Timestamp': vec['timestamp'],
                'Summary_Length': len(vec['intel_summary'])
            })
    
    # Export Source URLs
    urls_file = os.path.join(output_folder, f"{target_name}_SourceURLs.csv")
    with open(urls_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Query', 'URL', 'Timestamp', 'Domain'])
        writer.writeheader()
        for url_data in urls_data:
            domain = url_data['url'].split('/')[2] if '://' in url_data['url'] else 'unknown'
            writer.writerow({
                'Query': url_data['query'],
                'URL': url_data['url'],
                'Timestamp': url_data['timestamp'],
                'Domain': domain
            })
    
    # Export Analysis Sections
    sections_file = os.path.join(output_folder, f"{target_name}_AnalysisSections.csv")
    with open(sections_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Section_Title', 'Content', 'Word_Count', 'Timestamp'])
        writer.writeheader()
        for section in sections_data:
            writer.writerow({
                'Section_Title': section['section_title'],
                'Content': section['content'],
                'Word_Count': section['word_count'],
                'Timestamp': section['timestamp']
            })
    
    # Export Project Metadata
    metadata_file = os.path.join(output_folder, f"{target_name}_ProjectMetadata.csv")
    with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Target_Name', 'Total_Vectors', 'Total_URLs', 'Total_Sections', 'Report_Generated'])
        writer.writeheader()
        writer.writerow({
            'Target_Name': target_name,
            'Total_Vectors': len(vectors_data),
            'Total_URLs': len(urls_data),
            'Total_Sections': len(sections_data),
            'Report_Generated': datetime.now().isoformat()
        })
    
    return [vectors_file, urls_file, sections_file, metadata_file]

def generate_interactive_dashboard(target_name, vectors_data, urls_data, sections_data, output_folder):
    """
    Generate interactive HTML dashboard with Plotly visualizations
    """
    # Create DataFrame for easier manipulation
    df_vectors = pd.DataFrame(vectors_data)
    df_urls = pd.DataFrame(urls_data)
    df_sections = pd.DataFrame(sections_data)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Research Vectors Distribution', 
            'Top Source Domains',
            'Analysis Section Word Counts',
            'Intelligence Summary Lengths',
            'Data Collection Timeline',
            'Project Overview'
        ),
        specs=[
            [{"type": "bar"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "indicator"}]
        ],
        row_heights=[0.3, 0.35, 0.35]
    )
    
    # Chart 1: Research Vectors Bar Chart
    if not df_vectors.empty:
        df_vectors['summary_length'] = df_vectors['intel_summary'].str.len()
        fig.add_trace(
            go.Bar(
                x=df_vectors['query'],
                y=df_vectors['summary_length'],
                name='Summary Length',
                marker_color='rgb(55, 83, 109)'
            ),
            row=1, col=1
        )
    
    # Chart 2: Domain Distribution Pie Chart
    if not df_urls.empty:
        df_urls['domain'] = df_urls['url'].apply(lambda x: x.split('/')[2] if '://' in x else 'unknown')
        domain_counts = df_urls['domain'].value_counts().head(10)
        fig.add_trace(
            go.Pie(
                labels=domain_counts.index,
                values=domain_counts.values,
                name='Domains'
            ),
            row=1, col=2
        )
    
    # Chart 3: Section Word Counts
    if not df_sections.empty:
        fig.add_trace(
            go.Bar(
                x=df_sections['section_title'],
                y=df_sections['word_count'],
                name='Word Count',
                marker_color='rgb(26, 118, 255)'
            ),
            row=2, col=1
        )
    
    # Chart 4: Intelligence Summary Lengths Scatter
    if not df_vectors.empty:
        fig.add_trace(
            go.Scatter(
                x=list(range(len(df_vectors))),
                y=df_vectors['summary_length'],
                mode='lines+markers',
                name='Intelligence Length',
                line=dict(color='rgb(255, 127, 14)', width=3),
                marker=dict(size=10)
            ),
            row=2, col=2
        )
    
    # Chart 5: Timeline
    if not df_urls.empty:
        df_urls['timestamp'] = pd.to_datetime(df_urls['timestamp'])
        timeline_counts = df_urls.groupby(df_urls['timestamp'].dt.floor('min')).size()
        fig.add_trace(
            go.Scatter(
                x=timeline_counts.index,
                y=timeline_counts.values,
                mode='lines+markers',
                name='URLs over Time',
                fill='tozeroy',
                line=dict(color='rgb(0, 204, 150)', width=2)
            ),
            row=3, col=1
        )
    
    # Chart 6: Key Metrics Indicator
    total_intelligence = sum(len(v['intel_summary']) for v in vectors_data)
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=len(vectors_data),
            title={"text": f"Total Research Vectors<br><span style='font-size:0.6em'>URLs: {len(urls_data)} | Sections: {len(sections_data)}</span>"},
            domain={'x': [0, 1], 'y': [0, 1]}
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text=f"DiliGenix Intelligence Dashboard: {target_name}",
        title_font_size=24,
        title_x=0.5,
        showlegend=True,
        height=1200,
        template="plotly_dark",
        paper_bgcolor='rgb(17, 17, 17)',
        plot_bgcolor='rgb(17, 17, 17)'
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    
    # Save as interactive HTML
    dashboard_file = os.path.join(output_folder, f"{target_name}_Interactive_Dashboard.html")
    fig.write_html(dashboard_file)
    
    return dashboard_file

def generate_tableau_hyper(target_name, vectors_data, urls_data, sections_data, output_path):
    """
    Generate a .hyper file with a SINGLE unified fact table for Tableau Cloud
    Tableau Cloud REST API requires exactly one fact table
    """
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(endpoint=hyper.endpoint, 
                       database=output_path, 
                       create_mode=CreateMode.CREATE_AND_REPLACE) as connection:
            
            # Create the Extract schema
            connection.catalog.create_schema_if_not_exists("Extract")
            
            # Create ONE unified fact table that combines all data
            unified_table = TableDefinition(
                table_name=TableName("Extract", "Extract"),  # Must be named "Extract" for Tableau Cloud
                columns=[
                    TableDefinition.Column("Data_Type", SqlType.text()),
                    TableDefinition.Column("Query_Vector", SqlType.text()),
                    TableDefinition.Column("Content", SqlType.text()),
                    TableDefinition.Column("Metric_Name", SqlType.text()),
                    TableDefinition.Column("Metric_Value", SqlType.int()),
                    TableDefinition.Column("URL", SqlType.text()),
                    TableDefinition.Column("Domain", SqlType.text()),
                    TableDefinition.Column("Timestamp", SqlType.text()),
                    TableDefinition.Column("Target_Name", SqlType.text())
                ]
            )
            connection.catalog.create_table(unified_table)
            
            with Inserter(connection, unified_table) as inserter:
                # Insert Research Vectors data
                for vec in vectors_data:
                    inserter.add_row([
                        "Research Vector",
                        vec['query'],
                        vec['intel_summary'],
                        "Summary Length",
                        len(vec['intel_summary']),
                        "",
                        "",
                        vec['timestamp'],
                        target_name
                    ])
                
                # Insert Source URLs data
                for url_data in urls_data:
                    domain = url_data['url'].split('/')[2] if '://' in url_data['url'] else 'unknown'
                    inserter.add_row([
                        "Source URL",
                        url_data['query'],
                        "",
                        "URL Count",
                        1,
                        url_data['url'],
                        domain,
                        url_data['timestamp'],
                        target_name
                    ])
                
                # Insert Analysis Sections data
                for section in sections_data:
                    inserter.add_row([
                        "Analysis Section",
                        section['section_title'],
                        section['content'],
                        "Word Count",
                        section['word_count'],
                        "",
                        "",
                        section['timestamp'],
                        target_name
                    ])
                
                # Insert Summary Metadata
                inserter.add_row([
                    "Project Metadata",
                    "Summary",
                    f"Total Analysis for {target_name}",
                    "Total Vectors",
                    len(vectors_data),
                    "",
                    "",
                    datetime.now().isoformat(),
                    target_name
                ])
                
                inserter.add_row([
                    "Project Metadata",
                    "Summary",
                    f"Total Analysis for {target_name}",
                    "Total URLs",
                    len(urls_data),
                    "",
                    "",
                    datetime.now().isoformat(),
                    target_name
                ])
                
                inserter.add_row([
                    "Project Metadata",
                    "Summary",
                    f"Total Analysis for {target_name}",
                    "Total Sections",
                    len(sections_data),
                    "",
                    "",
                    datetime.now().isoformat(),
                    target_name
                ])
                
                inserter.execute()

# =================================================================
# 2. THE ADVANCED TERMINAL UI
# =================================================================
class DiliGenixTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiliGenix Apex v13.0 | Recursive Sectional Terminal")
        self.resize(1550, 950)
        self.query_nodes = {}
        self.full_report_accumulator = ""
        self.tableau_cloud_config = TableauCloudConfig()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 1. TICKER HUD
        hud = QFrame()
        hud.setFixedHeight(40)
        hud_lyt = QHBoxLayout(hud)
        self.ticker = QLabel("DILIGENIX APEX: SECTIONAL SYNTHESIS ACTIVE | VECTOR INTELLIGENCE ONLINE | RECURSIVE AGENT READY")
        self.ticker.setStyleSheet("color: #ffaa00; font-family: 'Consolas'; font-weight: bold; font-size: 11px;")
        hud_lyt.addWidget(self.ticker)
        main_layout.addWidget(hud)

        # 2. COMMAND PANEL
        cmd_panel = QFrame()
        cmd_panel.setFixedHeight(60)
        cmd_lyt = QHBoxLayout(cmd_panel)
        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("ENTER SUBJECT FOR SECTIONAL RECURSIVE ANALYSIS...")
        self.btn_run = QPushButton("DEPLOY AGENT")
        self.btn_run.clicked.connect(self.start_analysis)
        self.btn_save = QPushButton("DOWNLOAD MD")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_report)
        self.btn_tableau = QPushButton("EXPORT TO TABLEAU")
        self.btn_tableau.setEnabled(False)
        self.btn_tableau.clicked.connect(self.export_to_tableau)
        self.btn_cloud = QPushButton("☁️ PUBLISH TO CLOUD")
        self.btn_cloud.setEnabled(False)
        self.btn_cloud.clicked.connect(self.publish_to_cloud)
        self.btn_settings = QPushButton("⚙️ CLOUD SETTINGS")
        self.btn_settings.clicked.connect(self.show_cloud_settings)
        self.btn_help = QPushButton("? HOW TO OPEN")
        self.btn_help.clicked.connect(self.show_tableau_help)

        cmd_lyt.addWidget(QLabel("<b><font color='#ffaa00' size='4'>> </font></b>"))
        cmd_lyt.addWidget(self.input_subject)
        cmd_lyt.addWidget(self.btn_run)
        cmd_lyt.addWidget(self.btn_save)
        cmd_lyt.addWidget(self.btn_tableau)
        cmd_lyt.addWidget(self.btn_cloud)
        cmd_lyt.addWidget(self.btn_settings)
        cmd_lyt.addWidget(self.btn_help)
        main_layout.addWidget(cmd_panel)

        # 3. WORKSPACE
        splitter = QSplitter(Qt.Horizontal)

        # Left: Discovery Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Research Vectors / Mined Sources"])
        self.tree.setFixedWidth(380)
        splitter.addWidget(self.tree)

        # Center/Right: Multi-Tab Intelligence
        self.tabs = QTabWidget()
        
        # Tab 1: Vector Insights (The blocks)
        self.insight_view = QTextEdit()
        self.insight_view.setReadOnly(True)
        self.insight_view.setPlaceholderText("Individual vector intelligence will populate here during the crawl...")
        
        # Tab 2: Master Strategic Report (The streamed final)
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setPlaceholderText("The Master Report will stream here section-by-section...")
        
        self.tabs.addTab(self.insight_view, "Vector Intelligence Blocks")
        self.tabs.addTab(self.report_view, "Master Strategic Analysis")
        splitter.addWidget(self.tabs)
        
        main_layout.addWidget(splitter)

        # 4. FOOTER
        self.prog = QProgressBar()
        self.prog.hide()
        main_layout.addWidget(self.prog)
        
        self.log_box = QTextEdit()
        self.log_box.setFixedHeight(100)
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background: #000; color: #00FF41; font-family: 'Consolas'; font-size: 10px;")
        main_layout.addWidget(self.log_box)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #0b0e14; color: #d1d5db; font-family: 'Consolas', monospace; }
            QLineEdit { background: #0b0e14; border: 1px solid #30363d; padding: 10px; color: white; border-radius: 4px; }
            QPushButton { background: #238636; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px; }
            QPushButton:hover { background: #2ea043; }
            QPushButton:disabled { background: #1a1f26; color: #444; }
            QPushButton#help { background: #0969da; }
            QTabWidget::pane { border: 1px solid #30363d; }
            QTabBar::tab { background: #161b22; padding: 12px 25px; border: 1px solid #30363d; margin-right: 2px; }
            QTabBar::tab:selected { background: #58a6ff; color: black; font-weight: bold; }
            QTreeWidget { background: #0b0e14; border: 1px solid #30363d; }
            QHeaderView::section { background: #161b22; color: #ffaa00; padding: 5px; border: none; }
            QProgressBar { border: 1px solid #30363d; background: #000; height: 10px; }
            QProgressBar::chunk { background: #ffaa00; }
        """)

    def log(self, tag, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"<font color='#ffaa00'>[{ts}] <b>{tag}:</b></font> {msg}")

    def start_analysis(self):
        target = self.input_subject.text()
        if not target: return
        
        self.tree.clear()
        self.query_nodes = {}
        self.insight_view.clear()
        self.report_view.clear()
        self.full_report_accumulator = ""
        self.btn_run.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_tableau.setEnabled(False)
        self.btn_cloud.setEnabled(False)
        self.prog.show()
        
        self.worker = RecursiveSectionalAgent(target)
        self.worker.log_sig.connect(self.log)
        self.worker.query_sig.connect(self.add_query_node)
        self.worker.url_sig.connect(self.add_url_node)
        self.worker.vector_intel_sig.connect(self.stream_vector_insight)
        self.worker.master_section_sig.connect(self.stream_master_section)
        self.worker.finished_sig.connect(self.on_complete)
        self.worker.progress_sig.connect(self.prog.setValue)
        self.worker.start()

    def add_query_node(self, q):
        parent = QTreeWidgetItem(self.tree)
        parent.setText(0, f"VEC: {q.upper()}")
        parent.setForeground(0, QColor("#ffaa00"))
        self.query_nodes[q] = parent
        self.tree.expandItem(parent)

    def add_url_node(self, q, url):
        if q in self.query_nodes:
            child = QTreeWidgetItem(self.query_nodes[q])
            child.setText(0, url)
            child.setForeground(0, QColor("#58a6ff"))

    def stream_vector_insight(self, header, content):
        # This view uses a 'Lens' style: subtle borders and distinct header glows
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        
        vector_style = """
        <style>
            body { font-family: 'Segoe UI', sans-serif; color: #d1d5db; background-color: transparent; }
            .vector-header { 
                color: #ffaa00; 
                font-size: 14px; 
                font-weight: bold; 
                text-transform: uppercase;
                letter-spacing: 1px;
                border-left: 3px solid #ffaa00;
                padding-left: 10px;
                margin-bottom: 10px;
            }
            code { background: rgba(255, 255, 255, 0.1); color: #ff79c6; border-radius: 4px; padding: 2px; }
            hr { border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 20px 0; }
        </style>
        """
        
        # We use append for insights to keep the history of mined vectors visible
        styled_block = f"""
        {vector_style}
        <div class="vector-header">RECURSIVE VECTOR: {header.upper()}</div>
        <div class="vector-content">{html_content}</div>
        <hr>
        """
        self.insight_view.append(styled_block)

    def stream_master_section(self, title, content):
        self.tabs.setCurrentIndex(1)
        self.full_report_accumulator += f"## {title}\n\n{content}\n\n"
        
        # Convert cumulative MD to HTML
        html_body = markdown.markdown(self.full_report_accumulator, extensions=['fenced_code', 'tables'])
        
        master_style = """
        <style>
            body { 
                font-family: 'Segoe UI', sans-serif; 
                color: #e0e0e0; 
                background-color: #0b0e14; 
                line-height: 1.6;
            }
            h1 { color: #ffffff; text-align: center; margin-bottom: 30px; }
            h2 { 
                color: #ffaa00; 
                text-shadow: 0 0 12px rgba(255, 170, 0, 0.4); 
                border-bottom: 1px solid rgba(255, 170, 0, 0.2);
                padding-bottom: 5px;
                margin-top: 30px;
            }
            h3 { color: #58a6ff; }
            strong { color: #ffffff; font-weight: bold; }
            ul { margin-left: 20px; color: #b0b0b0; }
            li { margin-bottom: 8px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; background: rgba(255,255,255,0.03); }
            th { background: rgba(255,170,0,0.1); color: #ffaa00; padding: 10px; text-align: left; }
            td { border: 1px solid rgba(255,255,255,0.1); padding: 8px; }
            code { background: #161b22; color: #ff7b72; padding: 3px 6px; border-radius: 4px; }
        </style>
        """
        
        # setHtml overwrites the view with the updated full document
        self.report_view.setHtml(master_style + html_body)

    def on_complete(self):
        self.btn_run.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_tableau.setEnabled(True)
        self.btn_cloud.setEnabled(True)
        self.prog.hide()
        self.log("SUCCESS", "Master Strategic Report Generation Finalized.")

    def save_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "DiliGenix_Report.md", "Markdown (*.md)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# DiliGenix Intelligence Report: {self.input_subject.text()}\n\n")
                f.write(self.full_report_accumulator)
            QMessageBox.information(self, "Success", "Report exported to vault.")
    
    def export_to_tableau(self):
        target_name = self.input_subject.text().replace(' ', '_')
        
        # Ask user which format they prefer
        format_msg = QMessageBox(self)
        format_msg.setWindowTitle("Choose Export Format")
        format_msg.setText("Select the format for Tableau export:")
        format_msg.setInformativeText(
            "CSV: Works with ALL Tableau versions (recommended)\n"
            "Hyper: Native Tableau format (faster, requires newer Tableau)"
        )
        csv_btn = format_msg.addButton("Export as CSV", QMessageBox.AcceptRole)
        hyper_btn = format_msg.addButton("Export as Hyper", QMessageBox.AcceptRole)
        format_msg.addButton(QMessageBox.Cancel)
        format_msg.exec_()
        
        if format_msg.clickedButton() == csv_btn:
            self.export_to_csv(target_name)
        elif format_msg.clickedButton() == hyper_btn:
            self.export_to_hyper(target_name)
    
    def export_to_csv(self, target_name):
        """Export data as CSV files for Tableau"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save CSV Files & Dashboard")
        if folder:
            try:
                self.log("TABLEAU", "Generating CSV files and interactive dashboard...")
                
                # Generate CSV files
                files = generate_tableau_csv(
                    target_name=target_name,
                    vectors_data=self.worker.tableau_vectors,
                    urls_data=self.worker.tableau_urls,
                    sections_data=self.worker.tableau_sections,
                    output_folder=folder
                )
                
                # Generate interactive dashboard
                dashboard_file = generate_interactive_dashboard(
                    target_name=target_name,
                    vectors_data=self.worker.tableau_vectors,
                    urls_data=self.worker.tableau_urls,
                    sections_data=self.worker.tableau_sections,
                    output_folder=folder
                )
                
                self.log("SUCCESS", f"CSV files and dashboard exported to: {folder}")
                
                file_list = "\n".join([os.path.basename(f) for f in files])
                reply = QMessageBox.question(
                    self, 
                    "Export Complete", 
                    f"Successfully exported {len(self.worker.tableau_vectors)} vectors, "
                    f"{len(self.worker.tableau_urls)} URLs, and "
                    f"{len(self.worker.tableau_sections)} analysis sections!\n\n"
                    f"Files created:\n{file_list}\n\n"
                    f"📊 Interactive Dashboard: {os.path.basename(dashboard_file)}\n\n"
                    "Would you like to open the interactive dashboard now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Open the dashboard in browser
                    if sys.platform == 'win32':
                        os.startfile(dashboard_file)
                else:
                    # Just open the folder
                    if sys.platform == 'win32':
                        os.startfile(folder)
                    
            except Exception as e:
                self.log("ERROR", f"Export failed: {str(e)}")
                QMessageBox.critical(self, "Export Error", f"Failed to export files:\n{str(e)}")
    
    def export_to_hyper(self, target_name):
        """Export data as Hyper file for Tableau"""
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export to Tableau", 
            f"DiliGenix_{target_name}.hyper", 
            "Tableau Hyper (*.hyper)"
        )
        if path:
            try:
                self.log("TABLEAU", "Generating Tableau Hyper file...")
                generate_tableau_hyper(
                    target_name=target_name,
                    vectors_data=self.worker.tableau_vectors,
                    urls_data=self.worker.tableau_urls,
                    sections_data=self.worker.tableau_sections,
                    output_path=path
                )
                self.log("SUCCESS", f"Tableau file exported: {path}")
                
                # Ask user if they want to open the file
                reply = QMessageBox.question(
                    self, 
                    "Tableau Export Complete", 
                    f"Successfully exported {len(self.worker.tableau_vectors)} vectors, "
                    f"{len(self.worker.tableau_urls)} URLs, and "
                    f"{len(self.worker.tableau_sections)} analysis sections!\n\n"
                    "Would you like to open this file in Tableau now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.open_hyper_file(path)
                    
            except Exception as e:
                self.log("ERROR", f"Tableau export failed: {str(e)}")
                QMessageBox.critical(self, "Export Error", f"Failed to export Tableau file:\n{str(e)}")
    
    def open_hyper_file(self, file_path):
        """Open the .hyper file with the default application (Tableau)"""
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # linux
                subprocess.run(['xdg-open', file_path])
            self.log("SUCCESS", "Opening file in Tableau...")
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Cannot Open File", 
                f"File saved successfully but couldn't open automatically.\n\n"
                f"Please open manually:\n{file_path}\n\n"
                f"Error: {str(e)}"
            )
    
    def show_tableau_help(self):
        """Show instructions for opening .hyper files in Tableau"""
        help_msg = QMessageBox(self)
        help_msg.setWindowTitle("How to Open .hyper Files in Tableau")
        help_msg.setIcon(QMessageBox.Information)
        help_msg.setText(
            "<h3>📊 How to Open Your .hyper File in Tableau</h3>"
            "<p><b>Step 1: Open Tableau Desktop or Tableau Public</b></p>"
            "<p>• Launch the Tableau application</p>"
            "<p>• If you don't have it, download <a href='https://public.tableau.com/app/discover'>Tableau Public (Free)</a></p>"
            "<br>"
            "<p><b>Step 2: Connect to Data</b></p>"
            "<p>• On the start page, go to <b>Connect → To a File</b></p>"
            "<p>• Click <b>More...</b> at the bottom</p>"
            "<p>• Select <b>Tableau Hyper</b> from the list</p>"
            "<br>"
            "<p><b>Step 3: Select Your File</b></p>"
            "<p>• Browse to your exported <b>.hyper</b> file</p>"
            "<p>• Click <b>Open</b></p>"
            "<br>"
            "<p><b>Step 4: View Your Data</b></p>"
            "<p>You'll see 4 tables in the left panel:</p>"
            "<p>• <b>ResearchVectors</b> - Query intelligence data</p>"
            "<p>• <b>SourceURLs</b> - Web sources discovered</p>"
            "<p>• <b>AnalysisSections</b> - SWOT, PESTLE analysis</p>"
            "<p>• <b>ProjectMetadata</b> - Report summary</p>"
            "<br>"
            "<p>Drag tables to the canvas to start visualizing! 🎨</p>"
        )
        help_msg.setTextFormat(Qt.RichText)
        help_msg.setStandardButtons(QMessageBox.Ok)
        help_msg.exec_()
    
    def show_cloud_settings(self):
        """Show Tableau Cloud configuration dialog"""
        dialog = TableauCloudSettingsDialog(self.tableau_cloud_config, self)
        dialog.exec_()
    
    def publish_to_cloud(self):
        """Publish directly to Tableau Cloud using REST API"""
        # Check if config is set
        if not all([self.tableau_cloud_config.server_url, 
                   self.tableau_cloud_config.username, 
                   self.tableau_cloud_config.password]):
            reply = QMessageBox.question(
                self,
                "Tableau Cloud Not Configured",
                "You need to configure your Tableau Cloud credentials first.\\n\\n"
                "Would you like to configure them now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.show_cloud_settings()
            return
        
        target_name = self.input_subject.text().replace(' ', '_')
        
        # Create temporary hyper file
        temp_folder = os.path.join(os.getcwd(), "temp_tableau")
        os.makedirs(temp_folder, exist_ok=True)
        hyper_path = os.path.join(temp_folder, f"{target_name}.hyper")
        
        try:
            self.log("TABLEAU CLOUD", "Generating Hyper file for cloud publishing...")
            
            # Generate hyper file
            generate_tableau_hyper(
                target_name=target_name,
                vectors_data=self.worker.tableau_vectors,
                urls_data=self.worker.tableau_urls,
                sections_data=self.worker.tableau_sections,
                output_path=hyper_path
            )
            
            # Publish to Tableau Cloud
            datasource_url, datasource_id = publish_to_tableau_cloud(
                hyper_path=hyper_path,
                datasource_name=f"DiliGenix_{target_name}_{datetime.now().strftime('%Y%m%d')}",
                config=self.tableau_cloud_config,
                log_callback=self.log
            )
            
            # Success message with URL and option to open
            reply = QMessageBox.question(
                self,
                "Published to Tableau Cloud!",
                f"✅ Successfully published to Tableau Cloud!\n\n"
                f"📊 {len(self.worker.tableau_vectors)} Research Vectors\n"
                f"🌐 {len(self.worker.tableau_urls)} Source URLs\n"
                f"📝 {len(self.worker.tableau_sections)} Analysis Sections\n\n"
                f"Your datasource is ready at:\n{datasource_url}\n\n"
                "Would you like to open it in your browser now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            # Open in browser if user wants
            if reply == QMessageBox.Yes:
                try:
                    if sys.platform == 'win32':
                        os.startfile(datasource_url)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', datasource_url])
                    else:
                        subprocess.run(['xdg-open', datasource_url])
                    self.log("SUCCESS", "Opening Tableau Cloud in browser...")
                except Exception as e:
                    QMessageBox.information(
                        self,
                        "Copy URL",
                        f"Please copy this URL to your browser:\n\n{datasource_url}"
                    )
            
            # Cleanup
            try:
                os.remove(hyper_path)
            except:
                pass
                
        except Exception as e:
            self.log("ERROR", f"Tableau Cloud publish failed: {str(e)}")
            QMessageBox.critical(
                self,
                "Publish Failed",
                f"Failed to publish to Tableau Cloud:\\n\\n{str(e)}\\n\\n"
                "Please check your credentials in Cloud Settings."
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = DiliGenixTerminal()
    terminal.show()
    sys.exit(app.exec_())