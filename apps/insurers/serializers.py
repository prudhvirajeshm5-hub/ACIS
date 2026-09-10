from rest_framework import serializers

from .models import InsuranceBranch, InsuranceCompany


class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = ["id", "name", "code", "gstin", "contact_email", "contact_phone", "active"]


class InsuranceBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceBranch
        fields = ["id", "company", "name", "code", "district", "address", "active"]
