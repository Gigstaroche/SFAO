#!/usr/bin/env python3
"""
SFAO Database Studio - A Prisma Studio-like interface for database management
Provides web-based database visualization and management capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uvicorn
import json
from datetime import datetime

from models import Base, engine, SessionLocal, Feedback, User

# Initialize FastAPI app for database studio
studio_app = FastAPI(title="SFAO Database Studio", version="1.0.0")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseInspector:
    """Database inspection utilities"""

    @staticmethod
    def validate_table_name(table_name: str) -> None:
        """Reject unknown table names before using them in raw SQL."""
        if table_name not in DatabaseInspector.get_all_tables():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    @staticmethod
    def get_table_info(table_name: str) -> Dict[str, Any]:
        """Get detailed information about a table"""
        DatabaseInspector.validate_table_name(table_name)
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        return {
            "name": table_name,
            "columns": columns,
            "indexes": indexes,
            "foreign_keys": foreign_keys
        }
    
    @staticmethod
    def get_all_tables() -> List[str]:
        """Get list of all tables in the database"""
        inspector = inspect(engine)
        return inspector.get_table_names()
    
    @staticmethod
    def execute_query(query: str, db: Session, params: Dict[str, Any] | None = None) -> List[Dict]:
        """Execute raw SQL query and return results"""
        try:
            result = db.execute(text(query), params or {})
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")

# Initialize database inspector
db_inspector = DatabaseInspector()

@studio_app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing all tables"""
    tables = db_inspector.get_all_tables()
    table_info = {}
    
    db = next(get_db())
    try:
        for table in tables:
            count_query = f"SELECT COUNT(*) as count FROM {table}"
            result = db_inspector.execute_query(count_query, db)
            table_info[table] = {
                "name": table,
                "count": result[0]["count"] if result else 0,
                "info": db_inspector.get_table_info(table)
            }
    finally:
        db.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "tables": table_info,
        "title": "SFAO Database Studio"
    })

@studio_app.get("/table/{table_name}", response_class=HTMLResponse)
async def view_table(request: Request, table_name: str, page: int = 1, limit: int = 50, search: str = ""):
    """View table data with pagination"""
    offset = (page - 1) * limit
    search_term = search.strip()
    
    db = next(get_db())
    try:
        # Get table structure
        table_info = db_inspector.get_table_info(table_name)

        searchable_columns = [
            column["name"]
            for column in table_info["columns"]
            if str(column.get("type", "")).lower() not in {"blob", "binary"}
        ]

        search_clause = ""
        query_params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if search_term and searchable_columns:
            search_clause = " WHERE " + " OR ".join(
                [f"CAST({column_name} AS TEXT) LIKE :search" for column_name in searchable_columns]
            )
            query_params["search"] = f"%{search_term}%"
        
        # Get data with pagination
        data_query = f"SELECT * FROM {table_name}{search_clause} LIMIT :limit OFFSET :offset"
        data = db_inspector.execute_query(data_query, db, query_params)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM {table_name}{search_clause}"
        total_result = db_inspector.execute_query(count_query, db, {k: v for k, v in query_params.items() if k == "search"})
        total = total_result[0]["total"] if total_result else 0
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return templates.TemplateResponse("table.html", {
            "request": request,
            "table_name": table_name,
            "table_info": table_info,
            "data": data,
            "page": page,
            "limit": limit,
            "search": search_term,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        })
    finally:
        db.close()

@studio_app.get("/api/tables")
async def api_get_tables():
    """API endpoint to get all tables"""
    return {"tables": db_inspector.get_all_tables()}

@studio_app.get("/api/table/{table_name}")
async def api_get_table_data(table_name: str, page: int = 1, limit: int = 50):
    """API endpoint to get table data"""
    offset = (page - 1) * limit
    
    db = next(get_db())
    try:
        # Get table structure
        table_info = db_inspector.get_table_info(table_name)
        
        # Get data with pagination
        data_query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
        data = db_inspector.execute_query(data_query, db)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM {table_name}"
        total_result = db_inspector.execute_query(count_query, db)
        total = total_result[0]["total"] if total_result else 0
        
        return {
            "table_name": table_name,
            "table_info": table_info,
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    finally:
        db.close()

@studio_app.post("/api/query")
async def api_execute_query(query: dict):
    """API endpoint to execute custom SQL queries"""
    sql_query = query.get("query", "")
    if not sql_query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    db = next(get_db())
    try:
        result = db_inspector.execute_query(sql_query, db)
        return {
            "success": True,
            "data": result,
            "rows_affected": len(result)
        }
    except HTTPException as e:
        return {
            "success": False,
            "error": e.detail
        }
    finally:
        db.close()

@studio_app.get("/query", response_class=HTMLResponse)
async def query_interface(request: Request):
    """Query interface for custom SQL"""
    return templates.TemplateResponse("query.html", {
        "request": request,
        "title": "SQL Query Interface"
    })

@studio_app.get("/api/feedback/analytics")
async def feedback_analytics():
    """Get detailed feedback analytics"""
    db = next(get_db())
    try:
        # Get feedback analytics
        feedbacks = db.query(Feedback).all()
        
        # Calculate various metrics
        total_feedback = len(feedbacks)
        sentiments = {}
        categories = {}
        sources = {}
        urgencies = {}
        monthly_data = {}
        
        for feedback in feedbacks:
            # Count sentiments
            sentiments[feedback.sentiment] = sentiments.get(feedback.sentiment, 0) + 1
            
            # Count categories
            categories[feedback.category] = categories.get(feedback.category, 0) + 1
            
            # Count sources
            sources[feedback.source] = sources.get(feedback.source, 0) + 1
            
            # Count urgencies
            urgencies[feedback.urgency] = urgencies.get(feedback.urgency, 0) + 1
            
            # Monthly data
            month = feedback.created_at.strftime("%Y-%m")
            if month not in monthly_data:
                monthly_data[month] = {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
            
            monthly_data[month]["total"] += 1
            if feedback.sentiment.lower() == "positive":
                monthly_data[month]["positive"] += 1
            elif feedback.sentiment.lower() == "negative":
                monthly_data[month]["negative"] += 1
            else:
                monthly_data[month]["neutral"] += 1
        
        return {
            "total_feedback": total_feedback,
            "sentiments": sentiments,
            "categories": categories,
            "sources": sources,
            "urgencies": urgencies,
            "monthly_trends": monthly_data
        }
    finally:
        db.close()

@studio_app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Analytics dashboard"""
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "title": "SFAO Analytics Dashboard"
    })

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    
    print("🚀 Starting SFAO Database Studio...")
    print("📊 Access the database interface at: http://localhost:8001")
    print("📈 Access analytics dashboard at: http://localhost:8001/analytics")
    print("🔍 Access query interface at: http://localhost:8001/query")
    
    uvicorn.run(studio_app, host="0.0.0.0", port=8001)