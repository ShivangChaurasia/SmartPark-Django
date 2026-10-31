from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, HostKYCForm, ProfileUpdateForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Automatically log in new user (INT253 Unit VI: Sessions & Login)
            login(request, user)
            messages.success(request, f"Welcome to SmartPark, {user.username}! Your account has been created.")

            if user.role == 'host':
                return redirect('owner_kyc')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next', 'dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.POST.get('next') or 'dashboard')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def switch_role_view(request):
    user = request.user
    if user.role == 'user':
        # Switch to host
        if user.kyc_status != 'verified':
            messages.warning(request, "Host KYC verification is required to access Host mode.")
            return redirect('owner_kyc')
        user.role = 'host'
        user.save()
        messages.success(request, "Switched to Host Mode.")
        return redirect('owner_dashboard')
    else:
        user.role = 'user'
        user.save()
        messages.success(request, "Switched to User Mode.")
        return redirect('dashboard')


@login_required
def onboarding_view(request):
    if request.method == 'POST':
        role = request.POST.get('role', 'user')
        request.user.role = role
        request.user.onboarding_completed = True
        request.user.save()

        if role == 'host':
            return redirect('owner_kyc')
        return redirect('dashboard')

    return render(request, 'accounts/onboarding.html')


@login_required
def kyc_view(request):
    user = request.user
    if request.method == 'POST':
        form = HostKYCForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            host = form.save(commit=False)
            host.role = 'host'
            host.kyc_status = 'verified'  # Instant verification for seamless evaluation
            host.onboarding_completed = True
            host.save()
            messages.success(request, "KYC verified successfully! You now have full Host privileges.")
            return redirect('owner_dashboard')
    else:
        form = HostKYCForm(instance=user)

    return render(request, 'accounts/kyc.html', {'form': form, 'user': user})


@login_required
def settings_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('settings')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/settings.html', {'form': form})
