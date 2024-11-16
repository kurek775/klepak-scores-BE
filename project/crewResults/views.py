from django.http import JsonResponse


def crewResults(request):
    data = [
        {"id": 1, "name": "First Crew Member"},
        {"id": 2, "name": "Second Crew Member"},
        {"id": 3, "name": "Third Crew Member"},
        {"id": 4, "name": "Third  Member"},
        {"id": 5, "name": " Crew Member"},
        {"id": 6, "name": "Third Crew "},
        {"id": 7, "name": " Crew "},
    ]
    return JsonResponse(data, safe=False)
