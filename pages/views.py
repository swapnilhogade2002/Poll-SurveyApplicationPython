from django.shortcuts import render

def index(request):
  context ={'page': 'home'}
  return render(request, 'pages/index.html', context)
