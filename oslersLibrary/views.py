from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def index(request):
	if 'formName' in request.POST:
		if request.POST['formName'] == 'loginForm':
			username = request.POST['username']
			password = request.POST['password']
			
			user = authenticate(username=username, password=password)
			
			if user is not None:
				if user.is_active:
					login(request, user)
										
					return redirect('query/')
				else:
					# Return a 'disabled account' error message
					return render(request, 'index.html', {})
			else:
				# Return an 'invalid login' error message.				
				return render(request, 'index.html', {})
			
	return render(request, 'index.html', {})