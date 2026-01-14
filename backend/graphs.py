import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

class ChartGenerator:
    def __init__(self, dataset):
        self.dataset = dataset
    
    def create_scatter(self, x_col, y_col, color_col=None):
        """Create scatter plot"""
        fig = px.scatter(
            self.dataset, 
            x=x_col, 
            y=y_col,
            color=color_col if color_col else None,
            title=f"{y_col} vs {x_col}",
            hover_data=self.dataset.columns[:3].tolist()  # Show 3 columns on hover
        )
        fig.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=50))
        return fig
    
    def create_histogram(self, x_col, color_col=None):
        """Create histogram"""
        fig = px.histogram(
            self.dataset,
            x=x_col,
            color=color_col if color_col else None,
            title=f"Distribution of {x_col}",
            nbins=30
        )
        fig.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=50))
        return fig
    
    def create_box_plot(self, x_col, group_col=None):
        """Create box plot"""
        fig = px.box(
            self.dataset,
            x=group_col if group_col else None,
            y=x_col,
            title=f"Box plot of {x_col}" + (f" by {group_col}" if group_col else "")
        )
        fig.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=50))
        return fig
    
    def create_bar_chart(self, x_col, y_col=None, agg_func='mean'):
        """Create bar chart"""
        if y_col:
            # Group and aggregate
            if agg_func == 'mean':
                grouped = self.dataset.groupby(x_col)[y_col].mean().reset_index()
                title = f"Average {y_col} by {x_col}"
            elif agg_func == 'count':
                grouped = self.dataset.groupby(x_col)[y_col].count().reset_index()
                title = f"Count of {y_col} by {x_col}"
            else:  # sum
                grouped = self.dataset.groupby(x_col)[y_col].sum().reset_index()
                title = f"Total {y_col} by {x_col}"
            
            fig = px.bar(grouped, x=x_col, y=y_col, title=title)
        else:
            # Simple value counts
            counts = self.dataset[x_col].value_counts().reset_index()
            counts.columns = [x_col, 'count']
            fig = px.bar(counts, x=x_col, y='count', title=f"Count by {x_col}")
        
        fig.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=50))
        return fig

def get_chart_suggestions(dataset, query):
    """Suggest appropriate chart based on query and data types"""
    numeric_cols = dataset.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = dataset.select_dtypes(include=['object', 'category']).columns.tolist()
    
    query_lower = query.lower()
    
    # Look for specific chart types
    if "histogram" in query_lower or "distribution" in query_lower:
        if numeric_cols:
            return {"type": "histogram", "x": numeric_cols[0]}
    
    elif "scatter" in query_lower or "correlation" in query_lower or "relationship" in query_lower:
        if len(numeric_cols) >= 2:
            return {"type": "scatter", "x": numeric_cols[0], "y": numeric_cols[1]}
    
    elif "box" in query_lower:
        if numeric_cols:
            group_col = categorical_cols[0] if categorical_cols else None
            return {"type": "box", "x": numeric_cols[0], "group": group_col}
    
    elif "bar" in query_lower or "count" in query_lower:
        if categorical_cols:
            return {"type": "bar", "x": categorical_cols[0]}
    
    # Generic "plot" - try to be smart
    elif any(word in query_lower for word in ["plot", "chart", "graph", "visualize"]):
        # Look for column names in the query
        mentioned_cols = [col for col in dataset.columns if col.lower() in query_lower]
        
        if len(mentioned_cols) >= 2:
            # Two columns mentioned - probably want scatter
            return {"type": "scatter", "x": mentioned_cols[0], "y": mentioned_cols[1]}
        elif len(mentioned_cols) == 1:
            col = mentioned_cols[0]
            if col in numeric_cols:
                return {"type": "histogram", "x": col}
            else:
                return {"type": "bar", "x": col}
        else:
            # No specific columns - suggest based on data
            if len(numeric_cols) >= 2:
                return {"type": "scatter", "x": numeric_cols[0], "y": numeric_cols[1]}
            elif numeric_cols:
                return {"type": "histogram", "x": numeric_cols[0]}
            elif categorical_cols:
                return {"type": "bar", "x": categorical_cols[0]}
    
    return None

def auto_suggest_chart(dataset):
    """Suggest a good default chart for the dataset"""
    numeric_cols = dataset.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = dataset.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(numeric_cols) >= 2:
        return {"type": "scatter", "x": numeric_cols[0], "y": numeric_cols[1]}
    elif len(numeric_cols) >= 1:
        return {"type": "histogram", "x": numeric_cols[0]}
    elif len(categorical_cols) >= 1:
        return {"type": "bar", "x": categorical_cols[0]}
    
    return None