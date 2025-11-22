"""
Chart Generator for Performance Dashboard
Generates Chart.js compatible data structures
"""

import json


class ChartGenerator:
    """
    Generates chart data in Chart.js format for the dashboard
    """
    
    def generate_score_distribution(self, distribution):
        """
        Generate score distribution bar chart data
        
        Args:
            distribution: dict with score ranges and counts
        
        Returns:
            JSON string for Chart.js
        """
        labels = list(distribution.keys())
        data = list(distribution.values())
        
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Number of Students',
                    'data': data,
                    'backgroundColor': [
                        'rgba(239, 68, 68, 0.7)',   # Red for 0-49
                        'rgba(249, 115, 22, 0.7)',  # Orange for 50-69
                        'rgba(59, 130, 246, 0.7)',  # Blue for 70-84
                        'rgba(34, 197, 94, 0.7)',   # Green for 85-100
                    ],
                    'borderColor': [
                        'rgba(239, 68, 68, 1)',
                        'rgba(249, 115, 22, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(34, 197, 94, 1)',
                    ],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'top',
                    },
                    'title': {
                        'display': True,
                        'text': 'Score Distribution'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'ticks': {
                            'stepSize': 1
                        }
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def generate_status_pie_chart(self, kpis):
        """
        Generate pie chart for pass/fail status
        
        Args:
            kpis: dict with pass_rate and fail_rate
        
        Returns:
            JSON string for Chart.js
        """
        pass_rate = kpis.get('pass_rate', 0)
        fail_rate = 100 - pass_rate
        
        chart_data = {
            'type': 'pie',
            'data': {
                'labels': ['Pass', 'Fail'],
                'datasets': [{
                    'data': [pass_rate, fail_rate],
                    'backgroundColor': [
                        'rgba(34, 197, 94, 0.7)',  # Green for pass
                        'rgba(239, 68, 68, 0.7)',  # Red for fail
                    ],
                    'borderColor': [
                        'rgba(34, 197, 94, 1)',
                        'rgba(239, 68, 68, 1)',
                    ],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'bottom',
                    },
                    'title': {
                        'display': True,
                        'text': 'Pass/Fail Distribution'
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def generate_course_comparison(self, course_comparison):
        """
        Generate horizontal bar chart for course comparison
        
        Args:
            course_comparison: list of dicts with course statistics
        
        Returns:
            JSON string for Chart.js
        """
        if not course_comparison:
            return json.dumps({
                'type': 'bar',
                'data': {'labels': [], 'datasets': []},
                'options': {'responsive': True}
            })
        
        labels = [course['course_code'] for course in course_comparison]
        scores = [course['average_score'] for course in course_comparison]
        pass_rates = [course['pass_rate'] for course in course_comparison]
        
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Average Score',
                        'data': scores,
                        'backgroundColor': 'rgba(59, 130, 246, 0.7)',
                        'borderColor': 'rgba(59, 130, 246, 1)',
                        'borderWidth': 2
                    },
                    {
                        'label': 'Pass Rate (%)',
                        'data': pass_rates,
                        'backgroundColor': 'rgba(34, 197, 94, 0.7)',
                        'borderColor': 'rgba(34, 197, 94, 1)',
                        'borderWidth': 2
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'indexAxis': 'y',
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'top',
                    },
                    'title': {
                        'display': True,
                        'text': 'Course Performance Comparison'
                    }
                },
                'scales': {
                    'x': {
                        'beginAtZero': True,
                        'max': 100
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def generate_semester_trend(self, semester_trend):
        """
        Generate line chart for semester trends
        
        Args:
            semester_trend: list of dicts with semester statistics
        
        Returns:
            JSON string for Chart.js
        """
        if not semester_trend:
            return json.dumps({
                'type': 'line',
                'data': {'labels': [], 'datasets': []},
                'options': {'responsive': True}
            })
        
        labels = [sem['semester'] for sem in semester_trend]
        scores = [sem['average_score'] for sem in semester_trend]
        pass_rates = [sem['pass_rate'] for sem in semester_trend]
        
        chart_data = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Average Score',
                        'data': scores,
                        'borderColor': 'rgba(59, 130, 246, 1)',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 3,
                        'tension': 0.4,
                        'fill': True
                    },
                    {
                        'label': 'Pass Rate (%)',
                        'data': pass_rates,
                        'borderColor': 'rgba(34, 197, 94, 1)',
                        'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                        'borderWidth': 3,
                        'tension': 0.4,
                        'fill': True
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'top',
                    },
                    'title': {
                        'display': True,
                        'text': 'Performance Trends Over Time'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def generate_top_bottom_comparison(self, top_performers, bottom_performers):
        """
        Generate comparison chart for top and bottom performers
        
        Args:
            top_performers: list of top performer dicts
            bottom_performers: list of bottom performer dicts
        
        Returns:
            JSON string for Chart.js
        """
        if not top_performers and not bottom_performers:
            return json.dumps({
                'type': 'bar',
                'data': {'labels': [], 'datasets': []},
                'options': {'responsive': True}
            })
        
        top_5 = top_performers[:5]
        bottom_5 = bottom_performers[:5]
        
        top_labels = [f"{p['student_name']} ({p['course']})" for p in top_5]
        top_scores = [p['score'] for p in top_5]
        
        bottom_labels = [f"{p['student_name']} ({p['course']})" for p in bottom_5]
        bottom_scores = [p['score'] for p in bottom_5]
        
        all_labels = top_labels + bottom_labels
        all_scores = top_scores + bottom_scores
        
        # Create colors array
        colors = ['rgba(34, 197, 94, 0.7)'] * len(top_5) + ['rgba(239, 68, 68, 0.7)'] * len(bottom_5)
        
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': all_labels,
                'datasets': [{
                    'label': 'Scores',
                    'data': all_scores,
                    'backgroundColor': colors,
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': False,
                    },
                    'title': {
                        'display': True,
                        'text': 'Top 5 vs Bottom 5 Performers'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def generate_grade_distribution(self, performances):
        """
        Generate pie chart for grade distribution
        
        Args:
            performances: QuerySet of Performance objects
        
        Returns:
            JSON string for Chart.js
        """
        # Count grades
        grade_counts = {}
        for perf in performances:
            grade = perf.grade
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        if not grade_counts:
            return json.dumps({
                'type': 'doughnut',
                'data': {'labels': [], 'datasets': []},
                'options': {'responsive': True}
            })
        
        # Sort by grade order
        grade_order = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        labels = []
        data = []
        
        for grade in grade_order:
            if grade in grade_counts:
                labels.append(grade)
                data.append(grade_counts[grade])
        
        chart_data = {
            'type': 'doughnut',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': [
                        'rgba(34, 197, 94, 0.7)',   # A+
                        'rgba(52, 211, 153, 0.7)',  # A
                        'rgba(74, 222, 128, 0.7)',  # A-
                        'rgba(59, 130, 246, 0.7)',  # B+
                        'rgba(96, 165, 250, 0.7)',  # B
                        'rgba(147, 197, 253, 0.7)', # B-
                        'rgba(249, 115, 22, 0.7)',  # C+
                        'rgba(251, 146, 60, 0.7)',  # C
                        'rgba(253, 186, 116, 0.7)', # C-
                        'rgba(234, 88, 12, 0.7)',   # D
                        'rgba(239, 68, 68, 0.7)',   # F
                    ],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'right',
                    },
                    'title': {
                        'display': True,
                        'text': 'Grade Distribution'
                    }
                }
            }
        }
        
        return json.dumps(chart_data)