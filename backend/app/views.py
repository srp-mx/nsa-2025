"""
Views for the app.

This file contains the view functions that handle requests and responses
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Organization, Auditor, Audit, Measurement
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

@api_view(["GET"])
@permission_classes([])
def home(request):
    return HttpResponse(":D")


# Utility: parse request body safely
def parse_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return {}

# ---------------- USER ----------------
@api_view(["POST"])
@permission_classes([AllowAny])  # allow anyone to register
def signup_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")
    role = request.data.get("role")  # must be "organization" or "auditor"

    if not username or not password or not role:
        return Response(
            {"error": "username, password, and role are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if role not in ["organization", "auditor"]:
        return Response(
            {"error": "role must be either 'organization' or 'auditor'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already taken"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create the user
    user = User.objects.create_user(username=username, password=password, email=email)

    # Attach the user to exactly one role
    if role == "organization":
        Organization.objects.create(user=user)
    elif role == "auditor":
        Auditor.objects.create(user=user)

    return Response(
        {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role,
        },
        status=status.HTTP_201_CREATED,
    )

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # You can also add custom claims here if you want
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra responses here
        data["user_id"] = self.user.id
        data["username"] = self.user.username
        data["email"] = self.user.email
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# ---------------- ORGANIZATION ----------------
@api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
def organization_list(request):
    if request.method == "GET":
        data = list(Organization.objects.values("id", "user_id"))
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        user = get_object_or_404(User, id=body.get("user_id"))
        org = Organization.objects.create(user=user)
        return JsonResponse({"id": org.id, "user_id": org.user.id})


@api_view(["GET", "POST", "DELETE"])
# @permission_classes([IsAuthenticated])
def organization_detail(request, pk):
    org = get_object_or_404(Organization, pk=pk)

    if request.method == "GET":
        return JsonResponse({"id": org.id, "user_id": org.user.id})

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "user_id" in body:
            org.user = get_object_or_404(User, id=body["user_id"])
        org.save()
        return JsonResponse({"id": org.id, "user_id": org.user.id})

    elif request.method == "DELETE":
        org.delete()
        return JsonResponse({"deleted": True})


# ---------------- AUDITOR ----------------
@api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
def auditor_list(request):
    if request.method == "GET":
        data = list(Auditor.objects.values("id", "user_id"))
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        user = get_object_or_404(User, id=body.get("user_id"))
        auditor = Auditor.objects.create(user=user)
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})


@api_view(["GET", "POST", "DELETE"])
# @permission_classes([IsAuthenticated])
def auditor_detail(request, pk):
    auditor = get_object_or_404(Auditor, pk=pk)

    if request.method == "GET":
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "user_id" in body:
            auditor.user = get_object_or_404(User, id=body["user_id"])
        auditor.save()
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})

    elif request.method == "DELETE":
        auditor.delete()
        return JsonResponse({"deleted": True})

from .models import Site  # add this import with your other models

# ---------------- SITE ----------------
@api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
def site_list(request):
    if request.method == "GET":
        # Return all sites as JSON
        data = [
            {
                "id": s.id,
                "organization_id": s.organization_id,
                "region": s.region.geojson if s.region else None,
            }
            for s in Site.objects.all()
        ]
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        site = Site.objects.create(
            region=body.get("region"),  # NOTE: must be valid GeoJSON or WKT string
            organization_id=body.get("organization_id"),
        )
        return JsonResponse({"id": site.id})
    

@api_view(["GET", "POST", "DELETE"])
# @permission_classes([IsAuthenticated])
def site_detail(request, pk):
    site = get_object_or_404(Site, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": site.id,
            "organization_id": site.organization_id,
            "region": site.region.geojson if site.region else None,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "organization_id" in body:
            site.organization_id = body["organization_id"]
        if "region" in body:
            site.region = body["region"]  # again, must be valid geometry
        site.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        site.delete()
        return JsonResponse({"deleted": True})


# ---------------- AUDIT ----------------
@api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
def audit_list(request):
    if request.method == "GET":
        data = list(Audit.objects.values())
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        audit = Audit.objects.create(
            score=body.get("score"),
            max_score=body.get("max_score"),
            is_passing=body.get("is_passing", False),
            notes=body.get("notes", ""),
            organization_id=body.get("organization_id"),
            auditor_id=body.get("auditor_id"),
        )
        return JsonResponse({"id": audit.id})


@api_view(["GET", "POST", "DELETE"])
# @permission_classes([IsAuthenticated])
def audit_detail(request, pk):
    audit = get_object_or_404(Audit, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": audit.id,
            "score": audit.score,
            "max_score": audit.max_score,
            "is_passing": audit.is_passing,
            "notes": audit.notes,
            "organization_id": audit.organization_id,
            "auditor_id": audit.auditor_id,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        for field in ["score", "max_score", "is_passing", "notes", "organization_id", "auditor_id"]:
            if field in body:
                setattr(audit, field, body[field])
        audit.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        audit.delete()
        return JsonResponse({"deleted": True})


# ---------------- MEASUREMENT ----------------
@api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
def measurement_list(request):
    if request.method == "GET":
        data = list(Measurement.objects.values())
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        measurement = Measurement.objects.create(
            start_time=body.get("start_time"),
            end_time=body.get("end_time"),
            region=body.get("region"),  # NOTE: must be a valid GeoJSON or WKT string
            organization_id=body.get("organization_id"),
        )
        return JsonResponse({"id": measurement.id})


@api_view(["GET", "POST", "DELETE"])
# @permission_classes([IsAuthenticated])
def measurement_detail(request, pk):
    measurement = get_object_or_404(Measurement, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": measurement.id,
            "start_time": measurement.start_time,
            "end_time": measurement.end_time,
            "region": measurement.region.geojson if measurement.region else None,
            "organization_id": measurement.organization_id,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        for field in ["start_time", "end_time", "region", "organization_id"]:
            if field in body:
                setattr(measurement, field, body[field])
        measurement.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        measurement.delete()
        return JsonResponse({"deleted": True})

