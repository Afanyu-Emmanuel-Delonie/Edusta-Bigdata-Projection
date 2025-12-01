from django import template

register = template.Library()

@register.filter
def prettify_name(value):
    """
    Convert variable names to human readable format.
    Examples: 
    - "average_score" -> "Average Score"
    - "pass_rate" -> "Pass Rate"
    - "status_pie" -> "Status Pie"
    """
    if not value:
        return value
    
    # Replace underscores with spaces and title case
    pretty = value.replace('_', ' ').title()
    
    # Special cases
    special_cases = {
        'kpis': 'KPIs',
        'api': 'API',
        'ml': 'ML',
        'csv': 'CSV',
        'pdf': 'PDF',
    }
    
    return special_cases.get(value.lower(), pretty)

@register.filter
def underscore_to_space(value):
    """Alternative filter that just replaces underscores with spaces"""
    return value.replace("_", " ") if value else value