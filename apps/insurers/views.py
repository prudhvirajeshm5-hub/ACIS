from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from apps.accounts.permissions import PermissionRequiredMixin

from .forms import InsuranceBranchForm, InsuranceCompanyForm
from .models import InsuranceBranch, InsuranceCompany


class ClientListView(LoginRequiredMixin, View):
    """Function-style view kept as a plain view (not ListView) so it can
    show branches inline under each client without a second page — the
    two are almost always looked at together."""

    def get(self, request):
        companies = InsuranceCompany.objects.filter(active=True).prefetch_related("branches")
        return render(request, "insurers/client_list.html", {"companies": companies})


class ClientCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "insurers.add_insurancecompany"

    def get(self, request):
        return render(request, "insurers/client_form.html", {"form": InsuranceCompanyForm()})

    def post(self, request):
        form = InsuranceCompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            messages.success(request, f"{company.name} added as a client.")
            return redirect("insurers:list")
        return render(request, "insurers/client_form.html", {"form": form})


class BranchCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "insurers.add_insurancebranch"

    def get(self, request):
        return render(request, "insurers/branch_form.html", {"form": InsuranceBranchForm()})

    def post(self, request):
        form = InsuranceBranchForm(request.POST)
        if form.is_valid():
            branch = form.save()
            messages.success(request, f"{branch.name} branch added under {branch.company}.")
            return redirect("insurers:list")
        return render(request, "insurers/branch_form.html", {"form": form})
