"""
Views for the Home app
This handles the AUCA landing page
"""

from django.shortcuts import render

def home(request):
    """
    Renders the AUCA homepage
    
    This view displays the main landing page with:
    - Hero carousel section
    - Latest news
    - Testimonials
    - Admissions information
    
    Template: home.html (extends base.html)
    """
    
    # Carousel slides data
    hero_slides = [
        {
            'title': 'Welcome to AUCA',
            'subtitle': 'Adventist University of Central Africa',
            'description': 'Transforming Lives Through Faith-Based Education',
            'button_text': 'Apply Now',
            'button_link': '#admissions',
            'image': 'images/hero-1.png',  # You'll add actual images
        },
        {
            'title': 'Excellence in Education',
            'subtitle': 'World-Class Programs',
            'description': 'Join our community of scholars and leaders making a difference in Africa',
            'button_text': 'Explore Programs',
            'button_link': '#programs',
            'image': 'images/hero-2.png',
        },
        {
            'title': 'Innovation Center',
            'subtitle': 'Leading Technology & Research',
            'description': 'Empowering students with cutting-edge skills for tomorrow\'s challenges',
            'button_text': 'Learn More',
            'button_link': '#innovation',
            'image': 'images/hero-3.png',
        },
        {
            'title': 'Campus Life',
            'subtitle': 'A Vibrant Community',
            'description': 'Experience spiritual growth, academic excellence, and lifelong friendships',
            'button_text': 'Visit Campus',
            'button_link': '#campus',
            'image': 'images/hero-4.png',
        },
    ]
    
    context = {
        'page_title': 'Welcome to AUCA',
        'hero_slides': hero_slides,
    }
    
    return render(request, 'home.html', context)