import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

class ChartGenerator:
    def __init__(self, dataset):
        self.dataset = dataset
    
    def _validate_column(self, col_name):
        """Validate that column exists and has data"""
        if col_name not in self.dataset.columns:
            raise ValueError(f"Column '{col_name}' not found in dataset")
        if self.dataset[col_name].isna().all():
            raise ValueError(f"Column '{col_name}' contains no valid data")
        return True
    
    def create_scatter(self, x_col, y_col, color_col=None):
        """Create scatter plot"""
        self._validate_column(x_col)
        self._validate_column(y_col)
        
        # Filter out rows where x or y is null
        plot_data = self.dataset.dropna(subset=[x_col, y_col])
        if plot_data.empty:
            raise ValueError(f"No valid data points for {x_col} vs {y_col}")
        
        if color_col and color_col in self.dataset.columns:
            plot_data = plot_data.dropna(subset=[color_col])
        
        fig = px.scatter(
            plot_data, 
            x=x_col, 
            y=y_col,
            color=color_col if color_col and color_col in plot_data.columns else None,
            title=f"{y_col} vs {x_col}",
            hover_data=[col for col in plot_data.columns[:3] if col not in [x_col, y_col]]
        )
        
        return self._style_chart(fig, title=f"{y_col} vs {x_col}", kind="scatter")
    
    def create_histogram(self, x_col, color_col=None):
        """Create histogram"""
        self._validate_column(x_col)
        
        plot_data = self.dataset.dropna(subset=[x_col])
        if plot_data.empty:
            raise ValueError(f"No valid data for histogram of {x_col}")
        
        # Check if numeric - if not then create a count chart instead
        if pd.api.types.is_numeric_dtype(plot_data[x_col]):
            fig = px.histogram(
                plot_data,
                x=x_col,
                color=color_col if color_col and color_col in plot_data.columns else None,
                title=f"Distribution of {x_col}",
                nbins=min(30, max(10, len(plot_data[x_col].unique())))
            )
        else:
            # For categorical data, use value counts
            counts = plot_data[x_col].value_counts().head(20)
            fig = go.Figure(data=[go.Bar(x=counts.index, y=counts.values)])
            fig.update_layout(title=f"Count of {x_col}", xaxis_title=x_col, yaxis_title="Count")
        
        return self._style_chart(fig, title=f"Distribution of {x_col}", rotate_x=False, kind="histogram")

    def create_box_plot(self, x_col, group_col=None):
        """Create box plot"""
        self._validate_column(x_col)
        
        if not pd.api.types.is_numeric_dtype(self.dataset[x_col]):
            raise ValueError(f"Column '{x_col}' must be numeric for box plot")
        
        plot_data = self.dataset.dropna(subset=[x_col])
        if group_col and group_col in self.dataset.columns:
            plot_data = plot_data.dropna(subset=[group_col])
        
        if plot_data.empty:
            raise ValueError(f"No valid data for box plot of {x_col}")
        
        fig = px.box(
            plot_data,
            x=group_col if group_col and group_col in plot_data.columns else None,
            y=x_col,
            title=f"Box plot of {x_col}" + (f" by {group_col}" if group_col else "")
        )
        
        title = f"Box plot of {x_col}" + (f" by {group_col}" if group_col else "")
        return self._style_chart(fig, title=title, rotate_x=False, kind="box")
    
    def create_bar_chart(self, x_col, y_col=None, agg_func='count'):
        """Create bar chart"""
        self._validate_column(x_col)
        
        plot_data = self.dataset.dropna(subset=[x_col])
        
        if y_col and y_col in self.dataset.columns:
            self._validate_column(y_col)
            plot_data = plot_data.dropna(subset=[x_col, y_col])
            
            if plot_data.empty:
                raise ValueError(f"No valid data for bar chart")
            
            if pd.api.types.is_numeric_dtype(plot_data[y_col]):
                if agg_func == 'mean':
                    grouped = plot_data.groupby(x_col)[y_col].mean().reset_index()
                    title = f"{y_col} by {x_col}"
                elif agg_func == 'sum':
                    grouped = plot_data.groupby(x_col)[y_col].sum().reset_index()
                    title = f"Total {y_col} by {x_col}"
                else:  # count
                    grouped = plot_data.groupby(x_col)[y_col].count().reset_index()
                    title = f"Count of {y_col} by {x_col}"
                    
                # Limit categories
                if len(grouped) > 20:
                    grouped = grouped.nlargest(20, y_col)
                    title += " (Top 20)"
                
                fig = px.bar(grouped, x=x_col, y=y_col, title=title)
            else:
                # Both are categorical - do a crosstab
                crosstab = pd.crosstab(plot_data[x_col], plot_data[y_col])
                fig = px.bar(crosstab.reset_index().melt(id_vars=x_col), 
                           x=x_col, y='value', color='variable',
                           title=f"{x_col} vs {y_col}")
        else:
            # Simple value counts
            if plot_data.empty:
                raise ValueError(f"No valid data for bar chart of {x_col}")
            
            counts = plot_data[x_col].value_counts().head(20)
            fig = go.Figure(data=[go.Bar(x=counts.index.astype(str), y=counts.values)])
            fig.update_layout(
                title=f"Count by {x_col}",
                xaxis_title=x_col,
                yaxis_title="Count"
            )
        
        return self._style_chart(fig, title=title if 'title' in locals() else f"Count by {x_col}", kind="bar")

    
    def create_pie_chart(self, names_col, values_col=None):
        """Create pie chart"""
        self._validate_column(names_col)
        
        plot_data = self.dataset.dropna(subset=[names_col])
        
        if values_col and values_col in self.dataset.columns:
            self._validate_column(values_col)
            plot_data = plot_data.dropna(subset=[names_col, values_col])
            
            if plot_data.empty:
                raise ValueError(f"No valid data for pie chart")
            
            fig = px.pie(
                plot_data,
                names=names_col,
                values=values_col,
                title=f"Pie Chart of {names_col} by {values_col}"
            )
        else:
            counts = plot_data[names_col].value_counts().head(10)
            fig = px.pie(
                names=counts.index.astype(str),
                values=counts.values,
                title=f"Pie Chart of {names_col} (Top 10)" # Only display top 10 for aesthetics
            )
        
        return self._style_chart(fig, title=f"Distribution of {names_col}", rotate_x=False, kind="pie")
    
    def create_line_chart(self, x_col, y_col, color_col=None):
        """Create line chart"""
        self._validate_column(x_col)
        self._validate_column(y_col)
        
        plot_data = self.dataset.dropna(subset=[x_col, y_col])
        if plot_data.empty:
            raise ValueError(f"No valid data points for line chart of {y_col} vs {x_col}")
        
        if color_col and color_col in self.dataset.columns:
            plot_data = plot_data.dropna(subset=[color_col])
        
        fig = px.line(
            plot_data,
            x=x_col,
            y=y_col,
            color=color_col if color_col and color_col in plot_data.columns else None,
            title=f"{y_col} vs {x_col}"
        )
        
        return self._style_chart(fig, title=f"{y_col} vs {x_col}", kind="line")
    
    def _style_chart(self, fig, title=None, rotate_x=True, kind=None):
        if kind:
            fig = self._colourise(fig, kind)

        fig.update_layout(
        height=650,
        margin=dict(l=60, r=40, t=60, b=140),
        plot_bgcolor="white",
        title=dict(
            text=title,
            x=0.01,
            xanchor="left",
            font=dict(size=18)
            ) if title else None
        )

        fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)")
        fig.update_xaxes(showgrid=False, automargin=True)

        if rotate_x:
            fig.update_xaxes(tickangle=35)

        return fig
    
    def _colourise(self, fig, kind: str):
        # Add more colour where it makes sense to do so
        if kind == "bar":
            if len(fig.data) == 1:
                try:
                    trace = fig.data[0]
                    if hasattr(trace, "x") and trace.x is not None:
                        n = len(trace.x)
                        fig.update_traces(
                            marker_color=px.colors.qualitative.Set2 * ((n // len(px.colors.qualitative.Set2)) + 1)
                        )
                except Exception:
                    pass
            fig.update_layout(showlegend=False)

        elif kind == "histogram":
            fig.update_traces(marker_color=px.colors.qualitative.Set2[0])

        elif kind == "scatter":
            fig.update_traces(marker=dict(size=10, opacity=0.85))

        elif kind == "box":
            fig.update_traces(marker_color=px.colors.qualitative.Set2[0])

        elif kind == "line":
            fig.update_traces(line=dict(width=3))

        elif kind == "pie":
            fig.update_traces(marker=dict(colors=px.colors.qualitative.Set2))

        return fig

def render_chart(df, chart_spec: dict):
    gen = ChartGenerator(df)
    t = chart_spec.get("type")
    x = chart_spec.get("x")
    y = chart_spec.get("y")
    group = chart_spec.get("group")
    agg = chart_spec.get("agg", "count")

    if not t:
        raise ValueError("Please specify a chart type (bar/scatter/histogram/box/pie/line) and the column names (For example, 'bar chart of column1 vs column2').")

    if t == "scatter":
        if not x or not y:
            raise ValueError("Scatter needs two columns, e.g. 'age vs salary'.")
        return gen.create_scatter(x, y)

    if t == "histogram":
        if not x:
            raise ValueError("Histogram needs one column.")
        return gen.create_histogram(x)

    if t == "box":
        if not x:
            raise ValueError("Box plot needs one numeric column.")
        return gen.create_box_plot(x, group)

    if t == "bar":
        if not x:
            raise ValueError("Bar chart needs at least one column.")
        return gen.create_bar_chart(x, y, agg_func=agg)
    
    if t == "pie":
        if not x:
            raise ValueError("Pie chart needs one column (categories).")
        return gen.create_pie_chart(x, y)

    if t == "line":
        if not x or not y:
            raise ValueError("Line chart needs two columns.")
        return gen.create_line_chart(x, y, group)

    raise ValueError(f"Unsupported chart type: {t}")
