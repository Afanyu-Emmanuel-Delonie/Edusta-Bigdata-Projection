from django.shortcuts import render

def about_project(request):
    return render(request, 'about/about_project.html')