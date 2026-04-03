# Tennis Performance Analytics – Learner Tien

## Overview
This project presents a comprehensive, data-driven analysis of professional tennis player Learner Tien. The analysis evaluates performance across surfaces, match contexts, and opponent types to identify key strengths, weaknesses, and actionable areas for improvement.

## Full Report
📄 **View Full Write-Up:**  
[Click here to access the full report](./full_writeup/LearnerTien_Performance_Report.pdf)

## Key Insights
- Analyzed 80+ ATP matches across multiple datasets  
- Identified Dominance Ratio (DR) > 1.0 as a primary predictor of match outcomes  
- Diagnosed clay court performance gap (12.5% win rate) linked to reduced return effectiveness  
- Highlighted pressure-based trends, including a quarterfinal performance drop-off and strong semifinal results  

## Tools & Technologies
- Python (pandas, sqlite3)  
- Excel (data structuring and storage)  
- Data analysis and visualization
- SQL
- Claude
- Cursor

## Project Structure

full_writeup/  
  LearnerTien_Performance_Report.pdf  

analysis/  
  dr_analysis.py  
  h2h_analysis.py  
  ranking_trajectory.py  
  round_analysis.py  
  serve_analysis.py  
  surface_analysis.py  

data/  
  LearnerTien_Database.xlsx  

load/  
  load_db.py  

update_data/  
  update_tien_db.py  

## Description of Components

- **Full Writeup**: Final report synthesizing all analysis into clear, actionable insights  
- **Analysis**: Python scripts focused on specific performance dimensions (serve, surface, dominance ratio, etc.)  
- **Data**: Structured dataset used for all analysis  
- **Load**: Scripts to initialize and structure the dataset  
- **Update Data**: Script to continuously update the dataset with new match data  

## Purpose
The goal of this project was to not only build data analytics and AI skills but also to hopefully reach out to the team of Learner Tien to present to them my work. I really enjoyed working on this and spending the time to pull the data and figure out the best ways to present it and convert it into actionable steps. 
